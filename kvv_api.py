#!/usr/bin/env python3

import urllib.request
import json
from typing import *
from dateutil import parser
from datetime import datetime
from time import sleep


API_TOKEN: str = "TODO"  # like "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" (hex)
ORIGIN_ID: str = "TODO" # like: "0000000" (dec)
DESTINATION_ID: str = "7001105" # like: "0000000" (dec)

API_REQUEST_TRIP: str = f"https://www.rmv.de/hapi/trip?originId={ORIGIN_ID}&destId={DESTINATION_ID}&accessId={API_TOKEN}&format=json"
API_REQUEST_DEP: str = f"https://projekte.kvv-efa.de/sl3-alone/XSLT_DM_REQUEST?outputFormat=JSON&coordOutputFormat=WGS84[dd.ddddd]&depType=stopEvents&locationServerActive=1&mode=direct&name_dm={DESTINATION_ID}&type_dm=stop&useOnlyStops=1&useRealtime=1" #&time=23%3A59


def get_json_data(source_url: str):
    with urllib.request.urlopen(source_url) as url:
        data: str = url.read().decode()

    #f = open('mockdata.json')

    # returns JSON object as
    # a dictionary
    return json.loads(data)


def filter_data_trip(data, exclude_destinations: Set[str] = []) -> Iterable[Tuple[float, str, str]]:
    for element in data['Trip']:
        option = element['LegList']['Leg'][0]
        try:
            time = time_converter(option['Origin']['date'], option['Origin']['time'])
        except ValueError:
            # ignore negative time deltas (departures in the past are irrelevant)
            continue

        line_name = option['Product']['line']
        destination = option['direction']

        if destination not in exclude_destinations:
            yield time, line_name, destination


def filter_data_dep(data, exclude_destinations: Set[str] = []) -> Iterable[Tuple[str, str, str]]:
    for element in data['departureList']:
        if int(element['countdown']) < 15:
            if int(element['countdown']) == 0:
                time = "jetzt"
            else:
                time = f"{element['countdown']} min"
        else:
            time = f"{element['dateTime']['hour']}:{int(element['dateTime']['minute']):02d}"

        line_name = element['servingLine']['number']
        destination = element['servingLine']['direction']

        if destination not in exclude_destinations and element['platform'] == "2":
            yield time, line_name, destination


def time_converter(rmv_date: str, rmv_time: str) -> float:
    rmv_date_time = f"{rmv_date} {rmv_time}"
    time_offset = parser.parse(rmv_date_time) - datetime.now()
    if time_offset.days < 0:
        raise ValueError('Given time is in the past')
    else:
        return float(time_offset.seconds)


def print_to_console(data: List[Tuple[str, str, str]], num_entries: int = 5) -> None:
    print("---------------")
    for time, line, destination in data[:num_entries]:
        print(f"{time}\t\t{line}\t\t{destination}")
    print("---------------")
