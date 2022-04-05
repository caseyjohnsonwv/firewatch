import spacy
from fuzzywuzzy import process as fuzzymatching
from utils.aws import DynamoDB


NLP = spacy.load('en_core_web_sm')


def extract_park_name(msg:str) -> str:
    park_names = [r.park_name for r in DynamoDB.list_parks()]
    return _extract_best_match(msg, park_names)


def extract_ride_name(msg:str, park_id:int) -> str:
    ride_names = [r.ride_name for r in DynamoDB.list_rides_by_park(park_id)]
    return _extract_best_match(msg, ride_names)


def _extract_best_match(msg:str, match_list:list) -> str:
    doc = NLP(msg)
    closest_match, best_ratio = None, 0
    for chunk in doc.noun_chunks:
        match, ratio = fuzzymatching.extractOne(chunk.text, match_list)
        if ratio > best_ratio:
            closest_match = match
            best_ratio = ratio
            if ratio == 100:
                break

    if ratio > 85:
        return closest_match