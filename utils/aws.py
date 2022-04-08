import logging
import datetime
import boto3
from boto3.dynamodb.conditions import Key
from dynamodb_json import json_util as djson
import env


logger = logging.getLogger(env.ENV_NAME)


### AWS WRAPPERS ###


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

    def list_alerts_by_phone_number(phone_number:str) -> list:
        logger.debug(f"Querying {DynamoDB.ALERTS_TABLE} table for phone_number = {phone_number}")
        dynamo = boto3.resource('dynamodb')
        table = dynamo.Table(DynamoDB.ALERTS_TABLE)
        response = table.query(
            IndexName="alerts_by_phone_number",
            KeyConditionExpression=Key('phone_number').eq(phone_number),
        )
        items = response['Items'] 
        return [DynamoDB.AlertRecord(**djson.loads(item, as_dict=True)) for item in items]

    def delete_alert(alert_id:str) -> None:
        logger.debug(f"Deleting alert {alert_id} from {DynamoDB.ALERTS_TABLE}")
        dynamo = boto3.resource('dynamodb')
        table = dynamo.Table(DynamoDB.ALERTS_TABLE)
        table.delete_item(
            Key={'alert_id':alert_id}
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
        def __init__(self, alert_id:str, phone_number:str, park_id:int, ride_id:int, wait_time:int, start_time:int, end_time:int):
            self.alert_id = alert_id
            self.phone_number = phone_number
            self.park_id = park_id
            self.ride_id = ride_id
            self.wait_time = wait_time
            self.start_time = int(start_time)
            self.end_time = int(end_time)
        
        def __repr__(self):
            end = datetime.datetime.fromtimestamp(self.end_time).strftime('%I:%M')
            start = datetime.datetime.fromtimestamp(self.start_time).strftime('%I:%M')
            return f"{self.alert_id} - {self.phone_number} [{self.ride_id} @ {self.park_id}] {start} - {end} ({self.wait_time}m)"

        def _to_dict(self):
            # return all non-null class attributes
            return {attr:self.__dict__[attr] for attr in vars(self) if self.__dict__[attr] is not None}
        
        def write_to_dynamo(self):
            DynamoDB.put_item(DynamoDB.ALERTS_TABLE, self._to_dict())

        def delete_from_dynamo(self):
            DynamoDB.delete_alert(self.alert_id)