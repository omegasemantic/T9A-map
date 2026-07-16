#!/usr/bin/env python3
from bottle import Bottle, request, template
import subprocess, json, re
from datetime import datetime

import resolve
import steps as steps_mod
import result as result_mod

app = Bottle()

GMAPS_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
RESPONSE_FILE = 'response.json'


def load_api_key():
    with open('.env') as f:
        for line in f:
            line = line.strip()
            if line.startswith('GMAPS_API_KEY='):
                return line.split('=', 1)[1]
    raise RuntimeError('GMAPS_API_KEY not found in .env')


def parse_query(q):
    """Same parsing rules as cc: START.DEST.ARR|DEP HHMM"""
    q = q.strip()
    parts = [p.strip() for p in q.split('.')]
    start = parts[0] if len(parts) > 0 else ''
    dest = parts[1] if len(parts) > 1 else ''
    timefield = parts[2].upper() if len(parts) > 2 else ''

    m = re.search(r'(ARR|DEP)\s+(\d{4})', timefield)
    if m:
        type_ = m.group(1)
        time = m.group(2)
    else:
        type_ = 'DEP'
        time = ''

    timestamp = ''
    if time:
        hour, minute = time[:2], time[2:4]
        date = datetime.now().strftime('%Y-%m-%d')
        timestamp = f'{date}T{hour}:{minute}:00+12:00'

    return start, dest, type_, timestamp


def call_routes_api(req_body):
    """POST request.json to Google Routes API, write response.json,
    return the parsed dict. Raises on network failure."""
    api_key = load_api_key()
    result = subprocess.run(
        ['curl', '-s', '--connect-timeout', '5', '--max-time', '10',
         '-X', 'POST', GMAPS_URL,
         '-H', 'Content-Type: application/json',
         '-H', f'X-Goog-Api-Key: {api_key}',
         '-H', 'X-Goog-FieldMask: routes.duration,routes.distanceMeters,routes.legs',
         '-d', json.dumps(req_body)],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        raise RuntimeError('API request failed (timeout or network error)')

    with open(RESPONSE_FILE, 'w') as f:
        f.write(result.stdout)

    data = json.loads(result.stdout)
    if 'routes' not in data:
        raise RuntimeError(f'API returned no routes: {data}')

    return data


@app.route('/')
def form():
    return template('templates/input.tpl')


@app.route('/query', method='POST')
def query():
    q = request.forms.q

    try:
        start, dest, type_, timestamp = parse_query(q)
        req_body = resolve.build_request(start, dest, type_, timestamp)
        response_data = call_routes_api(req_body)
        steps_data = steps_mod.build_steps(response_data, start, dest)
        steps_data['steps'] = result_mod.filter_short_walks(steps_data['steps'])
        return template('templates/result.tpl', **steps_data)
    except Exception as e:
        return template('templates/error.tpl', message=str(e))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
