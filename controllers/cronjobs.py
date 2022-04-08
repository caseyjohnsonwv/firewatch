import logging
from threading import Thread
import time
import requests
from utils.aws import DynamoDB
from utils.sms import send_alert_sms
import env


logger = logging.getLogger(env.ENV_NAME)


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
    for company in j:
        parks = company['parks']
        for park in parks:
            id, name, country = park['id'], park['name'], park['country']
            if country != 'United States':
                continue
            r = DynamoDB.ParkRecord(park_id=id, park_name=name)
            r.write_to_dynamo()
            logger.debug(f"Record created for {name} ({id})")
    logger.info(f"Fetched parks.json and updated database in {time.time()-start:.1f} seconds")


# combined job for fetching wait times + updating in dynamo
def update_wait_times():
    logger.info('Fetching latest wait times json files...')
    start = time.time()
    all_parks = DynamoDB.list_parks()
    threads = []
    for i,park in enumerate(all_parks):
        logger.debug("Processing {park}")
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
    logger.info(f"Fetched wait times and updated DynamoDB in {time.time()-start:.1f} seconds")
# actual worker, defined for threading
def _update_wait_times_thread_target(park:DynamoDB.ParkRecord):
    response = requests.get(f"https://queue-times.com/en-US/parks/{park.park_id}/queue_times.json")
    j = response.json()
    for land in j['lands']:
        for ride in land['rides']:
            # put riderecords in rides table
            r = DynamoDB.RideRecord(ride['id'], park.park_id, ride['name'], park.park_name, ride['wait_time'], ride['is_open'])
            r.write_to_dynamo()


# cronjob task for fulfilling / expiring alerts and notifying users
def close_out_alerts():
    logger.info("Sending alert notifications...")
    print("Sending alert notifications...")
    start = time.time()
    # get all parks
    parks = DynamoDB.list_parks()
    for p in parks:
        logger.debug(f"Fulfilling alerts for {p}")
        print(f"Fulfilling alerts for {p}")
        rides = DynamoDB.list_rides_by_park(p.park_id)
        rides.sort(key=lambda r:r.ride_id)
        alerts = DynamoDB.list_alerts_by_park(p.park_id)
        alerts.sort(key=lambda a:a.ride_id)
        # two pointer logic
        r, a = 0, 0
        while r < len(rides) and a < len(alerts):
            if alerts[a].ride_id != rides[r].ride_id:
                r += 1
            else:
                while a < len(alerts) and alerts[a].ride_id == rides[r].ride_id:
                    # check ride wait time
                    expired = alerts[a].end_time <= time.time()
                    if rides[r].wait_time <= alerts[a].wait_time or expired:
                        # send text message for fulfilled/expired and delete alert
                        logger.debug(f"Closing out alert {alerts[a]}{' <<EXPIRED>>' if expired else ''}")
                        print(f"Closing out alert {alerts[a]}{' <<EXPIRED>>' if expired else ''}")
                        send_alert_sms(alerts[a].phone_number, rides[r].ride_name, alerts[a].wait_time if expired else rides[r].wait_time, expired)
                        alerts[a].delete_from_dynamo()
                    # move to next ride
                    a += 1
    logger.info(f"Alert notifications complete in {time.time()-start:.1f} seconds")
    print(f"Alert notifications complete in {time.time()-start:.1f} seconds")