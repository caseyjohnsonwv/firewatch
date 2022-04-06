import json
import logging
import os
import datetime
from typing import Tuple
import boto3
from boto3.dynamodb.conditions import Key, Attr
from dynamodb_json import json_util as djson
import env


logger = logging.getLogger(env.ENV_NAME)


### AWS WRAPPERS ###


class S3:
    BUCKET = f"qt-data-{env.ENV_NAME}"

    def put_object(filepath:str, key:str=None) -> None:
        if key is None:
            key = os.path.basename(filepath)
        logger.debug(f"Uploading {filepath} to S3 as {key}")
        client = boto3.client('s3')
        client.upload_file(filepath, S3.BUCKET, key)
        logger.debug("Upload complete")

    def get_object(key:str, filepath:str=None) -> str:
        if filepath is None:
            filepath = key
        logger.debug(f"Downloading {key} from S3 to {filepath}")
        client = boto3.client('s3')
        client.download_file(S3.BUCKET, key, filepath)
        logger.debug("Download complete")
        return key


class SQS:
    client = boto3.client('sqs')
    WAIT_TIMES_QUEUE_URL = client.get_queue_url(
        QueueName=f"qt-data-wait-times-update-queue-{env.ENV_NAME}"
    )['QueueUrl']
    del client

    def _poll_queue(queue_url:str) -> dict:
        # get s3 object key from upload event
        logger.debug("Polling SQS queue")
        client = boto3.client('sqs')
        messages = client.receive_message(
            QueueUrl = queue_url,
            MaxNumberOfMessages = 1,
            WaitTimeSeconds = 20,
        )
        msg_json, receipt_handle = None, None
        if messages.get('Messages') is not None:
            logger.debug("1 message received")
            msg = messages['Messages'][0]
            receipt_handle = msg['ReceiptHandle']
            msg_json = json.loads(msg['Body'])
        return (msg_json, receipt_handle)

    def _publish_to_queue(queue_url:str, msg_body:str) -> None:
        client = boto3.client('sqs')
        logger.debug("Publishing to SQS queue")
        client.send_message(
            QueueUrl = queue_url,
            MessageBody = msg_body,
        )
        logger.debug("Publish complete")

    def _delete_message(queue_url:str, receipt_handle:str) -> None:
        client = boto3.client('sqs')
        logger.debug("Deleting from SQS queue")
        client.delete_message(
            QueueUrl = queue_url,
            ReceiptHandle = receipt_handle,
        )
        logger.debug("Deletion complete")
    
    def poll_wait_times_queue() -> Tuple[str, str]:
        msg_json, receipt_handle = SQS._poll_queue(SQS.WAIT_TIMES_QUEUE_URL)
        # parse s3 upload event
        key = None
        if msg_json is not None and msg_json.get('Records'):
            key = msg_json['Records'][0]['s3']['object']['key']
        return (key, receipt_handle)

    def delete_wait_times_message(receipt_handle:str) -> None:
        SQS._delete_message(SQS.WAIT_TIMES_QUEUE_URL, receipt_handle)        



class DynamoDB:
    RIDES_TABLE = f"qt-rides-{env.ENV_NAME}"
    PARKS_TABLE = f"qt-parks-{env.ENV_NAME}"
    ALERTS_TABLE = f"qt-alerts-{env.ENV_NAME}"

    def get_item(tablename:str, lookup:dict) -> dict:
        logger.debug(f"Querying {tablename} with key = {lookup}")
        dynamo = boto3.resource('dynamodb')
        table = dynamo.Table(tablename)
        response = table.get_item(Key=lookup)
        return djson.loads(response['Item'], as_dict=True)

    def put_item(tablename:str, item:dict) -> None:
        logger.debug(f"Writing {item} to {tablename}")
        dynamo = boto3.resource('dynamodb')
        table = dynamo.Table(tablename)
        table.put_item(Item=item)

    def list_parks() -> list:
        logger.debug(f"Scanning {DynamoDB.PARKS_TABLE} table")
        dynamo = boto3.resource('dynamodb')
        table = dynamo.Table(DynamoDB.PARKS_TABLE)
        response = table.scan()
        items = response['Items'] 
        return [DynamoDB.ParkRecord(**djson.loads(item, as_dict=True)) for item in items]

    def list_rides_by_park(park_id:int) -> list:
        logger.debug(f"Querying {DynamoDB.RIDES_TABLE} table for park_id = {park_id}")
        dynamo = boto3.resource('dynamodb')
        table = dynamo.Table(DynamoDB.RIDES_TABLE)
        response = table.query(
            IndexName="rides_by_park",
            KeyConditionExpression=Key('park_id').eq(park_id),
        )
        items = response['Items']
        return [DynamoDB.RideRecord(**djson.loads(item, as_dict=True)) for item in items]

    def list_alerts_by_park(park_id:int) -> list:
        logger.debug(f"Querying {DynamoDB.ALERTS_TABLE} table for park_id = {park_id}")
        dynamo = boto3.resource('dynamodb')
        table = dynamo.Table(DynamoDB.ALERTS_TABLE)
        response = table.query(
            IndexName="alerts_by_park",
            KeyConditionExpression=Key('park_id').eq(park_id),
        )
        items = response['Items'] 
        return [DynamoDB.AlertRecord(**djson.loads(item, as_dict=True)) for item in items]

    def delete_alert(phone_number:str, ride_id:int) -> None:
        logger.debug(f"Deleting alert for {ride_id} by {phone_number} from {DynamoDB.ALERTS_TABLE}")
        dynamo = boto3.resource('dynamodb')
        table = dynamo.Table(DynamoDB.ALERTS_TABLE)
        table.delete_item(
            Key={'phone_number':phone_number},
            ConditionExpression=Attr('ride_id').eq(ride_id)
        )


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
        def __init__(self, ride_id:int, park_id:int, ride_name:str, park_name:str, wait_time:int, is_open:bool):
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


    class AlertRecord:
        def __init__(self, phone_number:str, park_id:int, ride_id:int, wait_time:int, start_time:int, end_time:int):
            self.phone_number = phone_number
            self.park_id = park_id
            self.ride_id = ride_id
            self.wait_time = wait_time
            self.start_time = int(start_time)
            self.end_time = int(end_time)
        
        def __repr__(self):
            end = datetime.datetime.fromtimestamp(self.end_time).strftime('%I:%M')
            start = datetime.datetime.fromtimestamp(self.start_time).strftime('%I:%M')
            return f"{self.phone_number} [{self.ride_id} @ {self.park_id}] {start} - {end} ({self.wait_time}m)"

        def _to_dict(self):
            # return all non-null class attributes
            return {attr:self.__dict__[attr] for attr in vars(self) if self.__dict__[attr] is not None}
        
        def write_to_dynamo(self):
            DynamoDB.put_item(DynamoDB.ALERTS_TABLE, self._to_dict())

        def delete_from_dynamo(self):
            DynamoDB.delete_alert(self.phone_number, self.ride_id)