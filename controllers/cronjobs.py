import json
import os
from timeit import repeat
from fastapi_utils.tasks import repeat_every
import requests
from utils.aws import s3_upload, s3_object_exists

# pull new parks data every week
@repeat_every(seconds=604800)
async def fetch_parks_json():
    filepath = 'parks.json'
    if not s3_object_exists(filepath):
        response = requests.get(f"https://queue-times.com/en-US/{filepath}")
        with open(filepath, 'w') as f:
            json.dump(response.json(), f)
        s3_upload(filepath)
        os.remove(filepath)


# cronjob for pulling new data every 5 minutes and dumping it to s3
@repeat_every(seconds=300)
def fetch_wait_times_json():
    # fetch wait times for all parks one at a time
    # ---> building with concurrency upgrades in mind
    # ---> dump jsons into s3 by park id
    # s3 upload event creates notification on sqs
    pass


# background job for updating rides table
@repeat_every(seconds=30)
def update_rides_table():
    # poll sqs queue for new s3 uploads
    # download json from s3
    pass

# background job for fulfilling / expiring alerts and notifying users