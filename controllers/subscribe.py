import json
import time
import uuid
from fastapi import APIRouter, Form, Response
from utils.aws import DynamoDB
from utils.sms import reply_to_sms
import utils.nlp as nlp
from pydantic import BaseModel


router = APIRouter(prefix='/alerts')


# class AlertCreationRequest(BaseModel):
#     phone_number:str
#     message_body:str


# @router.post('/create', status_code=201)
# def create_alert(req:AlertCreationRequest):
#     park = nlp.extract_park(req.message_body)
#     ride = nlp.extract_ride(req.message_body, park.park_id)
#     wait_time = nlp.extract_wait_time(req.message_body)
#     alert = DynamoDB.AlertRecord(str(uuid.uuid4()), req.phone_number, park.park_id, ride.ride_id, wait_time, time.time(), time.time()+7200)
#     alert.write_to_dynamo()
#     return {'alert':str(alert)}


@router.post('/twilio')
async def sms_reply(From: str = Form(...), Body: str = Form(...)):
    msg = Body
    phone_number = From

    alert_id = str(uuid.uuid4())
    park = nlp.extract_park(msg)
    ride = nlp.extract_ride(msg, park.park_id)
    wait_time = nlp.extract_wait_time(msg)
    start_time = time.time()
    end_time = start_time + 7200 #default of 2 hours

    alert = DynamoDB.AlertRecord(
        alert_id,
        phone_number,
        park.park_id,
        ride.ride_id,
        wait_time,
        start_time,
        end_time,
    )
    alert.write_to_dynamo()

    reply = f"Alert created! I'll watch https://queue-times.com/ for a wait under {wait_time} minutes on {ride.ride_name}."
    response = reply_to_sms([reply])
    return Response(content=str(response), media_type="application/xml")