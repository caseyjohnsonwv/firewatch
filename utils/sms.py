from twilio.twiml.messaging_response import MessagingResponse

def response(msg):
    resp = MessagingResponse()
    resp.message(msg)
    return str(resp)