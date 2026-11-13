#!/usr/bin/env python3
"""Download Town of Hempstead NYSLRS-reported earnings from SeeThroughNY."""
from __future__ import annotations

import csv
import html
import json
import re
from pathlib import Path

import requests

YEAR = "2026"
BASE = "https://seethroughny.net"
PAGE = f"{BASE}/payrolls/towns"
ENDPOINT = f"{BASE}/tools/required/reports/payroll?action=get"
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def clean(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", "", fragment))).strip()


def parse_rows(markup: str) -> list[dict]:
    records = []
    for match in re.finditer(
        r'<tr id="resultRow(?P<id>\d+)".*?</tr>\s*<tr id="expandRow(?P=id)".*?</tr>',
        markup,
        re.S,
    ):
        block = match.group(0)
        summary = block.split('</tr>', 1)[0]
        cells = re.findall(r'<td(?:\s+[^>]*)?>(.*?)</td>', summary, re.S)
        if len(cells) < 5:
            raise RuntimeError(f"Unexpected result row {match.group('id')}: {len(cells)} cells")
        name, agency, pay, category = map(clean, cells[1:5])
        fields = {
            clean(label): clean(value)
            for label, value in re.findall(
                r'<strong>(.*?)</strong>.*?</div>\s*<div class="col-xs-6">(.*?)</div>',
                block,
                re.S,
            )
        }
        records.append(
            {
                "id": match.group("id"),
                "name": name,
                "agency": agency,
                "total_pay": int(pay.replace("$", "").replace(",", "")),
                "category": category,
                "title": fields.get("Title", ""),
                "rate_of_pay": fields.get("Rate of Pay", ""),
                "pay_year": fields.get("Pay Year", YEAR),
                "pay_basis": fields.get("Pay Basis", ""),
            }
        )
    return records


def main() -> None:
    session = requests.Session()
    session.get(PAGE, timeout=60).raise_for_status()
    headers = {"X-Requested-With": "XMLHttpRequest", "Referer": PAGE}
    params = [
        ("PayYear[]", YEAR),
        ("BranchName[]", "Towns"),
        ("AgencyName[]", "Hempstead"),
        ("SortBy", "YTDPay DESC"),
    ]
    response = session.post(ENDPOINT, data=params, headers=headers, timeout=60)
    response.raise_for_status()
    payload = response.json()
    records = parse_rows(payload["html"])

    for page in range(1, int(payload["total_pages"])):
        page_params = params + [("current_page", str(page)), ("result_id", payload["result_id"])]
        response = session.post(ENDPOINT, data=page_params, headers=headers, timeout=60)
        response.raise_for_status()
        records.extend(parse_rows(response.json()["html"]))

    expected = int(payload["total_records"])
    if len(records) != expected:
        raise RuntimeError(f"Expected {expected:,} records; parsed {len(records):,}")

    records.sort(key=lambda row: (-row["total_pay"], row["name"]))
    for rank, record in enumerate(records, 1):
        record["rank"] = rank

    DATA.mkdir(parents=True, exist_ok=True)
    metadata = {
        "agency": "Town of Hempstead",
        "reporting_year": YEAR,
        "record_count": len(records),
        "source_reported_total": float(payload["total_sum"]),
        "sum_of_displayed_rounded_pay": sum(r["total_pay"] for r in records),
        "source": payload["share_url"],
        "source_notes": "https://seethroughny.net/data-notes/municipal/",
        "definition": "NYSLRS-reported pensionable earnings, including overtime and other extras; not base salary.",
    }
    (DATA / "payroll.json").write_text(json.dumps({"metadata": metadata, "records": records}, indent=2), encoding="utf-8")
    with (DATA / "payroll.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
