import re
from typing import Tuple
import spacy
from fuzzywuzzy import process as fuzzymatching
from utils.aws import DynamoDB


NLP = spacy.load('en_core_web_sm')


def extract_park(msg:str) -> DynamoDB.ParkRecord:
    parks = DynamoDB.list_parks()
    index, _ = _extract_best_match(msg, [p.park_name for p in parks])
    return parks[index]


def extract_ride(msg:str, park_id:int) -> DynamoDB.RideRecord:
    rides = DynamoDB.list_rides_by_park(park_id)
    index, _ = _extract_best_match(msg, [r.ride_name for r in rides])
    return rides[index]


def _extract_best_match(msg:str, match_list:list) -> Tuple[int, str]:
    doc = NLP(msg)
    closest_match, best_ratio = None, 0
    for chunk in doc.noun_chunks:
        match, ratio = fuzzymatching.extractOne(chunk.text, match_list)
        if ratio > best_ratio:
            closest_match = match
            best_ratio = ratio
            if ratio == 100:
                break
    # if ratio > 85:
    return match_list.index(closest_match), closest_match


def extract_wait_time(msg:str) -> int:
    # crude regex matching for now
    matches = re.findall('\d+', msg)
    if len(matches) > 0:
        wait_time = matches[0]
    return int(wait_time)