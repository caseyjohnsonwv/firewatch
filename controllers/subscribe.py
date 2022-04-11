import logging
import time
import uuid
from fastapi import APIRouter, Form, Response
from utils.aws import DynamoDB
from utils.sms import reply_to_sms
import utils.nlp as nlp
import env


logger = logging.getLogger(env.ENV_NAME)
router = APIRouter(prefix='/alerts')


@router.post('/twilio')
async def sms_reply(From: str = Form(...), Body: str = Form(...), AccountSid: str = Form(...)):
    msg = Body
    phone_number = From
    account_sid = AccountSid

    # verify request authenticity
    # this can be done better with TLS + request signing
    if account_sid != env.TWILIO_ACCOUNT_SID:
        logger.warning(f"Invalid requestor: {account_sid}")
        return Response(status_code=404)

    logger.info(f"Received message: '{msg}'")
    alert_id = str(uuid.uuid4())

    # fail if fuzzy matching can't detect park name
    try:
        park = nlp.extract_park(msg)
    except nlp.NLPException:
        reply = "Sorry, I'm not sure what park you're visting. Try rephrasing your message."
        return reply_to_sms([reply])

    # fail if fuzzy matching can't detect ride name
    try:
        ride = nlp.extract_ride(msg, park.park_id)
    except nlp.NLPException:
        reply = f"Sorry, I'm not sure which ride at {park.park_name} you're asking about. Try rephrasing your message."
        return reply_to_sms([reply])

    # TODO: make this actually work as intended
    wait_time = nlp.extract_wait_time(msg)
    start_time = time.time()
    end_time = start_time + 7200 # default of 2 hours

    # create the alert record
    alert = DynamoDB.AlertRecord(
        alert_id,
        phone_number,
        park.park_id,
        ride.ride_id,
        wait_time,
        start_time,
        end_time,
    )

    # don't create alert if ride is not open
    if not ride.is_open:
        reply = f"Whoops, it looks like {ride.ride_name} at {park.park_name} is not open right now. Try again later."
        return reply_to_sms([reply])

    # don't create alert if wait is already short enough
    elif ride.wait_time <= alert.wait_time:
        reply = f"The wait time for {ride.ride_name} at {park.park_name} is currently {ride.wait_time} minutes."
        return reply_to_sms([reply])

    # otherwise write alert to database
    else:
        alert.write_to_dynamo()
        logger.info(f"Created alert for {ride.ride_name} @ {park.park_name} <<{alert}>>")
        reply = f"Alert created! Watching {ride.ride_name} at {park.park_name} for a wait under {wait_time} minutes. Powered by https://queue-times.com/"
        return reply_to_sms([reply], status_code=201)