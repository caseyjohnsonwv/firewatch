import json
import os
import re
from threading import Thread
import time
import requests
from utils.aws import S3, SQS, DynamoDB
from utils.sms import send_alert_sms
import env


# cronjob task for pulling new parks data
def fetch_parks_json():
    # get latest parks.json
    filepath = 'parks.json'
    response = requests.get(f"https://queue-times.com/en-US/{filepath}")
    with open(filepath, 'w') as f:
        json.dump(response.json(), f)
    S3.put_object(filepath)
    # parse parks.json
    with open(filepath, 'r') as f:
        j = json.load(f)
        for company in j:
            parks = company['parks']
            for park in parks:
                id, name = park['id'], park['name']
                r = DynamoDB.ParkRecord(park_id=id, park_name=name)
                r.write_to_dynamo()
    # delete local json file
    os.remove(filepath)


# cronjob task for pulling wait times data
def fetch_wait_times_json():
    all_parks = DynamoDB.list_parks()
    for park in all_parks:
        response = requests.get(f"https://queue-times.com/en-US/parks/{park.park_id}/queue_times.json")
        filepath = f"{park.park_id}.json"
        with open(filepath, 'w') as f:
            json.dump(response.json(), f)
        S3.put_object(filepath, key=f"wait-times/{filepath}")
        os.remove(filepath)


# cronjob task for updating rides table
def update_rides_table():
    # use multiple threads
    threads = []
    for thread_num in range(1, env.THREAD_COUNT+1):
        threads.append(
            Thread(
                target=_update_rides_table_thread_task,
                kwargs={'thread_num':thread_num},
            )
        )
    for th in threads:
        th.start()
    for th in threads:
        th.join()
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
    # get all active park_id's from alerts table
    parks = DynamoDB.list_parks()
    # split threads by park
    threads = []
    for i in range(len(parks)):
        park = parks[i]
        threads.append(
            Thread(
                target=_close_out_alerts_thread_task,
                kwargs={'p':park},
            )
        )
        if len(threads) == env.THREAD_COUNT:
            for th in threads:
                th.start()
            for th in threads:
                th.join()
            threads = []
# actual worker, defined for threading
def _close_out_alerts_thread_task(p:DynamoDB.ParkRecord):
    # get all alerts for this park
    alerts = DynamoDB.list_alerts_by_park(p.park_id)
    if len(alerts) > 0:
        # sort by ride to reduce db queries
        alerts.sort(key = lambda a:a.ride_id)
        r = DynamoDB.RideRecord(**DynamoDB.get_item(DynamoDB.RIDES_TABLE, lookup={'ride_id':alerts[0].ride_id}))
        for a in alerts:
            if r.ride_id != a.ride_id:
                r = DynamoDB.RideRecord(**DynamoDB.get_item(DynamoDB.RIDES_TABLE, lookup={'ride_id':a.ride_id}))
            # check ride wait time
            expired = a.end_time <= time.time()
            if r.wait_time <= a.wait_time or expired:
                # send text message for fulfilled/expired and delete alert
                send_alert_sms(a.phone_number, r.ride_name, a.wait_time if expired else r.wait_time, expired)
                a.delete_from_dynamo()