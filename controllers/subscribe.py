import logging
import time
import uuid
from fastapi import APIRouter, Form, Response
from utils.postgres import Alert, CrudUtils
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
        ride = nlp.extract_ride(msg, park.id)
    except nlp.NLPException:
        reply = f"Sorry, I'm not sure which ride at {park.name} you're asking about. Try rephrasing your message."
        return reply_to_sms([reply])

    # TODO: make this actually work as intended
    wait_time = nlp.extract_wait_time(msg)
    expiration = int(time.time()) + 7200 # default of 2 hours

    # don't create alert if ride is not open
    if not ride.is_open:
        reply = f"Whoops, it looks like {ride.name} at {park.name} is not open right now. Try again later."
        return reply_to_sms([reply])

    # don't create alert if wait is already short enough
    elif ride.wait_time <= wait_time:
        reply = f"The wait time for {ride.name} at {park.name} is currently {ride.wait_time} minutes."
        return reply_to_sms([reply])

    # otherwise write alert to database
    else:
        alert = CrudUtils.create_alert(
            id=alert_id,
            park_id=park.id,
            ride_id=ride.id,
            phone_number=phone_number,
            wait_time=wait_time,
            expiration=expiration,
        )
        logger.info(f"Created alert for {ride.name} @ {park.name} <<{alert}>>")
        reply = f"Alert created! Watching {ride.name} at {park.name} for a wait under {wait_time} minutes. Powered by https://queue-times.com/"
        return reply_to_sms([reply], status_code=201)