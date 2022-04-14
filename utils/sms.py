import time
from typing import List
from fastapi import Response
import phonenumbers as pn
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from . import nlp, logic
import env


def create_reply_twiml(messages:List[str], status_code:int=200) -> str:
    response = MessagingResponse()
    for msg in messages:
        response.message(msg)
    return Response(
        content=str(response),
        media_type="application/xml",
        status_code=status_code
    )


def send_alert_sms(recipient:str, ride_name:str, wait_time:int, expired:bool=False) -> None:
    if expired:
        msg = f"Your alert for {ride_name} has expired! The line did not get shorter than {wait_time} minutes."
    else:
        msg = f"The line for {ride_name.strip()} is currently {wait_time} minutes! This alert is no longer active."
    _send_sms(recipient, msg)


def _send_sms(recipient:str, msg:str) -> None:
    client = Client(env.TWILIO_ACCOUNT_SID, env.TWILIO_AUTH_TOKEN)
    client.messages.create(
        body=msg,
        from_= pn.format_number(
            pn.parse(env.TWILIO_PHONE_NUMBER, "US"),
            pn.PhoneNumberFormat.E164
        ),
        to= pn.format_number(
            pn.parse(recipient, "US"),
            pn.PhoneNumberFormat.E164
        ),
    )


def process_message(msg:str, phone_number:str) -> str:
    # fail if fuzzy matching can't detect park name
    try:
        park = nlp.extract_park(msg)
    except nlp.NLPException:
        return "Sorry, I'm not sure what park you're visting. Try rephrasing your message."

    # fail if fuzzy matching can't detect ride name
    try:
        ride = nlp.extract_ride(msg, park.id)
    except nlp.NLPException:
        return f"Sorry, I'm not sure which ride at {park.name} you're asking about. Try rephrasing your message."

    # TODO: make this actually work as intended
    wait_time = nlp.extract_wait_time(msg)
    expiration = int(time.time()) + 7200 # default of 2 hours

    reply = logic.alert_creation_flow(ride=ride, park=park, phone_number=phone_number, wait_time=wait_time, expiration=expiration)
    return reply