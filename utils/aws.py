import os
import boto3
from botocore.exceptions import ClientError
from dynamodb_json import json_util as djson
import env


BUCKET = f"qt-data-{env.ENV_NAME}"
RIDES_TABLE = f"qt-rides-{env.ENV_NAME}"
ALERTS_TABLE = f"qt-alerts-{env.ENV_NAME}"


def s3_put_object(filepath:str) -> None:
    client = boto3.client('s3')
    client.upload_file(filepath, BUCKET, os.path.basename(filepath))


def s3_object_exists(obj_key:str) -> bool:
    s3 = boto3.resource('s3')
    try:
        s3.Object(BUCKET, obj_key).load()
    except ClientError as ex:
        if ex.response['Error']['Code'] == '404':
            return False
        else:
            raise
    return True


def dynamo_get_item(tablename:str, lookup:dict) -> dict:
    client = boto3.resource('dynamodb')
    table = client.Table(tablename)
    response = table.get_item(Key=lookup)
    return djson.loads(response['Item'], as_dict=True)


def dynamo_put_item(tablename:str, item:dict) -> None:
    client = boto3.resource('dynamodb')
    table = client.Table(tablename)
    table.put_item(Item=item)