"""Step 2. The persistence test. Reads data/domesday_places.csv and data/domesday_parishes.csv,
writes data/results.json (every number quoted on the page) and _site_data.json (what the
page draws; a temporary file that 03_build_page.py embeds in index.html and then deletes).

Usage:
    python3 code/02_analyse.py
"""
import json
import os

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data")
P = pd.read_csv(os.path.join(D, "domesday_places.csv"), dtype={"placeId": str})
Q = pd.read_csv(os.path.join(D, "domesday_parishes.csv"))

MIN_FALL = 20     # fewest 1086 households for the fallen giants and the ratio league tables
MIN_RATIO = 10    # fewest 1086 households for a parish to be ranked as a riser
TINY = 5          # "Domesday nobody": a parish whose places had at most this many households in 1086

R = {}


def rnd(x, d=3):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), d)


def corr(df, x, y):
    lx, ly = np.log10(df[x]), np.log10(df[y])
    r, _ = stats.pearsonr(lx, ly)
    rho, _ = stats.spearmanr(df[x], df[y])
    b, a = np.polyfit(lx, ly, 1)
    return {"n": int(len(df)), "pearson_log": rnd(r), "r2_log": rnd(r * r), "spearman": rnd(rho),
            "slope": rnd(b), "intercept": rnd(a)}


# ---------------------------------------------------------------- coverage
located = P[P.lat.notna()]
R["places_total"] = int(len(P))
R["places_located"] = int(len(located))
R["places_with_households"] = int((P.households1086 > 0).sum())
R["households_1086_total"] = rnd(P.households1086.sum(), 0)
R["entries_note"] = "figures from entries that DESCRIBE a place, shared equally when an entry describes several"
R["places_shared_entry"] = int((P.mostPlacesInOneEntry > 1).sum())
Q["unparished"] = Q.parishName.str.contains("unparished area", regex=False)
R["parishes_total"] = int(len(Q))
R["parishes_unparished"] = int(Q.unparished.sum())
R["unparished_households1086"] = rnd(Q.loc[Q.unparished, "households1086"].sum(), 0)
R["unparished_share_households1086"] = rnd(Q.loc[Q.unparished, "households1086"].sum() / Q.households1086.sum())
R["unparished_examples"] = Q.loc[Q.unparished].sort_values("households1086", ascending=False).head(8)[
    ["parishName", "households1086"]].assign(households1086=lambda d: d.households1086.round(0)).to_dict("records")
R["years"] = 2021 - 1086
R["yorkshire_places"] = int((P.countyName == "Yorkshire").sum())
R["yorkshire_with_households"] = int(((P.countyName == "Yorkshire") & (P.households1086 > 0)).sum())
# Quoted from the realm-domesday README ("How good is it?"), not computed here.
R["repo_checks"] = {"source": "realm-domesday README.md", "parish_agrees_wikidata": 0.90, "manors_checked": 450,
                    "villagers_agreement": 0.987, "smallholders_agreement": 0.989}
R["places_no_parish"] = int(P.parishCode.isna().sum())

# ---------------------------------------------------------------- lost places
L = located.copy()
L["lost"] = L.likelyLost.astype(str).str.lower() == "true"
R["lost_n"] = int(L.lost.sum())
R["lost_share"] = rnd(L.lost.mean())
R["lost_with_households"] = int((L.lost & (L.households1086 > 0)).sum())
R["lost_households1086"] = rnd(L.loc[L.lost, "households1086"].sum(), 0)
R["lost_households_share"] = rnd(L.loc[L.lost, "households1086"].sum() / L.households1086.sum())
R["lost_hh_median"] = rnd(L.loc[L.lost & (L.households1086 > 0), "households1086"].median(), 1)
R["notlost_hh_median"] = rnd(L.loc[~L.lost & (L.households1086 > 0), "households1086"].median(), 1)
lc = L.groupby("countyName").agg(n=("lost", "size"), lost=("lost", "sum")).reset_index()
lc["share"] = lc.lost / lc.n
lc = lc.sort_values("share", ascending=False)
R["lost_by_county"] = [{"county": r.countyName, "n": int(r.n), "lost": int(r.lost), "share": rnd(r.share)}
                       for r in lc.itertuples()]
big_lost = L[L.lost].sort_values("households1086", ascending=False).head(12)
R["lost_biggest"] = [{"name": r.name, "county": r.countyName, "households1086": rnd(r.households1086, 1),
                      "nearest": r.modernPlaceName, "km": rnd(r.modernPlaceDistanceKm, 2), "parish": r.parishName,
                      "path": r.openDomesdayPath, "totalClause": bool(r.totalClauseHouseholds1086 > 0)} for r in big_lost.itertuples()]

# Parishes where more than half the 1086 households come from entries with an "Altogether"/"In total"
# clause (possible soke totals) are kept in the correlations but left out of the league tables.
Q["totalShare"] = (Q.totalClauseHouseholds1086.fillna(0) / Q.households1086).fillna(0)
Q["flagTotal"] = Q.totalShare > 0.5
R["total_clause_households1086"] = rnd(P.totalClauseHouseholds1086.sum(), 0)
R["total_clause_places"] = int((P.totalClauseHouseholds1086 > 0).sum())

# ---------------------------------------------------------------- parish level, the main test
base = Q[(Q.households1086 > 0) & (Q.households2021 > 0) & ~Q.unparished].copy()
R["parish_main"] = corr(base, "households1086", "households2021")
R["parish_main_residents"] = corr(base[base.residents2021 > 0], "households1086", "residents2021")
complete = base[base.nPlacesWithHouseholds == base.nPlaces]
R["parish_complete"] = corr(complete, "households1086", "households2021")
noy = base[base.county1086 != "Yorkshire"]
R["parish_no_yorkshire"] = corr(noy, "households1086", "households2021")
R["parish_no_total_clause"] = corr(base[base.totalClauseHouseholds1086.isna()], "households1086", "households2021")
ge5 = base[base.households1086 >= 5]
R["parish_min5"] = corr(ge5, "households1086", "households2021")
R["parish_tenfold"] = rnd(10 ** R["parish_main"]["slope"], 2)
R["parish_median_ratio"] = rnd(base.householdsRatio.median(), 2)
R["parish_ratio_q25"] = rnd(base.householdsRatio.quantile(.25), 2)
R["parish_ratio_q75"] = rnd(base.householdsRatio.quantile(.75), 2)
R["parish_fewer_now"] = int((base.householdsRatio < 1).sum())
R["parish_fewer_now_share"] = rnd((base.householdsRatio < 1).mean())
R["parish_households1086_median"] = rnd(base.households1086.median(), 1)
R["parish_households2021_median"] = rnd(base.households2021.median(), 0)
R["parish_main_households1086_sum"] = rnd(base.households1086.sum(), 0)

# Rank persistence: how many of the biggest tenth in 1086 are in the biggest tenth now?
top86 = base.households1086 >= base.households1086.quantile(.9)
top21 = base.households2021 >= base.households2021.quantile(.9)
R["top10_n"] = int(top86.sum())
R["top10_still_top10"] = int((top86 & top21).sum())
R["top10_still_share"] = rnd((top86 & top21).sum() / top86.sum())
bot86 = base.households1086 <= base.households1086.quantile(.1)
R["bottom10_n"] = int(bot86.sum())
R["bottom10_now_top10"] = int((bot86 & top21).sum())
R["bottom10_now_top10_share"] = rnd((bot86 & top21).sum() / bot86.sum())
# By size quintile of 1086 households: median households now
base["q86"] = pd.qcut(base.households1086.rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
qs = base.groupby("q86", observed=True).agg(lo=("households1086", "min"), hi=("households1086", "max"),
                                            med86=("households1086", "median"),
                                            med21=("households2021", "median"),
                                            ratio=("householdsRatio", "median"), n=("households1086", "size"))
R["quintiles"] = [{"q": int(i), "n": int(r.n), "lo": rnd(r.lo, 1), "hi": rnd(r.hi, 1), "median1086": rnd(r.med86, 1),
                   "median2021": rnd(r.med21, 0), "median_ratio": rnd(r.ratio, 2)} for i, r in qs.iterrows()]

# ---------------------------------------------------------------- place level (a place alone in its parish)
pl = P[(P.parishDomesdayPlaces == 1) & (P.households1086 > 0) & (P.parishHouseholds2021 > 0)].copy()
R["place_alone"] = corr(pl, "households1086", "parishHouseholds2021")

# ---------------------------------------------------------------- does wealth add anything?
m = base[(base.value1086 > 0) & (base.ploughTeams1086 > 0)].copy()
m["lh21"] = np.log10(m.households2021)
m["lh86"] = np.log10(m.households1086)
m["lvph"] = np.log10(m.value1086 / m.households1086)
m["lpph"] = np.log10(m.ploughTeams1086 / m.households1086)
m["mill"] = (m.mills1086.fillna(0) > 0).astype(int)
m["lslaves"] = m.slaves1086.fillna(0) / m.households1086
m["larea"] = np.log10(m.areaHa)
fits = {}
for k, f in {"households": "lh21 ~ lh86",
             "plus_wealth": "lh21 ~ lh86 + lvph + lpph + mill",
             "plus_county": "lh21 ~ lh86 + lvph + lpph + mill + C(county1086)",
             "county_only": "lh21 ~ C(county1086)",
             "households_county": "lh21 ~ lh86 + C(county1086)",
             "plus_area": "lh21 ~ lh86 + lvph + lpph + mill + larea"}.items():
    res = smf.ols(f, data=m).fit(cov_type="HC1")
    fits[k] = {"n": int(res.nobs), "r2": rnd(res.rsquared), "coef": {c: rnd(res.params[c]) for c in
               ["lh86", "lvph", "lpph", "mill", "larea"] if c in res.params},
               "p": {c: rnd(res.pvalues[c], 4) for c in ["lh86", "lvph", "lpph", "mill", "larea"] if c in res.params}}
R["models"] = fits
R["models_note"] = "OLS on log10 2021 households, HC1 robust SEs; value per household in pence; plough teams per household; mill = any mill recorded"
# value alone vs households alone (Spearman with 2021 households)
R["spearman_value1086"] = rnd(stats.spearmanr(m.value1086, m.households2021)[0])
R["spearman_ploughteams"] = rnd(stats.spearmanr(m.ploughTeams1086, m.households2021)[0])
R["spearman_households_same_sample"] = rnd(stats.spearmanr(m.households1086, m.households2021)[0])
R["median_ratio_mill"] = rnd(m.loc[m.mill == 1, "householdsRatio"].median(), 2)
R["median_ratio_nomill"] = rnd(m.loc[m.mill == 0, "householdsRatio"].median(), 2)

# ---------------------------------------------------------------- by county
cty = []
for c, g in base.groupby("county1086"):
    if len(g) < 20:
        continue
    cc = corr(g, "households1086", "households2021")
    cty.append({"county": c, "n": cc["n"], "pearson_log": cc["pearson_log"], "spearman": cc["spearman"],
                "slope": cc["slope"], "median_ratio": rnd(g.householdsRatio.median(), 2),
                "fewer_now_share": rnd((g.householdsRatio < 1).mean()),
                "households1086": rnd(g.households1086.sum(), 0), "households2021": rnd(g.households2021.sum(), 0)})
cty.sort(key=lambda r: -r["spearman"])
R["by_county"] = cty
R["county_spearman_max"] = cty[0]
R["county_spearman_min"] = cty[-1]
R["counties_n"] = len(cty)
R["counties_spearman_over_04"] = sum(1 for r in cty if r["spearman"] >= 0.4)
R["counties_spearman_under_02"] = sum(1 for r in cty if r["spearman"] < 0.2)
# County aggregate (parished areas only): 1086 households vs 2021 households
agg = base.groupby("county1086").agg(h86=("households1086", "sum"), h21=("households2021", "sum")).reset_index()
r, _ = stats.pearsonr(np.log10(agg.h86), np.log10(agg.h21))
R["county_aggregate"] = {"n": int(len(agg)), "pearson_log": rnd(r),
                         "spearman": rnd(stats.spearmanr(agg.h86, agg.h21)[0])}

# ---------------------------------------------------------------- league tables
def prow(r):
    return {"parish": r.parishName, "district": r.ladName, "county": r.county1086, "places": r.places,
            "nPlaces": int(r.nPlaces), "households1086": rnd(r.households1086, 1),
            "households2021": int(r.households2021), "residents2021": int(r.residents2021) if r.residents2021 == r.residents2021 else None,
            "ratio": rnd(r.householdsRatio, 2)}


R["league_flag_excluded"] = int((base.flagTotal & (base.households1086 >= MIN_RATIO)).sum())
league = base[~base.flagTotal]
fall = league[league.households1086 >= MIN_FALL].sort_values("householdsRatio").head(20)
R["fallers"] = [prow(r) for r in fall.itertuples()]
R["fallers_n_eligible"] = int((base.households1086 >= MIN_FALL).sum())
R["fallers_fewer_now"] = int(((base.households1086 >= MIN_FALL) & (base.householdsRatio < 1)).sum())
fn = base[(base.households1086 >= MIN_FALL) & (base.householdsRatio < 1)].county1086.value_counts()
R["fallers_fewer_now_by_county"] = [{"county": c, "n": int(v)} for c, v in fn.items()]
rise = league[league.households1086 >= MIN_RATIO].sort_values("householdsRatio", ascending=False).head(20)
R["risers"] = [prow(r) for r in rise.itertuples()]
nob = league[league.households1086 <= TINY].sort_values("households2021", ascending=False).head(15)
R["nobodies"] = [prow(r) for r in nob.itertuples()]
R["nobodies_n_tiny"] = int((base.households1086 <= TINY).sum())
# Parishes whose Domesday places have no household figure at all, biggest today
nohh = Q[(Q.households1086.isna() | (Q.households1086 == 0)) & (Q.households2021 > 0) & ~Q.unparished]
R["nohh_parishes"] = int(len(nohh))
R["nohh_biggest"] = [{"parish": r.parishName, "district": r.ladName, "places": r.places,
                      "households2021": int(r.households2021)} for r in
                     nohh.sort_values("households2021", ascending=False).head(8).itertuples()]
# biggest parishes of 1086 (parished)
R["biggest1086"] = [prow(r) | {"flagTotal": bool(r.flagTotal)} for r in base.sort_values("households1086", ascending=False).head(12).itertuples()]
R["thresholds"] = {"min_fall": MIN_FALL, "min_ratio": MIN_RATIO, "tiny": TINY}

# Named checks used in the text
def place(name, county=None):
    x = P[P.name == name]
    if county:
        x = x[x.countyName == county]
    r = x.iloc[0]
    return {"name": r["name"], "county": r.countyName, "households1086": rnd(r.households1086, 1),
            "parish": r.parishName, "parishHouseholds2021": rnd(r.parishHouseholds2021, 0),
            "parishResidents2021": rnd(r.parishResidents2021, 0), "parishPlaces": rnd(r.parishDomesdayPlaces, 0),
            "entries": r.householdEntries}


R["example_waddingworth"] = place("Waddingworth", "Lincolnshire")
R["example_abberley"] = place("Abberley", "Worcestershire")
R["example_norwich"] = place("Norwich", "Norfolk")

with open(os.path.join(D, "results.json"), "w") as f:
    json.dump(R, f, indent=1, ensure_ascii=False)

# ---------------------------------------------------------------- site data (compact)
par_idx = {}
parishes = []
for r in Q.itertuples():
    par_idx[r.parishCode] = len(parishes)
    ok = (r.households1086 == r.households1086 and r.households1086 > 0 and r.households2021 == r.households2021
          and r.households2021 > 0 and not r.unparished)
    parishes.append([r.parishName, r.ladName,
                     int(r.residents2021) if r.residents2021 == r.residents2021 else None,
                     int(r.households2021) if r.households2021 == r.households2021 else None,
                     rnd(r.households1086, 1) if r.households1086 == r.households1086 else None,
                     rnd(r.householdsRatio, 2) if ok else None, int(r.nPlaces)])
counties = sorted(P.countyName.dropna().unique())
cidx = {c: i for i, c in enumerate(counties)}


def num(v, d=1):
    return None if v != v or v == "" else (int(v) if float(v).is_integer() else round(float(v), d))


pts = []
for r in located.itertuples():
    pts.append([round(r.lat, 4), round(r.lng, 4), r.name, cidx[r.countyName], num(r.households1086),
                num(r.villagers1086), num(r.smallholders1086), num(r.slaves1086), num(r.ploughTeams1086),
                num(r.mills1086), num(r.value1086, 0), par_idx.get(r.parishCode, -1),
                1 if str(r.likelyLost).lower() == "true" else 0, r.openDomesdayPath if r.openDomesdayPath == r.openDomesdayPath else "",
                int(r.mostPlacesInOneEntry), 1 if r.totalClauseHouseholds1086 > 0 else 0])
# scatter: parish points (log values)
sc = [[rnd(r.households1086, 1), int(r.households2021), r.parishName, r.county1086] for r in base.itertuples()]
site = {"counties": counties, "parishes": parishes, "places": pts, "scatter": sc}
with open(os.path.join(ROOT, "_site_data.json"), "w") as f:  # temporary; embedded and removed by 03_build_page.py
    json.dump(site, f, separators=(",", ":"), ensure_ascii=False)
print(json.dumps({k: R[k] for k in ["parish_main", "parish_complete", "parish_no_yorkshire", "parish_min5",
                                    "place_alone", "parish_main_residents", "county_aggregate"]}, indent=1))
