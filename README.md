# Is Domesday Destiny?

Does a place's size in 1086 still predict its size today? Every place named in Domesday Book, set against the 2021 census, parish by parish.

**Interactive version:** https://tristan-hotham.github.io/domesday-destiny/

This repository holds the interactive page, the place-level and parish-level datasets, the computed results and the analysis code for a data study by Dr Tristan Hotham (Independent researcher).

## Files

- `index.html`: the interactive page (map, charts, tables, search). The data is embedded, so it works as a single file.
- `header.png`: social card (1200 by 630).
- `data/domesday_places.csv`: one row per Domesday place (14,334), with its 1086 figures (households, villagers, smallholders, slaves, plough teams, mills, value in pence and more), the entries its households come from, its location, the 2021 civil parish it lies in, that parish's Census 2021 residents and households, and the "possibly lost" flag.
- `data/domesday_parishes.csv`: one row per modern parish that contains a Domesday place (7,641), with the summed 1086 figures of its places, its 2021 residents and households, and the ratio of 2021 to 1086 households.
- `data/results.json`: every number quoted on the page.
- `code/01_extract.py`: reads the realm-domesday reference files and writes the two CSV files.
- `code/02_analyse.py`: correlations, regressions, league tables and county figures; writes `results.json` and a temporary compact data file for the page.
- `code/03_build_page.py`: fills `code/page_template.html` with the results and data to make `index.html`. Every number in the text is a token filled from `results.json`; the map and chart data are embedded in the page.
- `code/04_header.py`: renders `header.png` with Playwright.

To rebuild: clone https://github.com/embabel-worlds/realm-domesday, then run

```
python3 code/01_extract.py /path/to/realm-domesday
python3 code/02_analyse.py
python3 code/03_build_page.py
python3 code/04_header.py
```

It needs Python 3 with pyyaml, pandas, numpy, scipy, statsmodels and playwright.

## Method in brief

- An entry's households are given to the places it describes, shared equally when it describes several (the rule used by the repository's own then-and-now views). Places an entry only names as dependencies get nothing from it.
- Each place reaches its 2021 civil parish through the repository's point test on the centre of its 1 km grid square. Parish figures sum all the Domesday places in the parish.
- The main test compares 1086 households with 2021 households for the 6,376 parishes with a figure at both dates: Pearson correlation and fitted slope on log10 values, and Spearman rank correlation.
- Domesday counts heads of household, not people, so 1086 households are compared with 2021 households.

## Known limits

- Unparished areas (most large towns and cities) have no Census 2021 figure in the source, so they are left out of the comparisons.
- Some entries carry an "altogether" or "in total" figure for a group of places while describing only one. These are flagged; parishes that depend mostly on them are left out of the league tables.
- Yorkshire's record is thin, the far north was largely not surveyed, and London and Winchester are absent. Little Domesday (Essex, Norfolk, Suffolk) figures are parsed from the translation.
- "Possibly lost" places are candidates, not findings.

## Sources and licence

- Domesday data: Hull Domesday Project, Professor J.J.N. Palmer, George Slater and the University of Hull (CC BY-NC-SA), https://digitalcollections.hull.ac.uk/collections/3t945r28b
- Joined data: the realm-domesday repository by embabel-worlds, https://github.com/embabel-worlds/realm-domesday
- Place links: Open Domesday by Anna Powell-Smith, https://opendomesday.org/
- Census 2021: Office for National Statistics, licensed under the Open Government Licence v3.0. Contains OS data © Crown copyright and database right 2022.
- Base map tiles: © Esri, HERE, Garmin, © OpenStreetMap contributors, and the GIS user community.

Because the Domesday figures are CC BY-NC-SA, the derived data (`data/`) and the page text are released under CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/). The code (`code/`) is released under the MIT licence (see `LICENSE`).

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
