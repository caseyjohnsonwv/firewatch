import logging
from threading import Thread
import time
import requests
from utils.postgres import Park, CrudUtils
from utils.sms import send_alert_sms
import env


logger = logging.getLogger('uvicorn')


# cronjob task for pulling new parks data
def fetch_parks_json():
    logger.info('Fetching latest parks.json file...')
    start = time.time()
    # get latest parks.json
    filepath = 'parks.json'
    response = requests.get(f"https://queue-times.com/en-US/{filepath}")
    j = response.json()
    logger.debug('File fetched successfully')
    # parse parks.json
    existing_park_ids = set([p.id for p in CrudUtils.read_parks()])
    for company in j:
        parks = company['parks']
        for park in parks:
            id, name, country = park['id'], park['name'], park['country']
            name=str(name).strip()
            country=str(country).strip()
            if country != 'United States':
                continue
            if id in existing_park_ids:
                CrudUtils.update_parks(id=id, updates={'name':name})
                logger.debug(f"Record updated for {name} ({id})")
            else:
                CrudUtils.create_park(id=id, name=name)
                logger.debug(f"Record created for {name} ({id})")
    logger.info(f"Fetched parks.json and updated database in {time.time()-start:.1f} seconds")


# combined job for fetching wait times + updating in database
def update_wait_times():
    logger.info('Fetching latest wait times json files...')
    start = time.time()
    all_parks = CrudUtils.read_parks()
    threads = []
    for i,park in enumerate(all_parks):
        logger.debug(f"Processing {park}")
        threads.append(Thread(
            target=_update_wait_times_thread_target,
            kwargs = {'park':park}
        ))
        if len(threads) == env.MAX_THREADS or i == len(all_parks) - 1:
            for th in threads:
                th.start()
            for th in threads:
                th.join()
            threads = []
    logger.info(f"Fetched wait times and updated database in {time.time()-start:.1f} seconds")
# actual worker, defined for threading
def _update_wait_times_thread_target(park:Park):
    response = requests.get(f"https://queue-times.com/en-US/parks/{park.id}/queue_times.json")
    j = response.json()
    all_ride_ids = set([r.id for r in CrudUtils.read_rides(park_id=park.id)])
    for land in j['lands']:
        for ride in land['rides']:
            # put riderecords in rides table
            if ride['id'] in all_ride_ids:
                CrudUtils.update_rides(
                    id=ride['id'],
                    updates={'wait_time':ride['wait_time'], 'is_open':ride['is_open']}
                )
            else:
                CrudUtils.create_ride(id=ride['id'], name=str(ride['name']).strip(), park_id=park.id, wait_time=ride['wait_time'], is_open=ride['is_open'])


# cronjob task for fulfilling / expiring alerts and notifying users
def close_out_alerts():
    logger.info("Sending alert notifications...")
    start = time.time()
    # get all parks
    parks = CrudUtils.read_parks()
    for p in parks:
        logger.debug(f"Fulfilling alerts for {p}")
        print(f"Fulfilling alerts for {p}")
        rides = CrudUtils.read_rides(park_id=p.id)
        rides.sort(key=lambda r:r.id)
        alerts = CrudUtils.read_alerts(park_id=p.id)
        alerts.sort(key=lambda a:a.ride_id)
        # two pointer logic
        r, a = 0, 0
        while r < len(rides) and a < len(alerts):
            if alerts[a].ride_id != rides[r].id:
                r += 1
            else:
                while a < len(alerts) and alerts[a].ride_id == rides[r].id:
                    # check ride wait time
                    expired = alerts[a].expiration <= time.time()
                    if rides[r].wait_time <= alerts[a].wait_time or expired:
                        # send text message for fulfilled/expired and delete alert
                        logger.debug(f"Closing out alert {alerts[a]}{' <<EXPIRED>>' if expired else ''}")
                        print(f"Closing out alert {alerts[a]}{' <<EXPIRED>>' if expired else ''}")
                        send_alert_sms(alerts[a].phone_number, rides[r].name, alerts[a].wait_time if expired else rides[r].wait_time, expired)
                        CrudUtils.delete_alerts(id=alerts[a].id)
                    # move to next ride
                    a += 1
    logger.info(f"Alert notifications complete in {time.time()-start:.1f} seconds")