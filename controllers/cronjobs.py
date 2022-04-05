import json
import logging
import os
import re
from threading import Thread
import time
import requests
from utils.aws import S3, SQS, DynamoDB
from utils.sms import send_alert_sms
import env


logger = logging.getLogger(env.ENV_NAME)


# reusable function for starting/joining threads
def run_threads(threads:list) -> None:
    logger.debug(f"Starting {len(threads)} threads")
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    logger.debug("Threads joined successfully")


# cronjob task for pulling new parks data
def fetch_parks_json():
    logger.info('Fetching latest parks.json file...')
    start = time.time()
    # get latest parks.json
    filepath = 'parks.json'
    response = requests.get(f"https://queue-times.com/en-US/{filepath}")
    logger.debug('File fetched successfully')
    with open(filepath, 'w') as f:
        json.dump(response.json(), f)
    S3.put_object(filepath)
    logger.debug('File uploaded to S3 successfuly')
    # parse parks.json
    with open(filepath, 'r') as f:
        j = json.load(f)
        for company in j:
            parks = company['parks']
            for park in parks:
                id, name, country = park['id'], park['name'], park['country']
                if country != 'United States':
                    continue
                r = DynamoDB.ParkRecord(park_id=id, park_name=name)
                r.write_to_dynamo()
                logger.debug(f"Record created for {name} ({id})")
    # delete local json file
    os.remove(filepath)
    logger.info(f"Fetched parks.json and updated database in {time.time()-start:.1f} seconds")


# cronjob task for pulling wait times data
def fetch_wait_times_json():
    logger.info('Fetching latest wait times json files...')
    start = time.time()
    all_parks = DynamoDB.list_parks()
    threads = []
    for park in all_parks:
        threads.append(
            Thread(
                target=_fetch_wait_times_json_thread_target,
                kwargs={'park_id':park.park_id},
            )
        )
        if len(threads) == env.THREAD_COUNT:
            run_threads(threads)
            threads = []
    logger.info(f"Fetched wait times and uploaded to S3 in {time.time()-start:.1f} seconds")
# actual worker, defined for threading
def _fetch_wait_times_json_thread_target(park_id:int):
    response = requests.get(f"https://queue-times.com/en-US/parks/{park_id}/queue_times.json")
    filepath = f"{park_id}.json"
    with open(filepath, 'w') as f:
        json.dump(response.json(), f)
    S3.put_object(filepath, key=f"wait-times/{filepath}")
    os.remove(filepath)


# cronjob task for updating rides table
def update_rides_table():
    logger.info("Polling SQS and updating rides table...")
    start = time.time()
    # use multiple threads
    threads = []
    for thread_num in range(1, env.THREAD_COUNT+1):
        threads.append(
            Thread(
                target=_update_rides_table_thread_task,
                kwargs={'thread_num':thread_num},
            )
        )
    run_threads(threads)
    logger.info(f"Updated ride wait times on DynamoDB in {time.time()-start:.1f} seconds")
# actual worker, defined for threading
def _update_rides_table_thread_task(thread_num:int):
    # poll sqs queue for new s3 uploads
    key, receipt_handle = SQS.poll_wait_times_queue()
    while key is not None:
        # download json from s3
        filepath = f"wait-times-{thread_num}.json"
        S3.get_object(key, filepath)
        park_id = int(re.search('\d+', key).group(0))
        # query for park name
        park_db_entry = DynamoDB.get_item(DynamoDB.PARKS_TABLE, lookup={'park_id':park_id})
        park_name = park_db_entry['park_name']
        # parse json for riderecords
        with open(filepath, 'r') as f:
            j = json.load(f)
            for land in j['lands']:
                for ride in land['rides']:
                    # put riderecords in rides table
                    r = DynamoDB.RideRecord(ride['id'], park_id, ride['name'], park_name, ride['wait_time'], ride['is_open'])
                    r.write_to_dynamo()
        # delete local file and sqs message
        os.remove(filepath)
        SQS.delete_wait_times_message(receipt_handle)
        # grab next message
        key, receipt_handle = SQS.poll_wait_times_queue()
    if receipt_handle is not None:
        SQS.delete_wait_times_message(receipt_handle)


# cronjob task for fulfilling / expiring alerts and notifying users
def close_out_alerts():
    logger.info("Sending alert notifications...")
    start = time.time()
    # get all parks
    parks = DynamoDB.list_parks()
    threads = []
    for p in parks:
        threads.append(
            Thread(
                target=_close_out_alerts_thread_task,
                kwargs={'park_id':p.park_id}
            )
        )
        if len(threads) == env.THREAD_COUNT:
            run_threads(threads)
            threads = []
    logger.info(f"Alert notifications complete in {time.time()-start:.1f} seconds")
# actual worker, defined for threading
def _close_out_alerts_thread_task(park_id:int):
    rides = DynamoDB.list_rides_by_park(park_id)
    rides.sort(key=lambda r:r.ride_id)
    alerts = DynamoDB.list_alerts_by_park(park_id)
    alerts.sort(key=lambda a:a.ride_id)
    # two pointer logic
    r, a = 0, 0
    while r < len(rides):
        while a < len(alerts):
            if alerts[a].ride_id < rides[r].ride_id:
                a += 1
            elif alerts[a].ride_id > rides[r].ride_id:
                r += 1
            else:
                # check ride wait time
                expired = alerts[a].end_time <= time.time()
                if rides[r].wait_time <= alerts[a].wait_time or expired:
                    # send text message for fulfilled/expired and delete alert
                    send_alert_sms(alerts[a].phone_number, rides[r].ride_name, alerts[a].wait_time if expired else rides[r].wait_time, expired)
                    alerts[a].delete_from_dynamo()