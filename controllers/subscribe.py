import logging
from fastapi import APIRouter, Form, Header, Response
from twilio.request_validator import RequestValidator
import utils.sms as sms
import env


logger = logging.getLogger(env.ENV_NAME)
live_router = APIRouter(prefix='/live')
test_router = APIRouter(prefix='/test')
validator = RequestValidator(env.TWILIO_AUTH_TOKEN)


@live_router.post('/twilio')
async def live_sms_reply(
    MessageSid:str = Form(...),
    SmsSid:str = Form(...),
    AccountSid:str = Form(...), 
    From:str = Form(...),
    To:str = Form(...),
    Body:str = Form(...), 
    NumMedia:int = Form(...),
    ReferralNumMedia:int = Form(...),
    X_Twilio_Signature:str = Header(...)
):
    # verify request authenticity
    url = f"https://{env.HEROKU_APP_NAME}.herokuapp.com{live_router.prefix}/twilio"
    params = {
        'MessageSid' : MessageSid,
        'SmsSid' : SmsSid,
        'AccountSid' : AccountSid,
        'From' : From,
        'To' : To,
        'Body' : Body,
        'NumMedia' : str(NumMedia),
        'ReferralNumMedia' : str(ReferralNumMedia),
    }
    if not validator.validate(url, params, X_Twilio_Signature):
        logger.warning(f"Invalid requestor: {AccountSid}")
        return Response(status_code=403)

    # process message
    logger.info(f"Received message: '{Body}'")
    reply = sms.process_message(Body, From)
    logger.info(f"Response message: <<{reply}>>")
    return sms.create_reply_twiml([reply], status_code=200)


# no validation, only mounted into app for local env
@test_router.post('/twilio')
async def test_sms_reply(Body:str = Form(...), From:str = Form(...)):
    logger.info(f"Received message: '{Body}'")
    reply = sms.process_message(Body, From)
    logger.info(f"Response message: <<{reply}>>")
    return sms.create_reply_twiml([reply], status_code=200)