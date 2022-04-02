import json
import os
import requests
from utils.models import RideRecord, ParkRecord
from utils.aws import S3


# background task for pulling new parks data
def fetch_parks_json():
    # get latest parks.json
    filepath = 'parks.json'
    if not S3.object_exists(filepath):
        response = requests.get(f"https://queue-times.com/en-US/{filepath}")
        with open(filepath, 'w') as f:
            json.dump(response.json(), f)
        S3.put_object(filepath)
    else:
        filepath = S3.get_object(filepath)
    # parse parks.json
    with open(filepath, 'r') as f:
        j = json.load(f)
        for company in j:
            parks = company['parks']
            for park in parks:
                id, name = park['id'], park['name']
                r = ParkRecord(park_id=id, park_name=name)
                r.write_to_dynamo()
    # delete local json file
    os.remove(filepath)


# background task for pulling wait times data
def fetch_wait_times_json():
    # fetch wait times for all parks one at a time
    # ---> building with concurrency upgrades in mind
    # ---> dump jsons into s3 by park id
    # s3 upload event creates notification on sqs
    pass


# background task for updating rides table
def update_rides_table():
    # poll sqs queue for new s3 uploads
    # download json from s3
    pass


# background task for fulfilling / expiring alerts and notifying users ---> dynamo ttl will handle deletion