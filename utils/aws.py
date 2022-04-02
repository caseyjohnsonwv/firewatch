import json
import os
from typing import Tuple
import boto3
from botocore.exceptions import ClientError
from dynamodb_json import json_util as djson
import env


### AWS WRAPPERS ###


class S3:
    BUCKET = f"qt-data-{env.ENV_NAME}"

    def put_object(filepath:str, key:str=None) -> None:
        if key is None:
            key = os.path.basename(filepath)
        client = boto3.client('s3')
        client.upload_file(filepath, S3.BUCKET, key)

    def get_object(key:str, filepath:str=None) -> str:
        if filepath is None:
            filepath = key
        client = boto3.client('s3')
        client.download_file(S3.BUCKET, key, filepath)
        return key


class SQS:
    QUEUE = f"qt-data-wait-times-update-queue-{env.ENV_NAME}"
    client = boto3.client('sqs')
    QUEUE_URL = client.get_queue_url(QueueName=QUEUE)['QueueUrl']
    del client

    def poll_wait_times_queue() -> Tuple[str, str]:
        # get s3 object key from upload event
        client = boto3.client('sqs')
        messages = client.receive_message(
            QueueUrl = SQS.QUEUE_URL,
            MaxNumberOfMessages = 1,
            WaitTimeSeconds = 20,
        )
        key, receipt_handle = None, None
        if messages.get('Messages') is not None:
            msg = messages['Messages'][0]
            receipt_handle = msg['ReceiptHandle']
            msg_json = json.loads(msg['Body'])
            if msg_json.get('Records'):
                key = msg_json['Records'][0]['s3']['object']['key']
        return (key, receipt_handle)

    def delete_wait_times_message(receipt_handle:str) -> None:
        client = boto3.client('sqs')
        client.delete_message(
            QueueUrl = SQS.QUEUE_URL,
            ReceiptHandle = receipt_handle,
        )


class DynamoDB:
    RIDES_TABLE = f"qt-rides-{env.ENV_NAME}"
    PARKS_TABLE = f"qt-parks-{env.ENV_NAME}"
    ALERTS_TABLE = f"qt-alerts-{env.ENV_NAME}"

    def get_item(tablename:str, lookup:dict) -> dict:
        dynamo = boto3.resource('dynamodb')
        table = dynamo.Table(tablename)
        response = table.get_item(Key=lookup)
        return djson.loads(response['Item'], as_dict=True)

    def put_item(tablename:str, item:dict) -> None:
        dynamo = boto3.resource('dynamodb')
        table = dynamo.Table(tablename)
        table.put_item(Item=item)

    def list_parks() -> list:
        dynamo = boto3.resource('dynamodb')
        table = dynamo.Table(DynamoDB.PARKS_TABLE)
        response = table.scan()
        items = response['Items'] 
        return [DynamoDB.ParkRecord(**djson.loads(item, as_dict=True)) for item in items]


    class ParkRecord:
        def __init__(self, park_id:int, park_name:str):
            self.park_id = park_id
            self.park_name = park_name

        def __repr__(self):
            return f"{self.park_name} ({self.park_id})"

        def _to_dict(self):
            return {'park_id':self.park_id, 'park_name':self.park_name}
        
        def write_to_dynamo(self):
            DynamoDB.put_item(DynamoDB.PARKS_TABLE, self._to_dict())


    class RideRecord:
        def __init__(self, ride_id:int, park_id:int, ride_name:str=None, park_name:str=None, wait_time:int=None, is_open:bool=None):
            self.ride_id = ride_id
            self.park_id = park_id
            self.ride_name = ride_name
            self.park_name = park_name
            self.wait_time = wait_time
            self.is_open = is_open

        def __repr__(self):
            return f"{self.ride_name} ({self.ride_id}) @ {self.park_name} ({self.park_id}): {'OPEN' if self.is_open else 'CLOSED'} - {self.wait_time}m"

        def _to_dict(self):
            # return all non-null class attributes
            return {attr:self.__dict__[attr] for attr in vars(self) if self.__dict__[attr] is not None}
        
        def write_to_dynamo(self):
            DynamoDB.put_item(DynamoDB.RIDES_TABLE, self._to_dict())