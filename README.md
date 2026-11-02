# T9AMAP

Public transport directions for an HMD 105 (Opera Mini, 2.4" screen, T9 keypad).
Bottle app calling the Google Routes API, served on port 80 by `t9amap-web.service`.
Only one of mail / map / drive holds port 80 at a time (`/root/restart map|mail|drive`).

Status as of 2026-11-03: input form redesign done and pushed. The VPS (sally) is the
source of truth. Develop and test there, because the HMD is the only real test device.

## Layout

```
map.py              routes, query assembly, recent entries
resolve.py          builds the Routes API request (reads config + favs)
steps.py, result.py parse and filter the API response
templates/          input.tpl (new form), classic.tpl (old textarea form),
                    admin.tpl, add_fav_confirm.tpl, result.tpl, error.tpl
static/             ticket.html (service switcher), ticket.png, 3.jpg
config              key=value: _CITY, _COUNTRY (set from /admin)
favs                NAME=value, one per line (managed from /admin or by hand)
.env                GMAPS_API_KEY (NOT in git; see Backups)
recent.json         last start/dest/type (runtime state, gitignored)
```

## How the input page works

- Start and Dest each have a dropdown plus a text box. A filled text box overrides
  its dropdown; if it is empty the dropdown is used.
- Dropdown = last-used entry (preselected), then Favs, sorted. One recent entry only
  (`RECENT_MAX = 1` in map.py).
- Then HHMM (optional, blank = now) and DEP/ARR radios (default = last used), Submit.
- Plain HTML only: Opera Mini lacks `<datalist>` and reliable JS/localStorage.
- Recent entries are saved only after a successful query (`recent.json`).
- `/query` accepts either `q` (the old `START.DEST.DEP HHMM` string, curl) or the new
  fields; it assembles the string and passes it to the unchanged `parse_query`.
- `/classic` is the old textarea form, kept as a fallback.
- `/preview` (POST) shows the assembled string, parsed values and request body with no
  Google call:

```
curl -s --data-urlencode 'start_sel=HOME' --data-urlencode 'dest_txt=12 Smith St' \
  -d type=DEP -d time=1100 localhost/preview
```

- Do not type a dot (`.`) in names or addresses; it is the field separator.

## City and favs (important)

- Typed addresses get `, {_CITY}, {_COUNTRY}` appended, so `12 Smith St` is searched in
  the city set on /admin.
- Fav values that are addresses get the COUNTRY ONLY. Every address fav must include its
  own city: `VIC=1240 Victoria Street, Hamilton`. Use the string that works in Chrome Maps.
- `ChIJ...` place IDs and `lat,lng` pairs need no city and are the most precise.
- No quotes in fav values. Names are uppercased on add.
- Favs from several cities are mixed in the dropdown (no city filtering, by decision).
  Ideas considered and parked: filter by city text in the value; `CITY:NAME` prefixes
  (breaks typed shortcuts such as `CENT`).
- The input page does not show the current city; a stale `_CITY` is the main risk for
  typed addresses.
- /admin writes `config` and `favs`, so `git status` will show them modified after edits.

## Edit cycle (on sally)

```
cd ~/T9A/map
cp map.py map.py.prev                       # backups are gitignored (*.prev*)
vim map.py templates/input.tpl
/root/.venvs/map/bin/python3 -m py_compile map.py && /root/restart map
curl -s -o /dev/null -w '%{http_code}\n' localhost/
```

Restart after every edit, templates included. A syntax error caught by py_compile
leaves the running app untouched. Check favs resolution without an API call:

```
for f in CENT VIC; do printf '%s: ' "$f"
  curl -s --data-urlencode "start_sel=$f" -d type=DEP localhost/preview | grep -m1 '"address"'
done
```

## Git and backups

- Remote: `git@github.com:omegasemantic/T9A-map.git` (private). Commit and push from sally.
- Gitignored: `.env`, `recent.json`, `request.json`, `response.json`, `steps.json`,
  `venv/`, `__pycache__/`, `*.bak`, `*.presort`, `*.prefilter`, `*.prefavs`, `*.prev*`.
- `config` and `favs` are tracked (private repo).
- `.env` is NOT in git. Keep its values in a password manager. `.env.example` shows the
  format. The Google API key can be viewed or rotated in Cloud Console; a Gmail app
  password is shown once and must be regenerated if lost.
- Full copy including `.env` and live state, from the Crostini machine:

```
rsync -av --exclude=venv --exclude=__pycache__ sally:T9A/ ~/posix/T9A/
```

- Revert code: `git log --oneline`, then `git checkout <commit> -- .` and
  `/root/restart map`. Before git, `~/T9A/map.pre-input` holds the pre-redesign state.

## Open items

- Real-query check on the phone for the trickiest favs (`VIC`, `EDGE`, `BASE`) and that
  last start/dest come back preselected.
- Delete `map.pre-input` and the `*.presort` / `*.prefilter` / `*.prefavs` / `*.prev*`
  backup files once happy.
- Same git pattern for `drive` and `mail`.
- Possible: show current city on the input page; show fav values in the admin table.
- `app.run(port=80)` is hard-coded, so running locally needs root or a code change.
