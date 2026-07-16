#!/usr/bin/env python3
# resolve.py — build request.json for the Google Routes API
# reads: config (key=value), favs.json (place codes)
# writes: request.json (for inspection, same as the old cc pipeline)

import json

CONFIG_FILE = 'config'
FAVS_FILE = 'favs.json'
REQUEST_FILE = 'request.json'


def load_config():
    """Parse the plain key=value config file."""
    cfg = {}
    with open(CONFIG_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            cfg[key.strip()] = value.strip()
    return cfg


def load_favs():
    with open(FAVS_FILE) as f:
        return json.load(f)


def resolve_token(token, favs, city, country):
    """Turn a typed token into a Routes API origin/destination object."""
    token = token.strip()
    code = token.upper()

    if code in favs:
        val = favs[code]
        if val.startswith('ChIJ'):
            return {'placeId': val}
        elif ',' in val and all(
            p.strip().lstrip('-').replace('.', '', 1).isdigit()
            for p in val.split(',')
        ):
            lat, lng = (float(p.strip()) for p in val.split(','))
            return {'location': {'latLng': {'latitude': lat, 'longitude': lng}}}
        else:
            return {'address': f'{val}, {country}'}
    else:
        return {'address': f'{token}, {city}, {country}'}


def build_request(start, dest, type_, timestamp):
    """Build the full Routes API request body, write request.json, return it."""
    cfg = load_config()
    favs = load_favs()

    city = cfg.get('_CITY', 'Auckland')
    mode = cfg.get('_MODE', 'TRANSIT')
    pref = cfg.get('_PREF', 'LESS_WALKING')
    country = cfg.get('_COUNTRY', 'New Zealand')

    req = {
        'origin': resolve_token(start, favs, city, country),
        'destination': resolve_token(dest, favs, city, country),
        'travelMode': mode,
        'transitPreferences': {'routingPreference': pref},
        'departureTime': None,
        'arrivalTime': None,
    }

    if type_ == 'DEP' and timestamp:
        req['departureTime'] = timestamp
    elif type_ == 'ARR' and timestamp:
        req['arrivalTime'] = timestamp

    with open(REQUEST_FILE, 'w') as f:
        json.dump(req, f, indent=2)

    return req
