#!/usr/bin/env python3
from bottle import Bottle, request, response, template, static_file
import subprocess, json, re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import resolve
import steps as steps_mod
import result as result_mod

app = Bottle()

GMAPS_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
RESPONSE_FILE = 'response.json'
CONFIG_FILE = 'config'
FAVS_FILE = 'favs'
RECENT_FILE = 'recent.json'
RECENT_MAX = 1
LOCAL_TZ = ZoneInfo('Pacific/Auckland')


def load_api_key():
    with open('.env') as f:
        for line in f:
            line = line.strip()
            if line.startswith('GMAPS_API_KEY='):
                return line.split('=', 1)[1]
    raise RuntimeError('GMAPS_API_KEY not found in .env')


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


def set_config_value(key, value):
    lines = []
    found = False
    with open(CONFIG_FILE) as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith(f'{key}=') and not stripped.startswith('#'):
                lines.append(f'{key}={value}\n')
                found = True
            else:
                lines.append(line)
    if not found:
        lines.append(f'{key}={value}\n')
    with open(CONFIG_FILE, 'w') as f:
        f.writelines(lines)


def load_favs_raw():
    """Load favs as an ordered list of (name, value) for display."""
    favs = []
    with open(FAVS_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            name, _, value = line.partition('=')
            favs.append((name.strip(), value.strip()))
    return favs


def add_fav(name, value):
    name = name.strip().upper()
    with open(FAVS_FILE, 'a') as f:
        f.write(f'{name}={value.strip()}\n')


def delete_fav(name):
    name = name.strip().upper()
    lines = []
    with open(FAVS_FILE) as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith(f'{name}=') and not stripped.startswith('#'):
                continue
            lines.append(line)
    with open(FAVS_FILE, 'w') as f:
        f.writelines(lines)


def parse_query(q):
    """Same parsing rules as cc: START.DEST.ARR|DEP HHMM
    Timestamps are built in Pacific/Auckland (DST-aware). If the
    requested time has already passed today, it rolls to tomorrow."""
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
        now = datetime.now(LOCAL_TZ)
        target = now.replace(hour=int(time[:2]), minute=int(time[2:4]),
                             second=0, microsecond=0)
        if target < now:
            target += timedelta(days=1)
        timestamp = target.isoformat()
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


# ---- recent entries (server-side state for the input form) ----

def load_recent():
    try:
        with open(RECENT_FILE) as f:
            d = json.load(f)
    except (OSError, ValueError):
        d = {}
    return {'start': d.get('start', []),
            'dest': d.get('dest', []),
            'type': d.get('type', 'DEP')}


def save_recent(start, dest, type_):
    d = load_recent()
    for key, val in (('start', start), ('dest', dest)):
        val = val.strip()
        if not val:
            continue
        rest = [x for x in d[key] if x.lower() != val.lower()]
        d[key] = ([val] + rest)[:RECENT_MAX]
    d['type'] = type_
    with open(RECENT_FILE, 'w') as f:
        json.dump(d, f)


def assemble_query():
    """Build 'START.DEST.TYPE HHMM' from the new form fields.
    A filled text box overrides its dropdown."""
    def field(name):
        return request.forms.getunicode(name, '').strip()
    start = field('start_txt') or field('start_sel')
    dest = field('dest_txt') or field('dest_sel')
    type_ = field('type') or 'DEP'
    digits = re.sub(r'\D', '', field('time'))
    if len(digits) == 3:
        digits = '0' + digits
    if digits and len(digits) != 4:
        raise ValueError('Time must be HHMM, e.g. 0930')
    if not start:
        raise ValueError('Start is required.')
    q = f'{start}.{dest}'
    if digits:
        q += f'.{type_} {digits}'
    return q


@app.route('/')
def form():
    rec = load_recent()
    return template('templates/input.tpl',
                    recent_start=rec['start'],
                    recent_dest=rec['dest'],
                    favs=sorted((n for n, _ in load_favs_raw()), key=str.lower),
                    last_type=rec['type'])


@app.route('/classic')
def classic():
    return template('templates/classic.tpl')


@app.route('/preview', method='POST')
def preview():
    """Show the assembled string and request body; no Google call."""
    response.content_type = 'text/plain; charset=utf-8'
    try:
        q = request.forms.q or assemble_query()
        start, dest, type_, timestamp = parse_query(q)
        req_body = resolve.build_request(start, dest, type_, timestamp)
        return (f'q: {q}\nparsed: {(start, dest, type_, timestamp)}\n\n'
                + json.dumps(req_body, indent=2))
    except Exception as e:
        return f'ERROR: {e}'


@app.route('/query', method='POST')
def query():
    q = request.forms.q
    try:
        if not q.strip():
            q = assemble_query()
        start, dest, type_, timestamp = parse_query(q)
        req_body = resolve.build_request(start, dest, type_, timestamp)
        response_data = call_routes_api(req_body)
        steps_data = steps_mod.build_steps(response_data, start, dest)
        steps_data['steps'] = result_mod.filter_short_walks(steps_data['steps'])
        try:
            save_recent(start, dest, type_)
        except Exception:
            pass
        return template('templates/result.tpl', **steps_data)
    except Exception as e:
        return template('templates/error.tpl', message=str(e))


@app.route('/ticket.html')
def ticket_page():
    return static_file('ticket.html', root='static')


@app.route('/ticket.png')
def ticket_image():
    return static_file('ticket.png', root='static')


SWITCH_SERVICES = {
    'mail': 't9amail-web.service',
    'map': 't9amap-web.service',
    'drive': 't9adrive-web.service',
}

RESTART_SCRIPT = '/root/restart'


@app.route('/switch/<name>', method='POST')
def switch(name):
    if name not in SWITCH_SERVICES:
        return "unknown service"
    subprocess.Popen(['systemd-run', '--unit=t9aswitch', RESTART_SCRIPT, name])
    return '<p>Switching... <a href="/">Wait a few seconds: click to reload</a></p>'


@app.route('/admin')
def admin():
    cfg = load_config()
    favs = sorted(load_favs_raw(), key=lambda f: f[0].lower())
    return template('templates/admin.tpl',
                     city=cfg.get('_CITY', ''),
                     country=cfg.get('_COUNTRY', ''),
                     favs=favs)


@app.route('/set_city', method='POST')
def set_city():
    city = request.forms.get('city', '').strip()
    if city:
        set_config_value('_CITY', city)
    return '<p>City updated.</p><p><a href="/admin">back</a></p>'


@app.route('/set_country', method='POST')
def set_country():
    country = request.forms.get('country', '').strip()
    if country:
        set_config_value('_COUNTRY', country)
    return '<p>Country updated.</p><p><a href="/admin">back</a></p>'


@app.route('/add_fav', method='POST')
def add_fav_confirm():
    name = request.forms.get('name', '').strip()
    value = request.forms.get('value', '').strip()
    if not (name and value):
        return template('templates/error', message='Name and value required.')
    return template('templates/add_fav_confirm', name=name, value=value)


@app.route('/add_fav_commit', method='POST')
def add_fav_commit():
    name = request.forms.get('name', '').strip()
    value = request.forms.get('value', '').strip()
    if name and value:
        add_fav(name, value)
    return '<p>Fav added.</p><p><a href="/admin">back</a></p>'


@app.route('/delete_fav', method='POST')
def delete_fav_route():
    name = request.forms.get('name', '').strip()
    if name:
        delete_fav(name)
    return '<p>Fav deleted.</p><p><a href="/admin">back</a></p>'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
