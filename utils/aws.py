import os
import boto3
from botocore.exceptions import ClientError
import env


BUCKET = f"qt-data-{env.ENV_NAME}"


def s3_upload(filepath:str) -> None:
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