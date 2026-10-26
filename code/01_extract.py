"""Step 1. Read the realm-domesday reference YAML and write compact place and parish tables.

Usage:
    python3 code/01_extract.py /path/to/realm-domesday

Writes data/domesday_places.csv and data/domesday_parishes.csv.

Allocation rule (the same as the repository's own views/then-and-now.yml): an entry's
figures are attributed to the places it DESCRIBES, shared equally among them when it
describes more than one. Places an entry merely INCLUDES (named dependencies) get nothing
from it. Each place reaches its 2021 parish through the repository's NOW_IN link (a point
test on the centre of its 1 km grid square).
"""
import csv
import glob
import os
import sys
from collections import defaultdict

import re

import yaml

try:
    Loader = yaml.CSafeLoader
except AttributeError:  # pragma: no cover
    Loader = yaml.SafeLoader

REPO = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/hist/realm-domesday"
REF = os.path.join(REPO, "reference")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(OUT, exist_ok=True)

FIG = ["households", "villagers", "smallholders", "slaves", "cottagers", "freemen", "freeMen",
       "burgesses", "ploughTeams", "ploughlands", "mills", "value1066", "value1086", "geldUnits"]


def load(pattern):
    for path in sorted(glob.glob(os.path.join(REF, pattern))):
        with open(path, encoding="utf-8") as f:
            docs = yaml.load(f, Loader=Loader) or []
        for d in docs:
            yield d


# ---- places
places = {}
for d in load("03-places-*.yml"):
    p = d["data"]
    places[p["placeId"]] = {
        "placeId": p["placeId"], "name": p.get("name"), "county": p.get("county"),
        "countyName": p.get("countyName"), "hundred": p.get("hundred"), "gridRef": p.get("gridRef"),
        "lat": p.get("lat"), "lng": p.get("lng"), "inLittleDomesday": p.get("inLittleDomesday"),
        "openDomesdayPath": p.get("openDomesdayPath"), "wikipedia": p.get("wikipedia"),
        "parishCode": p.get("parishCode"), "parishName": p.get("parishName"), "ladName": p.get("ladName"),
        "modernPlaceName": p.get("modernPlaceName"), "modernPlaceDistanceKm": p.get("modernPlaceDistanceKm"),
        "likelyLost": p.get("likelyLost"),
    }
print("places", len(places))

# ---- entries
acc = defaultdict(lambda: defaultdict(float))
has = defaultdict(set)
nentries = defaultdict(int)
maxshare = defaultdict(int)
refs = defaultdict(list)
totalclause = defaultdict(float)
# An entry whose text says "Altogether" or "In total" may carry a total for a whole soke or group of
# members while DESCRIBING only its head (for example Lincolnshire 1,80, Holton le Moor). Such
# households are kept, but flagged, so the league tables can leave them out.
TOTAL = re.compile(r"\b(in total|altogether)\b", re.I)
n_entries = n_with_hh = n_total = 0
kinds = defaultdict(int)
for d in load("05-entries-*.yml"):
    e = d["data"]
    n_entries += 1
    targets = [r["to"]["placeId"] for r in d.get("relations", [])
               if r["predicate"] == "DESCRIBES" and r["to"].get("type") == "DomesdayPlace"]
    if not targets:
        continue
    k = len(targets)
    if e.get("households") is not None:
        n_with_hh += 1
        if TOTAL.search(e.get("text") or ""):
            n_total += 1
            for pid in targets:
                totalclause[pid] += float(e["households"]) / k
    kinds[e.get("kind")] += 1
    for pid in targets:
        nentries[pid] += 1
        maxshare[pid] = max(maxshare[pid], k)
        if e.get("households") is not None:
            refs[pid].append("%s (%g)" % (e.get("ref"), round(float(e["households"]) / k, 2)))
        for f in FIG:
            v = e.get(f)
            if v is None or isinstance(v, bool):
                continue
            acc[pid][f] += float(v) / k
            has[pid].add(f)
print("entries", n_entries, "with households", n_with_hh, "with a total clause", n_total, dict(kinds))

# ---- parishes
parishes = {}
for d in load("00-modern-parishes-*.yml"):
    p = d["data"]
    parishes[p["parishCode"]] = p
print("parishes", len(parishes))

# ---- place table
cols = ["placeId", "name", "county", "countyName", "hundred", "gridRef", "lat", "lng", "inLittleDomesday",
        "entries", "mostPlacesInOneEntry"] + [f + "1086" if f not in ("value1066", "value1086") else f for f in FIG] + [
        "openDomesdayPath", "wikipedia", "parishCode", "parishName", "ladName", "parishDomesdayPlaces",
        "parishResidents2021", "parishHouseholds2021", "parishAreaHa", "modernPlaceName", "modernPlaceDistanceKm",
        "likelyLost", "totalClauseHouseholds1086", "householdEntries"]
rows = []
for pid, p in places.items():
    r = dict(p)
    r["entries"] = nentries.get(pid, 0)
    r["mostPlacesInOneEntry"] = maxshare.get(pid, 0)
    for f in FIG:
        key = f + "1086" if f not in ("value1066", "value1086") else f
        r[key] = round(acc[pid][f], 3) if f in has[pid] else ""
    r["totalClauseHouseholds1086"] = round(totalclause[pid], 3) if pid in totalclause else ""
    r["householdEntries"] = "; ".join(refs.get(pid, []))
    par = parishes.get(p.get("parishCode"))
    r["parishDomesdayPlaces"] = par.get("domesdayPlaces") if par else ""
    r["parishResidents2021"] = par.get("usualResidents2021") if par else ""
    r["parishHouseholds2021"] = par.get("households2021") if par else ""
    r["parishAreaHa"] = par.get("areaHectares") if par else ""
    rows.append(r)
rows.sort(key=lambda r: int(r["placeId"]))
with open(os.path.join(OUT, "domesday_places.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)

# ---- parish table: sum the places in each parish
pp = defaultdict(list)
for r in rows:
    if r["parishCode"]:
        pp[r["parishCode"]].append(r)
pcols = ["parishCode", "parishName", "ladName", "county1086", "countiesMixed", "nPlaces", "nPlacesWithHouseholds",
         "places", "households1086", "villagers1086", "smallholders1086", "slaves1086", "ploughTeams1086", "mills1086",
         "value1086", "totalClauseHouseholds1086", "residents2021", "households2021", "areaHa", "householdsRatio", "lat", "lng"]
prow = []
for code, lst in pp.items():
    par = parishes.get(code, {})
    s = lambda k: round(sum(float(x[k]) for x in lst if x[k] != ""), 3) if any(x[k] != "" for x in lst) else ""
    cnt = defaultdict(int)
    for x in lst:
        cnt[x["countyName"]] += 1
    county = max(cnt, key=cnt.get)
    hh = s("households1086")
    h21 = par.get("households2021")
    lat = [x["lat"] for x in lst if x["lat"] is not None]
    lng = [x["lng"] for x in lst if x["lng"] is not None]
    prow.append({
        "parishCode": code, "parishName": par.get("parishName", lst[0]["parishName"]), "ladName": par.get("ladName", ""),
        "county1086": county, "countiesMixed": len(cnt) > 1, "nPlaces": len(lst),
        "nPlacesWithHouseholds": sum(1 for x in lst if x["households1086"] != ""),
        "places": "; ".join(sorted(x["name"] for x in lst)),
        "households1086": hh, "villagers1086": s("villagers1086"), "smallholders1086": s("smallholders1086"),
        "slaves1086": s("slaves1086"), "ploughTeams1086": s("ploughTeams1086"), "mills1086": s("mills1086"),
        "value1086": s("value1086"), "totalClauseHouseholds1086": s("totalClauseHouseholds1086"), "residents2021": par.get("usualResidents2021", ""), "households2021": h21 or "",
        "areaHa": par.get("areaHectares", ""),
        "householdsRatio": round(h21 / hh, 3) if (hh not in ("", 0) and h21) else "",
        "lat": round(sum(lat) / len(lat), 5) if lat else "", "lng": round(sum(lng) / len(lng), 5) if lng else "",
    })
prow.sort(key=lambda r: r["parishCode"])
with open(os.path.join(OUT, "domesday_parishes.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=pcols)
    w.writeheader()
    w.writerows(prow)
print("place rows", len(rows), "parish rows", len(prow))
