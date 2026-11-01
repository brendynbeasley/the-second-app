"""Download the public inputs and reduce the NYC trip records to small committed tables.

What it does
  1. Saves the NYC Taxi & Limousine Commission (TLC) monthly industry report, which gives the number of
     distinct vehicles that did at least one app-dispatched (High Volume) trip each month,
     and the TLC taxi zone lookup (pickup zone to borough).
  2. Saves the NYC Open Data "FHV Base Aggregate Report" rows for the four app companies (Uber, Lyft, Via,
     Juno): trips and distinct vehicles per company per month, 2015 onward.
  3. Saves Lyft's annual income-statement facts from the inline XBRL of its 10-K filings for fiscal 2019,
     2022 and 2025 (each covers three years), taken from Lyft's investor-relations copy of the SEC filings.
  4. Downloads every High Volume For-Hire Vehicle trip file (about 500 MB a month, February 2019 onward),
     computes each trip's platform cut (rider fare minus driver pay) and aggregates it to
     platform x month x pickup zone and platform x month tables in data/processed/. Each trip file is
     deleted after it is reduced unless --keep is given.

Run from the repository root:
  python src/build_data.py                       # everything (about 46 GB of downloads, about 90 minutes)
  python src/build_data.py --skip-trips          # only the small files
  python src/build_data.py --months 2019-02 2019-03 --raw-dir data/raw/tlc
Months already present in data/processed/ are recomputed only with --force.
"""
import argparse
import re
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import requests

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"

TRIP_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/fhvhv_tripdata_{ym}.parquet"
MONTHLY_REPORT_URL = "https://www.nyc.gov/assets/tlc/downloads/csv/data_reports_monthly.csv"
ZONE_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"   # pickup zone -> borough
BASE_AGG_URL = ("https://data.cityofnewyork.us/resource/2v9c-2k7f.json?"
                "$where=base_license_number in('UBER','LYFT','VIA','JUNO')&$limit=50000")
# Lyft 10-K filings (SEC accession numbers) as served by Lyft's investor-relations site. The SEC's own EDGAR
# endpoints refused requests from this machine on the download date (2026-11-01); the files are the same filings.
LYFT_10K_URL = "https://investor.lyft.com/financials/sec-filings/content/{acc}/{acc}-xbrl.zip"
LYFT_10K = {"0001759509-20-000009": "lyft-20191231.htm", "0001759509-23-000028": "lyft-20221231.htm",
            "0001628280-26-006960": "lyft-20251231.htm"}
XBRL_CONCEPTS = ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "CostOfRevenue", "SellingAndMarketingExpense", "ResearchAndDevelopmentExpense",
                 "GeneralAndAdministrativeExpense", "OperatingIncomeLoss", "NetIncomeLoss"]
# TLC license numbers of the app companies (TLC trip record data dictionary).
PLATFORMS = {"HV0002": "Juno", "HV0003": "Uber", "HV0004": "Via", "HV0005": "Lyft"}
FIRST_MONTH = "2019-02"   # first month with fare and driver-pay fields in the public trip files
LAST_MONTH = "2026-09"    # last month published when the data were downloaded (2026-11-01)
COLS = ["hvfhs_license_num", "pickup_datetime", "PULocationID", "trip_miles", "trip_time",
        "base_passenger_fare", "driver_pay", "tips", "shared_request_flag"]
QUANTILES = [0.10, 0.25, 0.50, 0.75, 0.90]


def get(url, dest, headers=None):
    tmp = dest.with_name("." + dest.name + ".part")
    with requests.get(url, headers=headers or {"User-Agent": "Mozilla/5.0"}, stream=True, timeout=600) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    tmp.rename(dest)
    return dest


def small_files():
    RAW.mkdir(parents=True, exist_ok=True)
    get(MONTHLY_REPORT_URL, RAW / "tlc_data_reports_monthly.csv")
    print("saved TLC monthly report")
    get(ZONE_URL, RAW / "taxi_zone_lookup.csv")
    print("saved TLC taxi zone lookup")
    rows = requests.get(BASE_AGG_URL, timeout=120).json()
    base = pd.DataFrame(rows)[["base_license_number", "year", "month", "total_dispatched_trips",
                               "total_dispatched_shared_trips", "unique_dispatched_vehicles"]]
    for c in ["year", "month", "total_dispatched_trips", "total_dispatched_shared_trips", "unique_dispatched_vehicles"]:
        base[c] = pd.to_numeric(base[c])
    base = base.sort_values(["year", "month", "base_license_number"])
    base.to_csv(RAW / "fhv_base_aggregate_app_companies.csv", index=False)
    print(f"saved base aggregate report: {len(base)} company-month rows")
    facts = []
    for acc, member in LYFT_10K.items():
        z = RAW / f"lyft_10k_{acc}.zip"
        get(LYFT_10K_URL.format(acc=acc), z)
        with zipfile.ZipFile(z) as zf:
            html = zf.read(member).decode("utf-8")
        z.unlink()
        rows = parse_inline_xbrl(html, acc)
        facts += rows
        print(f"parsed {member}: {len(rows)} annual facts")
    pd.DataFrame(facts).to_csv(RAW / "lyft_10k_facts.csv", index=False)


def parse_inline_xbrl(html, acc):
    """Annual, undimensioned income-statement facts from an inline XBRL 10-K."""
    ctx = {}
    for m in re.finditer(r'<xbrli:context id="([^"]+)">(.*?)</xbrli:context>', html, re.S):
        body = m.group(2)
        if "xbrli:segment" in body:
            continue
        p = re.search(r"<xbrli:startDate>([^<]+)</xbrli:startDate><xbrli:endDate>([^<]+)</xbrli:endDate>", body)
        if p:
            ctx[m.group(1)] = p.groups()
    rows = []
    for m in re.finditer(r"<ix:nonFraction([^>]*)>([^<]*)</ix:nonFraction>", html):
        attrs = dict(re.findall(r'(\w+(?::\w+)?)="([^"]*)"', m.group(1)))
        name = attrs.get("name", "")
        if not name.startswith("us-gaap:") or name[8:] not in XBRL_CONCEPTS or attrs.get("contextRef") not in ctx:
            continue
        start, end = ctx[attrs["contextRef"]]
        if not 350 <= (pd.Timestamp(end) - pd.Timestamp(start)).days <= 380:
            continue
        text = m.group(2).replace(",", "").strip()
        if not re.fullmatch(r"\d+(\.\d+)?", text):
            continue  # empty or worded facts ("no", "-") carry no amount
        val = float(text) * 10 ** int(attrs.get("scale", "0"))
        if attrs.get("sign") == "-":
            val = -val
        rows.append({"concept": name[8:], "start": start, "end": end, "value_usd": val, "accession": acc})
    return pd.DataFrame(rows).drop_duplicates().to_dict("records")


def months_between(a, b):
    return [p.strftime("%Y-%m") for p in pd.period_range(a, b, freq="M")]


def reduce_month(path, ym):
    t = pq.read_table(path, columns=COLS).to_pandas()
    n0 = len(t)
    t = t[t["hvfhs_license_num"].isin(PLATFORMS)]
    n_platform = len(t)
    # Pooled (shared) requests are dropped: Lyft and Via record no per-trip driver pay for most of them,
    # and one driver payment is spread over several passengers' records, so the per-trip cut is undefined.
    shared = t["shared_request_flag"].eq("Y")
    t = t[~shared]
    ok = (t["base_passenger_fare"] > 0) & (t["driver_pay"] > 0) & (t["trip_miles"] > 0) & (t["trip_time"] > 0)
    t = t[ok].copy()
    t["platform"] = t["hvfhs_license_num"].map(PLATFORMS)
    t["take"] = t["base_passenger_fare"] - t["driver_pay"]
    t["take_rate"] = t["take"] / t["base_passenger_fare"]
    t["subsidized"] = t["take"] < 0
    t["hour"] = t["pickup_datetime"].dt.hour
    t["month"] = ym
    zone = (t.groupby(["platform", "month", "PULocationID"])
             .agg(trips=("take", "size"), fare=("base_passenger_fare", "sum"), driver_pay=("driver_pay", "sum"),
                  tips=("tips", "sum"), miles=("trip_miles", "sum"), seconds=("trip_time", "sum"),
                  subsidized=("subsidized", "sum"))
             .reset_index())
    hour = (t.groupby(["platform", "month", "hour"])
             .agg(trips=("take", "size"), fare=("base_passenger_fare", "sum"), driver_pay=("driver_pay", "sum"),
                  subsidized=("subsidized", "sum"))
             .reset_index())
    rows = []
    for plat, g in t.groupby("platform"):
        q = np.quantile(g["take_rate"].to_numpy(), QUANTILES)
        rows.append({"platform": plat, "month": ym, "trips": len(g),
                     "mean_trip_take_rate": g["take_rate"].mean(),
                     **{f"take_rate_p{int(x * 100)}": v for x, v in zip(QUANTILES, q)},
                     "median_fare": g["base_passenger_fare"].median(),
                     "median_driver_pay": g["driver_pay"].median()})
    dist = pd.DataFrame(rows)
    log = {"month": ym, "rows_in_file": n0, "rows_app_companies": n_platform,
           "rows_dropped_shared_request": int(shared.sum()),
           "rows_dropped_nonpositive_fare_pay_miles_or_time": int((~ok).sum()), "rows_kept": int(ok.sum())}
    return zone, hour, dist, log


def trips(months, raw_dir, keep, force):
    raw_dir.mkdir(parents=True, exist_ok=True)
    PROC.mkdir(parents=True, exist_ok=True)
    outs = {k: PROC / f"{k}.csv" for k in ["trips_platform_month_zone", "trips_platform_month_hour",
                                           "trips_platform_month_dist", "trips_build_log"]}
    old = {k: pd.read_csv(p) if p.exists() else pd.DataFrame() for k, p in outs.items()}
    done = set(old["trips_build_log"]["month"]) if len(old["trips_build_log"]) else set()
    for ym in months:
        if ym in done and not force:
            print(f"{ym}: already reduced, skipping (use --force to redo)")
            continue
        f = raw_dir / f"fhvhv_tripdata_{ym}.parquet"
        if not f.exists():
            get(TRIP_URL.format(ym=ym), f)
        zone, hour, dist, log = reduce_month(f, ym)
        print(f"{ym}: {log['rows_in_file']:,} rows, kept {log['rows_kept']:,}; dropped "
              f"{log['rows_dropped_shared_request']:,} pooled requests and "
              f"{log['rows_dropped_nonpositive_fare_pay_miles_or_time']:,} with non-positive fare, pay, miles or time")
        new = {"trips_platform_month_zone": zone, "trips_platform_month_hour": hour,
               "trips_platform_month_dist": dist, "trips_build_log": pd.DataFrame([log])}
        for k, df in new.items():
            prev = old[k]
            if len(prev):
                prev = prev[prev["month"] != ym]
            old[k] = pd.concat([prev, df], ignore_index=True).sort_values(
                [c for c in ["month", "platform"] if c in df.columns]).reset_index(drop=True)
            old[k].to_csv(outs[k], index=False, float_format="%.6g")
        if not keep:
            f.unlink()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--months", nargs="*", default=None, help="YYYY-MM list; default all months")
    ap.add_argument("--raw-dir", default=str(RAW / "tlc"), help="where trip files are downloaded")
    ap.add_argument("--keep", action="store_true", help="keep trip files after reducing them")
    ap.add_argument("--force", action="store_true", help="recompute months already reduced")
    ap.add_argument("--skip-trips", action="store_true")
    ap.add_argument("--skip-small", action="store_true")
    a = ap.parse_args()
    if not a.skip_small:
        small_files()
    if not a.skip_trips:
        months = a.months or months_between(FIRST_MONTH, LAST_MONTH)
        trips(months, Path(a.raw_dir), a.keep, a.force)


if __name__ == "__main__":
    main()
