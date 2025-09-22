#!/usr/bin/env python3

import urllib.request
import json
from typing import *
from dateutil import parser
from datetime import datetime
from time import sleep


API_TOKEN: str = "TODO"  # like "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" (hex)
ORIGIN_ID: str = "TODO" # like: "0000000" (dec)

# Station configuration for North and South directions
STATION_CONFIG = {
    "NORTH": {
        "id": "7001105",  # Same station ID, different platform
        "platform": "1",  # Platform for northbound trains
        "name": "← Richt. Neureut"
    },
    "SOUTH": {
        "id": "7001105",  # Same station ID, different platform  
        "platform": "2",  # Platform for southbound trains
        "name": "→ Richt. Innenstadt"
    }
}

# Default direction (currently South as in your original code)
current_direction = "SOUTH"

def get_api_request_dep(direction: str = None) -> str:
    """Generate API request URL for the specified direction"""
    global current_direction
    if direction:
        current_direction = direction
    
    station_id = STATION_CONFIG[current_direction]["id"]
    return f"https://projekte.kvv-efa.de/sl3-alone/XSLT_DM_REQUEST?outputFormat=JSON&coordOutputFormat=WGS84[dd.ddddd]&depType=stopEvents&locationServerActive=1&mode=direct&name_dm={station_id}&type_dm=stop&useOnlyStops=1&useRealtime=1"

def get_api_request_trip(direction: str = None) -> str:
    """Generate API request URL for trip planning"""
    global current_direction
    if direction:
        current_direction = direction
    
    destination_id = STATION_CONFIG[current_direction]["id"]
    return f"https://www.rmv.de/hapi/trip?originId={ORIGIN_ID}&destId={destination_id}&accessId={API_TOKEN}&format=json"

# Maintain backward compatibility
API_REQUEST_DEP: str = get_api_request_dep()
API_REQUEST_TRIP: str = get_api_request_trip()


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
    """Filter departure data based on current direction (platform)"""
    target_platform = STATION_CONFIG[current_direction]["platform"]
    
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

        if destination not in exclude_destinations and element['platform'] == target_platform:
            yield time, line_name, destination


def switch_direction(new_direction: str) -> str:
    """Switch to North or South direction and return the new direction"""
    global current_direction
    if new_direction in STATION_CONFIG:
        current_direction = new_direction
        print(f"🚇 Direction switched to: {STATION_CONFIG[current_direction]['name']} (Platform {STATION_CONFIG[current_direction]['platform']})")
    return current_direction


def get_current_direction_info() -> dict:
    """Get current direction configuration"""
    return {
        "direction": current_direction,
        "name": STATION_CONFIG[current_direction]["name"],
        "platform": STATION_CONFIG[current_direction]["platform"],
        "station_id": STATION_CONFIG[current_direction]["id"]
    }


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
