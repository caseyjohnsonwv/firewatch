import csv
import re
import time
import pathlib
from random import choice, randint
from typing import Tuple
import requests


def main():
    rides_data = scrape_data()
    # GENERATE SAMPLE TEXT MESSAGES
    messages_dict = generate_messages(rides_data, data_multiplier=2)
    with open(f"{pathlib.Path(__file__).parent.resolve()}/training-data.csv", 'w') as f:
        w = csv.writer(f)
        for park, msg_list in messages_dict.items():
            data = [park, ' '.join(msg_list)]
            w.writerow(data)


def scrape_data(num_parks:int=0) -> dict:
    raw_data = requests.get('https://queue-times.com/en-US/parks.json').json()
    parks_data = {}
    for company in raw_data:
        parks = company['parks']
        for park in parks:
            id, name, country = park['id'], park['name'], park['country']
            if country != 'United States':
                continue
            banned_words = ['hurricane', 'harbor', 'water', 'aquatica', 'bay', 'cove']
            if any([w in name.lower() for w in banned_words]):
                continue
            name = re.sub('[^\w\s]+', '', name)
            parks_data[id] = name
    total_parks = len(parks_data.keys())

    if num_parks < 1:
        num_parks = total_parks + 1
    park_num = 1
    rides_data = {}
    for id, name in parks_data.items():
        print(f"({park_num}/{total_parks}): Fetching queue times for {name}...")
        rides_data[name] = []
        raw_data = requests.get(f"https://queue-times.com/en-US/parks/{id}/queue_times.json").json()
        for ride_class in raw_data['lands']:
            for ride in ride_class['rides']:
                rides_data[name].append(ride['name'])
        if len(rides_data[name]) == 0:
            del rides_data[name]
        else:
            park_num += 1
        if park_num >= num_parks:
            break
    del parks_data
    return rides_data


def generate_wait_string(max_minutes:int=180) -> Tuple[str, int]:
    # random minute times in 15 minute increments
    minutes = randint(1, max_minutes//15) * 15
    string = choice([
        f"{minutes} minutes",
        f"{minutes}m",
        f"{minutes} m",
        f"{minutes}min",
        f"{minutes} min",
        f"{minutes} mins",
    ])
    # return formatted string + time converted to seconds
    return (string, minutes*60)


def generate_two_timestamps(open_time_sec:int=36000, close_time_sec:int=79200, min_time_between:int=900) -> Tuple[str, str]:
    # choose two times
    time1 = randint(open_time_sec, close_time_sec-min_time_between)//900*900
    time2 = randint(time1, close_time_sec)//900*900
    outputs = [time1, time2]
    # random hh:mm timestamps in 15 minute increments
    for i,s in enumerate(outputs):
        ts = time.strftime(
            choice([
                '%I:%M %p',
                '%I:%M%p',
            ]),
            time.gmtime(s)
        )
        # randomly apply lowercase to AM/PM
        if randint(1,2) == 1:
            ts = ts.lower()
        # drop leading 0 from hours
        outputs[i] = ts[1:] if ts[0] == '0' else ts
    # unpack list to tuple
    return (outputs[0], outputs[1])


def generate_messages(rides_data:dict, data_multiplier:int=1, maximum:int=0) -> dict:
    # return park name mapped to list of sample messages
    message_templates = [
        "We'll ride RIDE_NAME if the wait is less than WAIT_TIME between TIME1 and TIME2",
        "Watch RIDE_NAME for a line shorter than WAIT_TIME before TIME1",
        "I'll wait up to WAIT_TIME for RIDE_NAME",
        "Watch RIDE_NAME until TIME1 for a line shorter than WAIT_TIME",
        "Let me know if RIDE_NAME gets a shorter wait than WAIT_TIME by TIME1",
        "I want to get on RIDE_NAME after TIME1 if the wait gets below WAIT_TIME",
        "Tell me when RIDE_NAME's wait gets under WAIT_TIME"
    ]
    total_messages = 0
    messages = {}
    for num in range(1, data_multiplier+1):
        for park, ride_list in rides_data.items():
            messages[park] = []
            print(f"Generating message set {num} for {park}...")
            for ride in ride_list:
                wait_string, wait_seconds = generate_wait_string()
                time1, time2 = generate_two_timestamps(min_time_between=wait_seconds)
                message = choice(message_templates)
                message = re.sub('RIDE_NAME', ride, message)
                message = re.sub('WAIT_TIME', wait_string, message)
                message = re.sub('TIME1', time1, message)
                message = re.sub('TIME2', time2, message)
                message += choice(['.','!'])
                if randint(1,2) == 1:
                    message = message.lower()
                messages[park].append(message.encode('ascii', 'ignore').decode())
                total_messages += 1
                if maximum > 0 and total_messages >= maximum:
                    return messages
    return messages


if __name__ == '__main__':
    main()