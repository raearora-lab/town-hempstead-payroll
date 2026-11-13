# Town of Hempstead Payroll Explorer

An independent, searchable presentation of Town of Hempstead employee earnings reported to NYSLRS for the 2025–26 reporting year.

## Data caveat

The figures are **pensionable earnings**, including overtime and other extras—not authorized base salaries. The municipal reporting year ends March 31. See [SeeThroughNY's municipal data notes](https://seethroughny.net/data-notes/municipal/) for exclusions and limitations.

## Refresh the dataset

```bash
python scripts/fetch_payroll.py
```

## Run locally

```bash
python -m http.server 8000
```

Then visit `http://localhost:8000`.

## Files

- `data/payroll.json` — website dataset and metadata
- `data/payroll.csv` — downloadable complete dataset
- `scripts/fetch_payroll.py` — reproducible source pull

The site is not affiliated with the Town of Hempstead.
