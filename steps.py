#!/usr/bin/env python3
# steps.py — read response.json (Routes API result), write steps.json
# input: the raw API response dict, plus origin/dest strings as typed
# output: a flat structured steps list, written to steps.json for inspection

import json
from datetime import datetime

STEPS_FILE = 'steps.json'


def to_24h(time_str):
    return datetime.strptime(time_str, "%I:%M %p").strftime("%H:%M")


def build_steps(response_data, origin, dest):
    """Turn a Routes API response into the flat steps structure, write
    steps.json, return it. Raises KeyError/IndexError if the response
    doesn't contain a usable route -- caller should catch and show
    error.tpl."""

    leg = response_data['routes'][0]['legs'][0]
    steps = []

    for step in leg['steps']:
        mode = step['travelMode']
        td = step.get('transitDetails')

        if mode == 'TRANSIT' and td:
            vehicle = td['transitLine']['vehicle']['name']['text']
            steps.append({
                'type': vehicle.upper(),
                'line': td['transitLine'].get('name') or td['transitLine'].get('nameShort', ''),
                'headsign': td['headsign'],
                'depart': td['stopDetails']['departureStop']['name'],
                'arrive': td['stopDetails']['arrivalStop']['name'],
                'dep_time': to_24h(td['localizedValues']['departureTime']['time']['text']),
                'arr_time': to_24h(td['localizedValues']['arrivalTime']['time']['text']),
                'stops': td['stopCount'],
            })
        elif mode == 'WALK':
            inst = step.get('navigationInstruction', {}).get('instructions')
            if inst:
                steps.append({
                    'type': 'WALK',
                    'instruction': inst,
                    'distance': step['localizedValues']['distance']['text'],
                })

    transit_steps = [s for s in steps if s.get('arr_time')]
    arrival = transit_steps[-1]['arr_time'] if transit_steps else None

    out = {
        'origin': origin,
        'dest': dest,
        'distance': leg['localizedValues']['distance']['text'],
        'duration': leg['localizedValues']['duration']['text'],
        'arrival': arrival,
        'steps': steps,
    }

    with open(STEPS_FILE, 'w') as f:
        json.dump(out, f, indent=2)

    return out
