import json
from fastapi import APIRouter, Body
from utils import sms

router = APIRouter()

@router.post('/handle-message')
def handle_message(req: str = Body(default={})):
    msg = json.loads(req).get('body')
    print(msg)
    return sms.response('Hello!')