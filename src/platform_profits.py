"""Extension: does the platform's cut become a profit? Lyft's annual results from its 10-K filings, 2017-2025.

Caillaud and Jullien's central contrast is about profit, not about the per-trade fee. With exclusive services the
dominant intermediary earns zero; with nonexclusive services intermediaries can earn positive profits. The trip
records show the per-trip fee. This script reads the annual income-statement facts Lyft tagged in the inline
XBRL of its 10-K filings (saved by src/build_data.py in data/raw/lyft_10k_facts.csv) and computes margins.

Lyft earns nearly all its revenue from ride-hailing, and until it bought the European app Freenow in July 2025 it
operated only in North America, so its operating margin is the closest public number to the intermediation
profit in the model. Its revenue is, roughly, the platform's cut
of what riders pay (after incentives booked as contra-revenue), so operating income divided by revenue says how
much of each dollar of cut is left after running the platform. Uber is not included: its consolidated accounts
mix ride-hailing with delivery and freight, and its investor-relations site refused automated downloads.

Run from the repository root:  python src/platform_profits.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "results"

COST_LINES = ["CostOfRevenue", "SellingAndMarketingExpense", "ResearchAndDevelopmentExpense",
              "GeneralAndAdministrativeExpense"]


def main():
    OUT.mkdir(exist_ok=True)
    f = pd.read_csv(RAW / "lyft_10k_facts.csv")
    print(f"Lyft 10-K facts: {len(f)} rows from {f['accession'].nunique()} filings")
    f["year"] = f["end"].str[:4].astype(int)
    # A year appears in up to three filings; keep the value from the latest filing (restatements win).
    conflicts = int((f.groupby(["concept", "year"])["value_usd"].nunique() > 1).sum())
    f = f.sort_values(["end", "accession"]).groupby(["concept", "year"]).tail(1)
    print(f"  kept {len(f)} concept-year values; {conflicts} concept-years differ across filings (latest kept)")
    d = f.pivot(index="year", columns="concept", values="value_usd")
    # The fiscal 2019 filing tags total revenue as revenue from contracts with customers; later filings use
    # Revenues (which then also includes a small amount of lease revenue).
    d["Revenues"] = d["Revenues"].fillna(d["RevenueFromContractWithCustomerExcludingAssessedTax"])
    n0 = len(d)
    d = d.dropna(subset=["Revenues", "OperatingIncomeLoss"])
    print(f"  kept {len(d)} fiscal years with revenue and operating income, dropped {n0 - len(d)}")
    d["operating_margin"] = d["OperatingIncomeLoss"] / d["Revenues"]
    d["net_margin"] = d["NetIncomeLoss"] / d["Revenues"]
    for c in COST_LINES:
        d[c + "_share_of_revenue"] = d[c] / d["Revenues"]
    d = d.reset_index()
    d.to_csv(OUT / "lyft_profits.csv", index=False, float_format="%.4f")

    pre = d[d["year"] <= 2021]
    post = d[d["year"] >= 2022]
    summ = pd.DataFrame([{
        "years": f"{d['year'].min()}-{d['year'].max()}",
        "cumulative_revenue": d["Revenues"].sum(),
        "cumulative_operating_income": d["OperatingIncomeLoss"].sum(),
        "cumulative_operating_margin": d["OperatingIncomeLoss"].sum() / d["Revenues"].sum(),
        "years_with_operating_profit": int((d["OperatingIncomeLoss"] > 0).sum()),
        "best_year": int(d.loc[d["operating_margin"].idxmax(), "year"]),
        "best_operating_margin": d["operating_margin"].max(),
        "operating_margin_2017_2021": pre["OperatingIncomeLoss"].sum() / pre["Revenues"].sum(),
        "operating_margin_2022_2025": post["OperatingIncomeLoss"].sum() / post["Revenues"].sum(),
        "latest_year": int(d["year"].max()),
        "latest_operating_margin": d.loc[d["year"].idxmax(), "operating_margin"],
        "latest_operating_income": d.loc[d["year"].idxmax(), "OperatingIncomeLoss"],
        "latest_revenue": d.loc[d["year"].idxmax(), "Revenues"],
    }])
    summ.to_csv(OUT / "lyft_profits_summary.csv", index=False, float_format="%.4f")
    show = d[["year", "Revenues", "OperatingIncomeLoss", "operating_margin", "NetIncomeLoss"]].copy()
    show[["Revenues", "OperatingIncomeLoss", "NetIncomeLoss"]] = (show[["Revenues", "OperatingIncomeLoss",
                                                                        "NetIncomeLoss"]] / 1e6).round(1)
    print(show.to_string(index=False))
    print(summ.T.to_string(header=False))
    if np.isnan(summ.loc[0, "cumulative_operating_margin"]):
        raise SystemExit("no usable Lyft data")


if __name__ == "__main__":
    main()
