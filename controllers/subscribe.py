import json
from fastapi import APIRouter, Body
from utils import aws, sms, watson

router = APIRouter()

@router.post('/handle-message')
def handle_message(req: str = Body(default={})):
    msg = json.loads(req).get('body')
    '''
    Check users table for this phone number
    ---> If no entry, create one, respond with hello
    ---> If entry with different park exists, verify new park exists
        - if yes, delete existing alerts and update park attribute
    
    Check for wait time data in rides table
    ---> Pull new data if needed
    
    Send request to IBM Watson to parse message with NLP
    ---> Verify that the ride name exists in the data file
    ---> Verify that ride is currently open
    ---> Parse message tokens to get maximum wait time
        - if no start/end time supplied, default to next 2 hours
    
    Use tokenized message to determine if user is creating, deleting, or updating an alert
    ---> If creating, add new data to alerts + users tables
    ---> If deleting, purge from alerts + users tables
    ---> If updating, verify that an alert exists for this ride
        - if yes, allow update to start/end time or wait time
    
    Create a text message response for the user and send it via Twilio
    '''
    ibm_resp = watson.send_nlp_request(msg)
    ride = watson.get_main_entity(ibm_resp)
    tokens = watson.get_tokens(ibm_resp)
    print(ride)
    print(tokens)


    return sms.response('Hello world!')