"""Pull recent eBird sightings for the Bay Area into a compact sightings.json.

Runs in GitHub Actions with EBIRD_KEY set, so the key never reaches the browser.
Usage: python scripts/fetch_sightings.py OUT.json
"""
import json, os, sys, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

BBOX = (-123.05, 37.20, -121.75, 38.20)   # lng/lat: Point Reyes to San Jose
STEP_KM, RADIUS_KM, BACK_DAYS = 7, 5, 14
NOTABLE_CENTERS = [(-122.40, 37.75), (-122.90, 38.02), (-121.95, 37.40)]

def get(path, **params):
    url = "https://api.ebird.org/v2/" + path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"x-ebirdapitoken": os.environ["EBIRD_KEY"]})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as e:
            if attempt == 3:
                print("failed", path, params, e, file=sys.stderr)
                return []
            time.sleep(5 * 2 ** attempt)   # eBird answers 429 when pushed

def grid():
    lng0, lat0, lng1, lat1 = BBOX
    dlat = STEP_KM / 111.0
    dlng = STEP_KM / (111.0 * 0.79)          # cos(37.7°)
    lat = lat0
    while lat <= lat1:
        lng = lng0
        while lng <= lng1:
            yield round(lng, 4), round(lat, 4)
            lng += dlng
        lat += dlat

def main(out):
    pts = list(grid())
    with ThreadPoolExecutor(2) as ex:
        batches = list(ex.map(lambda p: get("data/obs/geo/recent", lat=p[1], lng=p[0], dist=RADIUS_KM, back=BACK_DAYS), pts))
        notable = list(ex.map(lambda p: get("data/obs/geo/recent/notable", lat=p[1], lng=p[0], dist=50, back=BACK_DAYS), NOTABLE_CENTERS))
    species, sp_idx, locs, loc_idx, obs, seen = [], {}, [], {}, [], set()
    notable_keys = {o["speciesCode"] + "|" + o["locId"] for b in notable for o in b}
    for o in (o for b in batches + notable for o in b):
        key = o["speciesCode"] + "|" + o["locId"]
        if key in seen:
            continue
        seen.add(key)
        if o["speciesCode"] not in sp_idx:
            sp_idx[o["speciesCode"]] = len(species)
            species.append([o["speciesCode"], o["comName"], o["sciName"]])
        if o["locId"] not in loc_idx:
            loc_idx[o["locId"]] = len(locs)
            locs.append([o["locId"], o["locName"], round(o["lat"], 5), round(o["lng"], 5)])
        obs.append([sp_idx[o["speciesCode"]], loc_idx[o["locId"]], o["obsDt"], o.get("howMany"), o.get("subId"),
                    1 if key in notable_keys else 0])
    # Taxonomic order and family for each species, so the map can colour pins by bird group.
    for i in range(0, len(species), 100):
        codes = ",".join(sp[0] for sp in species[i:i + 100])
        tax = {t["speciesCode"]: t for t in get("ref/taxonomy/ebird", fmt="json", species=codes)}
        for sp in species[i:i + 100]:
            t = tax.get(sp[0], {})
            sp += [t.get("order", ""), t.get("familyComName", "")]
    data = {"updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "backDays": BACK_DAYS,
            "species": species, "locs": locs, "obs": obs}
    with open(out, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    print(f"{len(pts)} grid calls, {len(obs)} sightings, {len(species)} species, {len(locs)} locations")
    if not obs:
        sys.exit("no sightings fetched; check the EBIRD_KEY secret")

if __name__ == "__main__":
    main(sys.argv[1])
