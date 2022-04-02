import os
import boto3
from botocore.exceptions import ClientError
from dynamodb_json import json_util as djson
import env


class S3:
    BUCKET = f"qt-data-{env.ENV_NAME}"

    def put_object(filepath:str) -> None:
        client = boto3.client('s3')
        client.upload_file(filepath, S3.BUCKET, os.path.basename(filepath))

    def object_exists(obj_key:str) -> bool:
        s3 = boto3.resource('s3')
        try:
            s3.Object(S3.BUCKET, obj_key).load()
        except ClientError as ex:
            if ex.response['Error']['Code'] == '404':
                return False
            else:
                raise
        return True

    def get_object(key:str) -> str:
        client = boto3.client('s3')
        client.download_file(S3.BUCKET, key, key)
        return key


class DynamoDB:
    RIDES_TABLE = f"qt-rides-{env.ENV_NAME}"
    PARKS_TABLE = f"qt-parks-{env.ENV_NAME}"
    ALERTS_TABLE = f"qt-alerts-{env.ENV_NAME}"

    def get_item(tablename:str, lookup:dict) -> dict:
        client = boto3.resource('dynamodb')
        table = client.Table(tablename)
        response = table.get_item(Key=lookup)
        return djson.loads(response['Item'], as_dict=True)

    def put_item(tablename:str, item:dict) -> None:
        client = boto3.resource('dynamodb')
        table = client.Table(tablename)
        table.put_item(Item=item)