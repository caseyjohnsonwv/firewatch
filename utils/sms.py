import phonenumbers as pn
from twilio.rest import Client
import env


def send_alert_sms(recipient:str, ride_name:str, wait_time:int, expired:bool=False) -> None:
    if expired:
        msg = f"Your alert for {ride_name} has expired! The line did not get shorter than {wait_time} minutes."
    else:
        msg = f"The line for {ride_name.strip()} is currently {wait_time} minutes! This alert has been deleted."
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