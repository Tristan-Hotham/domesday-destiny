import json, os
import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches
from matplotlib import font_manager as fm

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, '..', 'data')
# Natural Earth 10m land clipped to the British Isles (prepared for the lighthouse project)
COAST = os.path.join(HERE, '..', '..', 'did-lighthouses-work', 'release', 'build', 'ne10m_land_british_isles.json')
F = '/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts/'
for f in ['FrauncesVar.ttf', 'IBMPlexMono-Regular.ttf', 'IBMPlexMono-Medium.ttf', 'SourceSerif4-Regular.ttf', 'SourceSerif4-Semibold.ttf', 'SourceSerif4-It.ttf']:
    fm.fontManager.addfont(F + f)
DISP = fm.FontProperties(fname=F + 'FrauncesVar.ttf', weight=900)
SER = 'Source Serif 4'; MONO = 'IBM Plex Mono'

BG = '#F1E4C8'; FG = '#1D1A15'; MUT = '#65573F'; LAND = '#E6D3AE'; RULE = '#CDB991'
G = ['#9B3018', '#D9733F', '#DB9461', '#8DB2CF', '#3F7DB8', '#1D4B80']
GN = '#A89A7C'; HOT = '#C2410C'; BLUE = '#1D4B80'
BINS = [0, 1, 3, 10, 30, 100, np.inf]
BLAB = ['fewer households now', '1 to 3 times', '3 to 10 times', '10 to 30 times', '30 to 100 times', 'over 100 times']

R = json.load(open(os.path.join(D, 'results.json')))
Q = pd.read_csv(os.path.join(D, 'domesday_parishes.csv'))
P = pd.read_csv(os.path.join(D, 'domesday_places.csv'), dtype={'placeId': str})
Q['unparished'] = Q.parishName.str.contains('unparished area', regex=False)
base = Q[(Q.households1086 > 0) & (Q.households2021 > 0) & ~Q.unparished]
ratio = base.set_index('parishCode').householdsRatio
L = P[P.lat.notna()].copy()
L['ratio'] = L.parishCode.map(ratio.round(2))
L['bin'] = pd.cut(L.ratio, BINS, right=False, labels=False)
K = np.cos(np.radians(52.5))
L['x'] = L.lng * K
L['hh'] = L.households1086.fillna(0)


def stack_blocks(fig, x, ytop, ybot, blocks, size, inner=0.007):
    """Place big-number blocks top to bottom with equal measured gaps between ytop and ybot."""
    r = fig.canvas.get_renderer(); H = fig.bbox.height
    items = []
    for big, c, small in blocks:
        tb = fig.text(x, 0.5, big, fontproperties=DISP, fontsize=size, color=c, va='top')
        ts = fig.text(x, 0.5, small, family=SER, fontsize=12, color=FG, va='top', linespacing=1.3)
        items.append((tb, ts, tb.get_window_extent(r).height / H, ts.get_window_extent(r).height / H))
    total = sum(hb + inner + hs for _, _, hb, hs in items)
    gap = (ytop - ybot - total) / (len(items) - 1)
    y = ytop
    for tb, ts, hb, hs in items:
        tb.set_y(y); ts.set_y(y - hb - inner); y -= hb + inner + hs + gap
    return gap

CLEAR = 40 / 3000  # at least 40 px between the subtitle block and the right column

fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)
fig.text(0.04, 0.968, 'Is Domesday destiny?', fontproperties=DISP, fontsize=50, color=FG, va='top')
dek = fig.text(0.04, 0.915, 'In 1086 the king\'s commissioners counted England\'s households, village by village.\n'
         'I set all %s Domesday places against the 2021 census, parish by parish, %d years on.'
         % (format(R['places_total'], ','), R['years']),
         family=SER, fontsize=15, color=FG, va='top', linespacing=1.4)
DEKB = dek.get_window_extent(fig.canvas.get_renderer()).y0 / fig.bbox.height
HDR = DEKB - CLEAR

# ---------------- hero map
ax = fig.add_axes([0.012, 0.305, 0.62, 0.562], facecolor=BG)
ax.set_aspect('equal'); ax.axis('off')
ax.set_xlim(-6.0 * K, 1.85 * K); ax.set_ylim(49.9, 55.0)
for g in json.load(open(COAST)):
    polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    for p in polys:
        ring = np.array(p[0])
        if ring[:, 1].min() < 49.6 and ring[:, 0].max() > 1.0:
            continue
        ax.fill(ring[:, 0] * K, ring[:, 1], color=LAND, lw=0, zorder=0)
sz = lambda h: 1.5 + (h.clip(0, 400) ** 0.75) * 0.75
grey = L[L.bin.isna()]
ax.scatter(grey.x, grey.lat, s=sz(grey.hh), c=GN, alpha=0.6, lw=0, zorder=1, rasterized=True)
col = L[L.bin.notna()].sort_values('hh', ascending=False)
ax.scatter(col.x, col.lat, s=sz(col.hh), c=[G[int(b)] for b in col.bin], alpha=0.88, lw=0.2, edgecolors=BG, zorder=2, rasterized=True)

def lab(txt, lon, lat, tlon, tlat, ha='left'):
    ax.annotate(txt, xy=(lon * K, lat), xytext=(tlon * K, tlat), family=SER, style='italic', fontsize=11.5, color=FG, ha=ha,
                va='center', arrowprops=dict(arrowstyle='-', color=FG, lw=0.7), zorder=5)
w = Q[Q.parishName == 'Waddingworth'].iloc[0]
m = Q[Q.parishName == 'Macclesfield'].iloc[0]
b = Q[Q.parishName == 'Bracknell'].iloc[0]
lab('Waddingworth', w.lng, w.lat, 0.45, 53.95)
lab('Macclesfield', m.lng, m.lat, -4.0, 52.55, ha='center')
lab('Bracknell', b.lng, b.lat, -1.5, 50.4, ha='center')
lab('London: no parish\ncensus figures', -0.12, 51.5, 0.75, 50.45, ha='center')

# legend in the empty north-west
n = col.bin.value_counts().reindex(range(6)).fillna(0).astype(int)
lx = fig.add_axes([0.03, 0.645, 0.25, 0.20]); lx.axis('off'); lx.set_xlim(0, 1); lx.set_ylim(0, 1)
lx.text(0, 1.0, 'HOUSEHOLDS 2021 v 1086', family=MONO, fontsize=11, color=FG, va='top')
lx.text(0, 0.89, 'growth of each place\'s modern parish', family=SER, fontsize=11, color=MUT, va='top')
for i in range(6):
    y = 0.72 - i * 0.105
    lx.scatter([0.03], [y], s=80, c=G[i], lw=0)
    lx.text(0.08, y, '%s  %s' % (BLAB[i], format(n[i], ',')), family=MONO, fontsize=10.5, color=FG, va='center')
y = 0.72 - 6 * 0.105
lx.scatter([0.03], [y], s=80, c=GN, lw=0)
lx.text(0.08, y, 'no comparison  %s' % format(len(grey), ','), family=MONO, fontsize=10.5, color=FG, va='center')
lx.text(0, y - 0.13, 'Dot size: households in 1086', family=SER, fontsize=11, color=MUT, va='top')

fig.text(0.04, 0.318, 'Grey: no 2021 parish figure, mostly big unparished towns and cities (%d areas, %.1f%% of 1086\nhouseholds). '
         'London and Winchester are not in Domesday; much of the far north was not surveyed.'
         % (R['parishes_unparished'], R['unparished_share_households1086'] * 100),
         family=SER, style='italic', fontsize=10.5, color=MUT, va='top', linespacing=1.35)

# ---------------- right column numbers
X0 = 0.64
pm = R['parish_main']
nums = [('%.2f' % pm['spearman'], HOT, 'rank correlation between parish size in\n1086 and 2021, across %s parishes.\n1 would mean the same order at both dates.' % format(pm['n'], ',')),
        ('%.1f%%' % (R['top10_still_share'] * 100), FG, 'of the biggest tenth of parishes in 1086\nare still in the biggest tenth today\n(%d of %d). Chance alone: about 10%%.' % (R['top10_still_n'] if 'top10_still_n' in R else R['top10_still_top10'], R['top10_n'])),
        ('%.1f times' % R['parish_median_ratio'], BLUE, 'the households of the typical parish now,\nagainst 1086. Only %d parishes (%.1f%%)\nhave fewer than Domesday counted.' % (R['parish_fewer_now'], R['parish_fewer_now_share'] * 100)),
        ('%.0f%%' % (pm['r2_log'] * 100), FG, 'of the variation in size today explained\nby size in 1086 (log scales). Ten times\nbigger then is about %.0f times bigger now.' % R['parish_tenfold'])]
stack_blocks(fig, X0, HDR, 0.34, nums, 34)

# ---------------- bottom row: slope chart of giants and nobodies
fig.text(0.04, 0.262, 'FALLEN GIANTS AND DOMESDAY NOBODIES', family=MONO, fontsize=11, color=MUT)
sa = fig.add_axes([0.19, 0.105, 0.23, 0.135], facecolor=BG)
sa.set_yscale('log'); sa.set_ylim(2.5, 60000); sa.set_xlim(0, 1)
sa.axis('off')
for x, t in ((0, 'households 1086'), (1, '2021')):
    sa.plot([x, x], [2.5, 60000], color=RULE, lw=1, zorder=0)
    sa.text(x, 70000, t, family=MONO, fontsize=11, color=FG, ha='center', va='bottom')
rows = [('Thetford', '#7A7262', 0, 0.42), ('Waddingworth', G[0], 0, 0), ('Bracknell', G[5], 0, 1.9), ('Macclesfield', G[4], 0, 0.75)]
for nm, c_, dl, dr in rows:
    r = Q[Q.parishName == nm].sort_values('households1086').iloc[-1]
    a0, a1 = r.households1086, r.households2021
    sa.plot([0, 1], [a0, a1], color=c_, lw=2.6, solid_capstyle='round')
    sa.scatter([0, 1], [a0, a1], s=40, c=c_, zorder=3, lw=0)
    sa.text(-0.06, a0, '%s  %s' % (nm, format(int(round(a0)), ',')), family=MONO, fontsize=10.5, color=FG, ha='right', va='center')
    sa.text(1.06, a1 * (dr if dr else 1), '%s  %s' % (format(int(a1), ','), nm), family=MONO, fontsize=10.5, color=c_ if nm != 'Thetford' else FG, ha='left', va='center')

# quintile chart
fig.text(0.68, 0.262, 'THE SMALL GREW FASTEST', family=MONO, fontsize=11, color=MUT)
qa = fig.add_axes([0.70, 0.115, 0.27, 0.095], facecolor=BG)
qs = R['quintiles']
qa.bar(range(5), [q['median_ratio'] for q in qs], color=[G[5], G[4], G[3], G[2], G[1]], width=0.7, lw=0)
for i, q in enumerate(qs):
    qa.text(i, q['median_ratio'] + 0.8, '%.1fx' % q['median_ratio'] if q['median_ratio'] < 30 else '%.0fx' % q['median_ratio'],
            family=MONO, fontsize=10.5, color=FG, ha='center')
qa.set_xticks(range(5)); qa.set_xticklabels(['smallest', '2', '3', '4', 'biggest'])
qa.set_yticks([])
for sp in qa.spines.values():
    sp.set_visible(False)
qa.tick_params(colors=MUT, labelsize=10, length=0)
for t in qa.get_xticklabels():
    t.set_family(MONO)
qa.set_ylim(0, 47)
fig.text(0.68, 0.243, 'median growth by fifth of\nparish size in 1086', family=SER, fontsize=11, color=MUT, va='top')

fig.text(0.04, 0.012,
         'Data: Hull Domesday Project (Prof. J.J.N. Palmer, George Slater, University of Hull; CC BY-NC-SA) via the realm-domesday repository;\n'
         'Open Domesday by Anna Powell-Smith; Census 2021 households, Office for National Statistics (OGL v3), contains OS data\n'
         '© Crown copyright and database right 2022; coastline Natural Earth. Domesday counts heads of households, not people;\n'
         'an entry describing several places is shared equally among them. Unparished towns and cities are left out.\n'
         'Analysis and chart: Tristan Hotham, with Python and matplotlib.',
         family=MONO, fontsize=9, color=MUT, linespacing=1.45, va='bottom')

fig.savefig(os.path.join(HERE, 'is_domesday_destiny.png'), facecolor=BG, dpi=200)
print('ok')
