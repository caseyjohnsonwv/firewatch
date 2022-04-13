import re
from typing import Tuple
import spacy
from fuzzywuzzy import process as fuzzymatching
from utils.postgres import Ride, Park, CrudUtils


NLP = spacy.load('en_core_web_sm')


class NLPException(Exception):
    pass


def extract_park(msg:str) -> Park:
    parks = CrudUtils.read_parks()
    res = _extract_best_match(msg, [p.name for p in parks], threshold=30)
    if res is None:
        raise NLPException
    index, _ = res
    return parks[index]


def extract_ride(msg:str, park_id:int) -> Ride:
    rides = CrudUtils.read_rides(park_id=park_id)
    res = _extract_best_match(msg, [r.name for r in rides], threshold=70)
    if res is None:
        raise NLPException
    index, _ = res
    return rides[index]


def _extract_best_match(msg:str, match_list:list, threshold:int=0) -> Tuple[int, str]:
    doc = NLP(msg)
    closest_match, best_ratio = None, 0
    for chunk in doc.noun_chunks:
        match, ratio = fuzzymatching.extractOne(chunk.text, match_list)
        if ratio > best_ratio:
            closest_match = match
            best_ratio = ratio
            if ratio == 100:
                break
    if ratio > threshold:
        return match_list.index(closest_match), closest_match


def extract_wait_time(msg:str) -> int:
    # crude regex matching for now
    matches = re.findall('\d+', msg)
    if len(matches) > 0:
        wait_time = matches[0]
    return int(wait_time)