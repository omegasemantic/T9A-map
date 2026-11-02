# T9AMAP

Public transport directions for an HMD 105 (Opera Mini, 2.4" screen, T9 keypad).
Bottle app calling the Google Routes API, served on port 80 by `t9amap-web.service`.
Only one of mail / map / drive holds port 80 at a time (`/root/restart map|mail|drive`).

Status as of 2026-11-03: new input form live; last-entry retention removed from the
page and parked. One week of bench testing on the phone, then review. The VPS (sally)
is the source of truth; develop and test there, because the HMD is the only real test
device.

## Layout

```
map.py              routes, query assembly (also still holds unused recent-entry code)
resolve.py          builds the Routes API request (reads config + favs)
steps.py, result.py parse and filter the API response
templates/          input.tpl (form), classic.tpl (old textarea form),
                    admin.tpl, add_fav_confirm.tpl, result.tpl, error.tpl
static/             ticket.html (service switcher), ticket.png, 3.jpg
config              key=value: _CITY, _COUNTRY, _MODE, _PREF (city/country set from /admin)
favs                NAME=value, one per line (managed from /admin or by hand)
.env                GMAPS_API_KEY (NOT in git; see Git and backups)
recent.json         still written after a successful query, no longer read (gitignored)
restartmap          older helper; prefer /root/restart
```

## How the input page works

- Start and Dest each have a dropdown (favs, sorted) plus a text box. A filled text box
  overrides its dropdown; if it is empty the dropdown is used.
- Then HHMM (optional, blank = now), DEP/ARR radios (default DEP), Submit.
- Plain HTML only: Opera Mini lacks `<datalist>` and reliable JS/localStorage.
- `/query` accepts either `q` (the old `START.DEST.DEP HHMM` string, curl, `/classic`)
  or the new fields; it assembles the string and passes it to the unchanged `parse_query`.
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
  Considered and parked: filter by city text in the value; `CITY:NAME` prefixes (breaks
  typed shortcuts such as `CENT`).
- The input page does not show the current city; a stale `_CITY` is the main risk for
  typed addresses.
- /admin writes `config` and `favs`, so `git status` shows them modified after edits.

## Retention (parked)

- Tried: server-side `recent.json` feeding a preselected Recent entry and last DEP/ARR.
  Code is in commit 018fc3a.
- Symptom on the phone: the screen showed one string but the query sent was an earlier,
  no-longer-visible one, with different errors each time. Suspected cause is Opera Mini
  serving a cached page or restoring old form state (not confirmed). The server reads
  `recent.json` fresh each time and cannot cause a screen/query mismatch by itself.
- Removed from the page by editing `templates/input.tpl` only. `map.py` still has
  `load_recent` / `save_recent`, unused.
- If a wrong query ever appears again, suspect stale text restored into a text box (a
  filled box overrides its dropdown).
- Next time: log the received string first (temporary `print(q)` in `/query`, read with
  `journalctl -u t9amap-web`) and compare it with what the screen showed. Cheap
  insurance to try: `autocomplete="off"` on the form and `Cache-Control: no-store` on `/`.
  Then rebuild retention in small steps.

## Edit cycle (on sally)

```
cd ~/T9A/map
cp map.py map.py.prev                       # backups are gitignored (*.prev*)
vim map.py templates/input.tpl
/root/.venvs/map/bin/python3 -m py_compile map.py && /root/restart map
curl -s -o /dev/null -w '%{http_code}\n' localhost/
```

- Restart after every edit, templates included.
- `/root/restart` does NOT syntax-check. Always py_compile first, and run commands in the
  shell, never paste them into a file.
- Check favs resolution without an API call:

```
for f in CENT VIC; do printf '%s: ' "$f"
  curl -s --data-urlencode "start_sel=$f" -d type=DEP localhost/preview | grep -m1 '"address"'
done
```

## Troubleshooting

- 503 from the phone: the app is not listening on port 80 (crash loop).

```
journalctl -u t9amap-web.service -n 30 --no-pager      # find the traceback
ss -ltnp | grep ':80 '                                 # who holds port 80
```

  Fix the cause (or `git checkout -- map.py`), then `/root/restart map`, which also
  clears systemd's "repeated too quickly" failure state.
- Back to a known-good version: `git log --oneline`, `git checkout <commit> -- .`,
  `/root/restart map`. Before git, `~/T9A/map.pre-input` holds the pre-redesign state.

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

## Open items

- Bench test for a week; note anything odd (wrong place resolved, stale fields, errors).
- Real-query check for the trickiest favs (`VIC`, `EDGE`, `BASE`).
- Afterwards: remove the unused recent code from map.py, or rebuild retention (see above).
- Delete `~/T9A/map.pre-input` and the `*.presort` / `*.prefilter` / `*.prefavs` /
  `*.prev*` backup files once happy.
- Same git pattern for `drive` and `mail`.
- Possible: show current city on the input page; show fav values in the admin table.
- `app.run(port=80)` is hard-coded, so running locally needs root or a code change.
