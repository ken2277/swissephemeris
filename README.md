# swissephemeris

Natal chart calculation code used by [moonsign-astrology.com](https://moonsign-astrology.com/).

This repository contains only the part of the site's backend that uses the
[Swiss Ephemeris](https://www.astro.com/swisseph/) (via `pyswisseph`). It is published
under the **GNU AGPL v3** (see `LICENSE`) because the Swiss Ephemeris is used under its
AGPL option. The rest of the site (pages, contact form, map proxy) is not included.

## Contents

- `app/natal_chart.py` – natal chart calculation (planets, houses, angles)
- `app/ephemeris.py` – Swiss Ephemeris path setup
- `app/aspects.py` – aspect calculation
- `app/zodiac.py` – zodiac sign helpers
- `app/timezone_utils.py` – local time to UTC conversion
- `app/api_routes.py` – the `/api/natal-chart` endpoint and input validation
- `ephe/`, `scripts/download_ephemeris.sh` – ephemeris data directory and download script

These files are copied from the site's source repository. They originally run inside a
Flask app whose factory (`create_app`) and `config.py` are not included here.

Copyright (c) 2026 Ken Kusuki
