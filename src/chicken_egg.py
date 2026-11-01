"""Caillaud and Jullien (2003) on New York City ride-hailing, 2015-2026.

Reads the committed TLC tables (data/raw/ and data/processed/, built by src/build_data.py) and writes every
table and chart used in the README to results/.

  1. Market structure and multihoming. Trips and distinct vehicles per app company per month (TLC base
     aggregate report) against distinct vehicles doing any app trip (TLC monthly report). Vehicles counted by
     two companies in the same month are drivers using both apps ("multihoming").
  2. Divide and conquer. An entrant that pays drivers more can sign them up (divide) but needs riders to keep
     them busy (conquer). Trips per vehicle for Juno, Via and Lyft relative to Uber, month by month.
  3. Transaction fees. Each trip's platform cut = base passenger fare - driver pay (TLC trip records). Share
     of trips on which the platform pays the driver more than the rider paid (a subsidized match).
  4. Proposition 4 test. Within the same pickup zone and month, is Uber's cut (the platform that handles
     most matches) lower than Lyft's, as the paper's "first source / second source" equilibrium predicts?

Run from the repository root:  python src/chicken_egg.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
OUT = ROOT / "results"

COMPANIES = {"UBER": "Uber", "LYFT": "Lyft", "JUNO": "Juno", "VIA": "Via"}
HAC_LAGS = 12          # Newey-West lags for monthly series: one year
MIN_ZONE_TRIPS = 100   # a zone-month cell enters the Uber-Lyft comparison only if each has 100+ trips there
LAST_FULL_YEAR = 2025  # last calendar year with all twelve months of trip records
COLORS = {"Uber": "#1f4e79", "Lyft": "#c2185b", "Juno": "#e69f00", "Via": "#009e73"}


def say(msg):
    print(msg, flush=True)


def market_structure():
    base = pd.read_csv(RAW / "fhv_base_aggregate_app_companies.csv")
    base["month"] = base["year"].astype(str) + "-" + base["month"].map("{:02d}".format)
    base["platform"] = base["base_license_number"].map(COMPANIES)
    say(f"base aggregate report: {len(base)} company-month rows, {base['month'].min()} to {base['month'].max()}")
    rep = pd.read_csv(RAW / "tlc_data_reports_monthly.csv", thousands=",")
    rep = rep[rep["License Class"] == "FHV - High Volume"].rename(columns={"Month/Year": "month"})
    say(f"TLC monthly report: {len(rep)} High Volume months")
    trips = base.pivot_table(index="month", columns="platform", values="total_dispatched_trips", aggfunc="sum")
    veh = base.pivot_table(index="month", columns="platform", values="unique_dispatched_vehicles", aggfunc="sum")
    d = pd.DataFrame(index=trips.index)
    for p in COMPANIES.values():
        d[f"trips_{p}"] = trips.get(p)
        d[f"vehicles_{p}"] = veh.get(p)
    d["trips_total"] = trips.sum(axis=1)
    for p in COMPANIES.values():
        d[f"trip_share_{p}"] = d[f"trips_{p}"] / d["trips_total"]
    d["hhi_trips"] = (trips.div(trips.sum(axis=1), axis=0) ** 2).sum(axis=1) * 10_000
    d["active_platforms"] = trips.notna().sum(axis=1)
    d = d.join(rep.set_index("month")[["Unique Vehicles"]].rename(columns={"Unique Vehicles": "vehicles_any_app"}))
    n0 = len(d)
    d = d.dropna(subset=["vehicles_any_app"])
    say(f"market structure: kept {len(d)} months with both sources, dropped {n0 - len(d)}")
    d["app_memberships"] = veh.reindex(d.index).sum(axis=1)
    # With two companies the excess equals the number of vehicles on both apps; with three or four it counts
    # a vehicle on k apps k-1 times, so it is an upper bound on the number of multihoming vehicles.
    d["excess_memberships"] = d["app_memberships"] - d["vehicles_any_app"]
    d["multihoming_share"] = d["excess_memberships"] / d["vehicles_any_app"]
    two = d["active_platforms"] == 2
    d["lyft_fleet_also_on_uber"] = np.where(two, d["excess_memberships"] / d["vehicles_Lyft"], np.nan)
    d["uber_fleet_also_on_lyft"] = np.where(two, d["excess_memberships"] / d["vehicles_Uber"], np.nan)
    d.index.name = "month"
    d.reset_index().to_csv(OUT / "market_structure_monthly.csv", index=False, float_format="%.4f")
    yr = d.groupby(d.index.str[:4])
    ann = pd.DataFrame({"months": yr.size(), "trips_total": yr["trips_total"].sum(),
                        "active_platforms_max": yr["active_platforms"].max(),
                        "mean_vehicles_any_app": yr["vehicles_any_app"].mean(),
                        "mean_multihoming_share": yr["multihoming_share"].mean(),
                        "mean_lyft_fleet_also_on_uber": yr["lyft_fleet_also_on_uber"].mean(),
                        "mean_hhi_trips": yr["hhi_trips"].mean()})
    for p in COMPANIES.values():
        ann[f"trip_share_{p}"] = yr[f"trips_{p}"].sum() / ann["trips_total"]
        ann[f"mean_vehicles_{p}"] = yr[f"vehicles_{p}"].mean()
    ann.index.name = "year"
    ann.reset_index().to_csv(OUT / "market_structure_by_year.csv", index=False, float_format="%.4f")
    return d


def hac_mean(series):
    y = series.dropna().to_numpy()
    fit = sm.OLS(y, np.ones(len(y))).fit(cov_type="HAC", cov_kwds={"maxlags": HAC_LAGS})
    lo, hi = fit.conf_int()[0]
    return fit.params[0], fit.bse[0], lo, hi, fit.pvalues[0], len(y)


def divide_and_conquer(d):
    rows = []
    for p in ["Lyft", "Juno", "Via"]:
        gap = np.log(d[f"trips_{p}"] / d[f"vehicles_{p}"]) - np.log(d["trips_Uber"] / d["vehicles_Uber"])
        b, se, lo, hi, pv, n = hac_mean(gap)
        first = gap.dropna().index
        sub = d.loc[first]
        rows.append({"platform": p, "first_month": first.min(), "last_month": first.max(), "months": n,
                     "mean_log_gap_trips_per_vehicle": b, "se_hac": se, "ci_low": lo, "ci_high": hi, "p_value": pv,
                     "trips_per_vehicle_relative_to_uber": np.exp(b),
                     "ratio_ci_low": np.exp(lo), "ratio_ci_high": np.exp(hi),
                     "peak_trip_share": sub[f"trip_share_{p}"].max(),
                     "peak_month_trip_share": sub[f"trip_share_{p}"].idxmax(),
                     "peak_vehicles": sub[f"vehicles_{p}"].max(),
                     "peak_fleet_relative_to_uber": (sub[f"vehicles_{p}"] / sub["vehicles_Uber"]).max(),
                     "mean_fleet_relative_to_uber": (sub[f"vehicles_{p}"] / sub["vehicles_Uber"]).mean(),
                     "mean_trips_relative_to_uber": (sub[f"trips_{p}"] / sub["trips_Uber"]).mean()})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "divide_and_conquer.csv", index=False, float_format="%.4f")
    return out


def load_trips():
    z = pd.read_csv(PROC / "trips_platform_month_zone.csv")
    log = pd.read_csv(PROC / "trips_build_log.csv")
    say(f"trip records: {log['rows_in_file'].sum():,} rows in {len(log)} monthly files, "
        f"{log['month'].min()} to {log['month'].max()}")
    say(f"  dropped {log['rows_dropped_shared_request'].sum():,} pooled requests and "
        f"{log['rows_dropped_nonpositive_fare_pay_miles_or_time'].sum():,} rows with non-positive fare, pay, "
        f"miles or time; kept {log['rows_kept'].sum():,}")
    z["year"] = z["month"].str[:4].astype(int)
    return z, log


def fee_tables(z):
    m = z.groupby(["platform", "month"])[["trips", "fare", "driver_pay", "subsidized", "miles", "tips"]].sum()
    m["take_rate"] = 1 - m["driver_pay"] / m["fare"]
    m["take_per_trip"] = (m["fare"] - m["driver_pay"]) / m["trips"]
    m["fare_per_trip"] = m["fare"] / m["trips"]
    m["driver_pay_per_trip"] = m["driver_pay"] / m["trips"]
    m["subsidized_share"] = m["subsidized"] / m["trips"]
    m = m.reset_index()
    dist = pd.read_csv(PROC / "trips_platform_month_dist.csv")
    m = m.merge(dist.drop(columns="trips"), on=["platform", "month"], how="left")
    m.to_csv(OUT / "take_rate_monthly.csv", index=False, float_format="%.4f")
    y = z.groupby(["platform", "year"])[["trips", "fare", "driver_pay", "subsidized"]].sum()
    y["months"] = z.groupby(["platform", "year"])["month"].nunique()
    y["take_rate"] = 1 - y["driver_pay"] / y["fare"]
    y["fare_per_trip"] = y["fare"] / y["trips"]
    y["driver_pay_per_trip"] = y["driver_pay"] / y["trips"]
    y["take_per_trip"] = y["fare_per_trip"] - y["driver_pay_per_trip"]
    y["subsidized_share"] = y["subsidized"] / y["trips"]
    y = y.reset_index()
    y.to_csv(OUT / "take_rate_by_year.csv", index=False, float_format="%.4f")
    return m, y


def within_cell(z, platforms, outcome, ref, label, cell="PULocationID", cluster="PULocationID"):
    """Weighted regression of a cell-month outcome on platform dummies with cell x month fixed effects
    (cell = pickup zone by default, or hour of day), standard errors clustered by pickup zone (or month).
    Fixed effects are absorbed by within-cell demeaning."""
    s = z[z["platform"].isin(platforms)].copy()
    s["take_rate"] = 1 - s["driver_pay"] / s["fare"]
    s["subsidized_share"] = s["subsidized"] / s["trips"]
    n0 = len(s)
    s = s[s["trips"] >= MIN_ZONE_TRIPS]
    cells = s.groupby([cell, "month"])["platform"].transform("nunique")
    s = s[cells == len(platforms)].copy()
    others = [p for p in platforms if p != ref]
    for p in others:
        s[p] = (s["platform"] == p).astype(float)
    cols = [outcome] + others
    w = s["trips"]
    g = s.groupby([cell, "month"])
    for c in cols:
        wm = (s[c] * w).groupby([s[cell], s["month"]]).transform("sum") / g["trips"].transform("sum")
        s[c + "_dm"] = s[c] - wm
    X = s[[p + "_dm" for p in others]]
    fit = sm.WLS(s[outcome + "_dm"], X, weights=w).fit(cov_type="cluster",
                                                         cov_kwds={"groups": pd.factorize(s[cluster])[0]})
    rows = []
    for p in others:
        lo, hi = fit.conf_int().loc[p + "_dm"]
        rows.append({"test": label, "outcome": outcome, "platform": p, "reference": ref,
                     "cells": cell, "cluster": cluster,
                     "estimate": fit.params[p + "_dm"], "se_cluster": fit.bse[p + "_dm"], "ci_low": lo,
                     "ci_high": hi, "p_value": fit.pvalues[p + "_dm"], "rows": len(s), "rows_dropped": n0 - len(s),
                     "cell_values": s[cell].nunique(), "months": s["month"].nunique(),
                     "trips": int(w.sum()),
                     "reference_mean": np.average(s.loc[s["platform"] == ref, outcome],
                                                  weights=w[s["platform"] == ref])})
    return rows


def fee_tests(z):
    rows = []
    both = z[z["platform"].isin(["Uber", "Lyft"])]
    rows += within_cell(both, ["Lyft", "Uber"], "take_rate", "Lyft", "Uber vs Lyft, all months")
    rows += within_cell(both, ["Lyft", "Uber"], "subsidized_share", "Lyft", "Uber vs Lyft, all months")
    early, late = both[both["year"] <= 2021], both[both["year"] >= 2023]
    rows += within_cell(early, ["Lyft", "Uber"], "take_rate", "Lyft", "Uber vs Lyft, 2019-2021 (3-4 apps)")
    rows += within_cell(late, ["Lyft", "Uber"], "take_rate", "Lyft", "Uber vs Lyft, 2023-2026 (2 apps)")
    rows += within_cell(both, ["Lyft", "Uber"], "take_rate", "Lyft", "Uber vs Lyft, all months, month clusters",
                        cluster="month")
    for yr in sorted(both["year"].unique()):
        rows += within_cell(both[both["year"] == yr], ["Lyft", "Uber"], "take_rate", "Lyft", f"Uber vs Lyft, {yr}")
    hour = pd.read_csv(PROC / "trips_platform_month_hour.csv")
    hour = hour[hour["platform"].isin(["Uber", "Lyft"])]
    rows += within_cell(hour, ["Lyft", "Uber"], "take_rate", "Lyft", "Uber vs Lyft, hour-of-day cells",
                        cell="hour", cluster="month")
    juno = z[(z["month"] <= "2019-10") & z["platform"].isin(["Uber", "Lyft", "Juno"])]
    rows += within_cell(juno, ["Uber", "Lyft", "Juno"], "subsidized_share", "Uber", "Juno and Lyft vs Uber, Feb-Oct 2019")
    rows += within_cell(juno, ["Uber", "Lyft", "Juno"], "take_rate", "Uber", "Juno and Lyft vs Uber, Feb-Oct 2019")
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "fee_tests.csv", index=False, float_format="%.5f")
    for _, r in out.iterrows():
        say(f"  {r['test']:<38} {r['outcome']:<17} {r['platform']}-{r['reference']}: {r['estimate']:+.4f} "
            f"(se {r['se_cluster']:.4f}, p={r['p_value']:.3g}, N={r['rows']})")
    return out


def borough_table(z):
    zones = pd.read_csv(RAW / "taxi_zone_lookup.csv")
    s = z[(z["year"] == LAST_FULL_YEAR) & z["platform"].isin(["Uber", "Lyft"])].merge(
        zones[["LocationID", "Borough"]], left_on="PULocationID", right_on="LocationID", how="left")
    b = s.groupby(["Borough", "platform"])[["trips", "fare", "driver_pay", "subsidized"]].sum().reset_index()
    b["take_rate"] = 1 - b["driver_pay"] / b["fare"]
    b["subsidized_share"] = b["subsidized"] / b["trips"]
    tot = b.groupby("Borough")["trips"].transform("sum")
    b["trip_share_in_borough"] = b["trips"] / tot
    b.to_csv(OUT / "boroughs_last_full_year.csv", index=False, float_format="%.4f")
    return b


def platform_names(d, dc, y):
    rows = []
    for p in ["Uber", "Lyft", "Juno", "Via"]:
        t = d[f"trips_{p}"].dropna()
        yy = y[y["platform"] == p].set_index("year")
        yr = d[d.index.str[:4] == str(LAST_FULL_YEAR)]
        later = d[d.index >= "2016-01"]   # Uber was the only app company in 2015's first months
        r = {"platform": p, "first_month_in_tlc_data": t.index.min(), "last_month_in_tlc_data": t.index.max(),
             "peak_trip_share_since_2016": later[f"trip_share_{p}"].max(),
             f"trip_share_{LAST_FULL_YEAR}": yr[f"trips_{p}"].sum() / yr["trips_total"].sum(),
             "peak_vehicles": d[f"vehicles_{p}"].max(),
             f"mean_monthly_vehicles_{LAST_FULL_YEAR}": yr[f"vehicles_{p}"].mean(),
             "take_rate_2019": yy["take_rate"].get(2019, np.nan),
             "subsidized_share_2019": yy["subsidized_share"].get(2019, np.nan),
             f"take_rate_{LAST_FULL_YEAR}": yy["take_rate"].get(LAST_FULL_YEAR, np.nan),
             f"subsidized_share_{LAST_FULL_YEAR}": yy["subsidized_share"].get(LAST_FULL_YEAR, np.nan),
             f"trips_{LAST_FULL_YEAR}": yy["trips"].get(LAST_FULL_YEAR, np.nan)}
        if p != "Uber":
            r["trips_per_vehicle_relative_to_uber"] = dc.set_index("platform").loc[p, "trips_per_vehicle_relative_to_uber"]
        rows.append(r)
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "platforms.csv", index=False, float_format="%.4f")
    return out


def figures(d, m):
    fig, ax = plt.subplots(2, 1, figsize=(9, 7.5), sharex=True)
    x = pd.to_datetime(d.index)
    for p in COMPANIES.values():
        ax[0].plot(x, 100 * d[f"trip_share_{p}"], color=COLORS[p], label=p, lw=1.8)
    ax[0].set_ylabel("Share of app trips (%)")
    ax[0].set_title("Who carries New York's app rides", loc="left", fontsize=11)
    ax[0].legend(frameon=False, ncol=4)
    ax[1].plot(x, 100 * d["multihoming_share"], color="#444444", lw=1.8, label="All app vehicles")
    ax[1].plot(x, 100 * d["lyft_fleet_also_on_uber"], color=COLORS["Lyft"], lw=1.8,
               label="Lyft's vehicles that also drove for Uber")
    ax[1].set_ylabel("Percent")
    ax[1].set_title("Drivers on more than one app (2015-2021, with 3-4 apps: extra app sign-ups per vehicle)", loc="left", fontsize=11)
    ax[1].legend(frameon=False, loc="lower right")
    for a in ax:
        a.spines[["top", "right"]].set_visible(False)
        a.grid(axis="y", color="#dddddd", lw=0.6)
    fig.tight_layout()
    fig.savefig(OUT / "market_and_multihoming.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(2, 1, figsize=(9, 7.5), sharex=True)
    for p in ["Uber", "Lyft", "Juno"]:
        s = m[m["platform"] == p]
        xx = pd.to_datetime(s["month"])
        ax[0].plot(xx, 100 * s["take_rate"], color=COLORS[p], lw=1.8, label=p)
        ax[1].plot(xx, 100 * s["subsidized_share"], color=COLORS[p], lw=1.8, label=p)
    ax[0].set_ylabel("Platform's cut, % of base fare")
    ax[0].set_title("The platform's cut of each fare", loc="left", fontsize=11)
    ax[1].set_ylabel("Percent of trips")
    ax[1].set_title("Trips on which the driver was paid more than the rider's base fare", loc="left", fontsize=11)
    for a in ax:
        a.legend(frameon=False, ncol=3)
        a.spines[["top", "right"]].set_visible(False)
        a.grid(axis="y", color="#dddddd", lw=0.6)
    ax[0].axhline(0, color="#999999", lw=0.8)
    fig.tight_layout()
    fig.savefig(OUT / "take_rates.png", dpi=150)
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    d = market_structure()
    two = d[d["active_platforms"] == 2]
    say(f"multihoming, two-platform months ({two.index.min()} to {two.index.max()}): "
        f"mean share of all app vehicles on both apps {two['multihoming_share'].mean():.3f}; "
        f"mean share of Lyft's fleet also on Uber {two['lyft_fleet_also_on_uber'].mean():.3f}")
    dc = divide_and_conquer(d)
    say(dc[["platform", "months", "trips_per_vehicle_relative_to_uber", "ratio_ci_low", "ratio_ci_high", "p_value"]].to_string(index=False))
    z, _ = load_trips()
    m, y = fee_tables(z)
    say(y[["platform", "year", "months", "trips", "take_rate", "subsidized_share"]].to_string(index=False))
    say("within zone-month tests:")
    fee_tests(z)
    borough_table(z)
    platform_names(d, dc, y)
    figures(d, m)
    say(f"wrote tables and figures to {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
