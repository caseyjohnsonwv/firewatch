import time
import uuid
from fastapi import APIRouter
from utils.aws import DynamoDB
# import utils.sms as sms
import utils.nlp as nlp
from pydantic import BaseModel


router = APIRouter(prefix='/alerts')


class AlertCreationRequest(BaseModel):
    phone_number:str
    message_body:str


@router.post('/create', status_code=201)
def create_alert(req:AlertCreationRequest):
    park = nlp.extract_park(req.message_body)
    ride = nlp.extract_ride(req.message_body, park.park_id)
    wait_time = nlp.extract_wait_time(req.message_body)
    alert = DynamoDB.AlertRecord(str(uuid.uuid4()), req.phone_number, park.park_id, ride.ride_id, wait_time, time.time(), time.time()+3600000)
    alert.write_to_dynamo()
    return {'alert':str(alert)}