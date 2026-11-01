# Technical notes

This is the technical companion to the [README](README.md). Every table is in
[results/FINDINGS.md](results/FINDINGS.md), and a review of the original paper's methods is in
[METHODS_REVIEW.md](METHODS_REVIEW.md).

## The original study

Bernard Caillaud and Bruno Jullien, "Chicken & Egg: Competition among Intermediation Service Providers," *RAND
Journal of Economics* 34(2), Summer 2003, pp. 309–328. The paper is pure theory and reports no estimates. Its
headline results are qualitative. With exclusive services, the only equilibria have one intermediary serving all
users, charging the maximal transaction fee, subsidizing registration and earning zero profit (Proposition 1,
p. 314). With nonexclusive services, intermediaries earn positive profits; the most profitable equilibrium with
both firms serving everyone has the first source charging a lower transaction fee than the second source,
tᴵ < tᴱ (Proposition 4, pp. 317–318), and a dominant firm's profit is positive but below the total marginal cost c
(Proposition 5, p. 318). Entrants use "divide and conquer" pricing, which with multihoming makes it "easier to
'divide' but more difficult to 'conquer'" (p. 310).

## Headline results

| Test | Estimate | 95% CI | N |
|---|---|---|---|
| Share of Lyft's cars also driving for Uber, 2025 monthly mean | 84.7% | | 12 months |
| Share of all app cars on both apps, 2025 monthly mean | 56.9% | | 12 months |
| Juno trips per car ÷ Uber's (Newey–West) | 0.205 | 0.135 to 0.313 | 45 months |
| Lyft trips per car ÷ Uber's (Newey–West) | 0.477 | 0.452 to 0.504 | 134 months |
| Uber − Lyft cut, same zone-month, 2019–2021 | −0.0881 | −0.0920 to −0.0842 | 17,806 cells |
| Uber − Lyft cut, same zone-month, 2023–2026 | +0.0008 | −0.0081 to +0.0098 | 23,090 cells |
| Uber − Lyft cut, same zone-month, all months | −0.0278 | −0.0343 to −0.0214 | 47,024 cells |
| Juno − Uber subsidized share, Feb–Oct 2019 | −0.0455 | −0.0674 to −0.0236 | 6,324 cells |
| Lyft operating margin, 2017–2025 cumulative | −29.0% | | 9 years |

## Data

All files were downloaded on November 1, 2026 by `src/build_data.py`.

| File | Source | Content |
|---|---|---|
| `data/raw/tlc_data_reports_monthly.csv` | TLC, nyc.gov/assets/tlc/downloads/csv/data_reports_monthly.csv | Distinct vehicles doing any High Volume (app) trip per month |
| `data/raw/fhv_base_aggregate_app_companies.csv` | NYC Open Data, FHV Base Aggregate Report (2v9c-2k7f), rows UBER, LYFT, JUNO, VIA | Trips and distinct vehicles per company per month, January 2015 to May 2026 |
| `data/raw/taxi_zone_lookup.csv` | TLC taxi zone lookup, d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv | Pickup zone to borough |
| `data/raw/lyft_10k_facts.csv` | Inline XBRL of Lyft's 10-K filings, accessions 0001759509-20-000009, 0001759509-23-000028, 0001628280-26-006960, from investor.lyft.com | Annual revenue, costs, operating and net income, 2017–2025 |
| `data/processed/trips_platform_month_zone.csv` | TLC High Volume FHV trip records, `fhvhv_tripdata_YYYY-MM.parquet`, February 2019 to September 2026 | Trips, fare, driver pay, tips, miles, seconds and subsidized trips by company, month and pickup zone |
| `data/processed/trips_platform_month_hour.csv` | Same | The same by hour of pickup |
| `data/processed/trips_platform_month_dist.csv` | Same | Percentiles of the per-trip cut by company and month |
| `data/processed/trips_build_log.csv` | Same | Rows read, dropped and kept per monthly file |

The 92 trip files total about 46 GB and are not committed; `build_data.py` downloads, reduces and deletes them one
at a time. The SEC's EDGAR servers refused requests from this machine on the download date, so the Lyft filings
were taken from the copies on Lyft's investor-relations site, which serves the same filed documents.

## Method

The rules below were fixed before the tests were run.

- **Trips.** Keep trips by the four app companies (TLC licenses HV0002 Juno, HV0003 Uber, HV0004 Via, HV0005 Lyft).
  Drop pooled requests (`shared_request_flag = Y`) and trips with non-positive base fare, driver pay, miles or time.
- **Cut.** The cut uses the base passenger fare, which excludes tolls, tips, taxes, the Black Car Fund charge and
  congestion and airport surcharges:

```math
\tau_{kzt} = 1 - \frac{\sum_{j \in (k,z,t)} D_j}{\sum_{j \in (k,z,t)} F_j}, \qquad \text{subsidized}_j = \mathbf{1}\{D_j > F_j\}
```

- **Multihoming.** With $`K`$ companies active, $`m_t = (\sum_k V_{kt} - V_t)/V_t`$. With $`K = 2`$ this is the
  share of cars on both apps; with $`K > 2`$ it is an upper bound.
- **Divide and conquer.** For each entrant, the monthly log gap in trips per vehicle against Uber, with mean and
  Newey–West standard errors with 12 lags:

```math
g_{kt} = \ln\frac{T_{kt}}{V_{kt}} - \ln\frac{T_{\text{Uber},t}}{V_{\text{Uber},t}} = \delta_k + u_{kt}, \qquad H_0:\ \delta_k = 0
```

- **First source.** Weighted least squares with zone × month fixed effects, absorbed by within-cell demeaning,
  weights equal to trips, cells with at least 100 trips per company, standard errors clustered by pickup zone
  (robustness: clustered by month; hour-of-day × month cells):

```math
\tau_{kzt} = \beta \, \mathbf{1}\{k = \text{Uber}\} + \gamma_{zt} + \varepsilon_{kzt}, \qquad H_0:\ \beta = 0,\quad \text{Proposition 4: } \beta < 0
```

- **Periods.** 2019–2021 has three or four apps (Juno until November 2019, Via until late 2021); 2023–2026 has two.
  2022 is reported by itself as the first full two-app year.
- **Profit.** Lyft's operating income ÷ revenue from the 10-K inline XBRL; where a year appears in more than one
  filing, the latest filing's value is used (no values differed). The fiscal 2019 filing tags revenue as
  `RevenueFromContractWithCustomerExcludingAssessedTax`; later filings use `Revenues`.

## Full test statistics

| Test | Difference | SE | p | Cells |
|---|---|---|---|---|
| Uber − Lyft cut, 2019 | −0.1052 | 0.0034 | < 0.001 | 5,600 |
| Uber − Lyft cut, 2020 | −0.0672 | 0.0027 | < 0.001 | 6,074 |
| Uber − Lyft cut, 2021 | −0.0882 | 0.0017 | < 0.001 | 6,132 |
| Uber − Lyft cut, 2022 | −0.0196 | 0.0013 | < 0.001 | 6,128 |
| Uber − Lyft cut, 2023 | +0.0210 | 0.0032 | < 0.001 | 6,160 |
| Uber − Lyft cut, 2024 | −0.0069 | 0.0053 | 0.19 | 6,156 |
| Uber − Lyft cut, 2025 | +0.0125 | 0.0051 | 0.015 | 6,148 |
| Uber − Lyft cut, 2026 (Jan–Sep) | −0.0295 | 0.0048 | < 0.001 | 4,626 |
| Uber − Lyft cut, all months, month clusters | −0.0278 | 0.0051 | < 0.001 | 47,024 |
| Uber − Lyft cut, hour × month cells, month clusters | −0.0158 | 0.0055 | 0.004 | 4,416 |
| Uber − Lyft subsidized share, all months | +0.0778 | 0.0030 | < 0.001 | 47,024 |
| Lyft − Uber subsidized share, Feb–Oct 2019 | −0.2418 | 0.0052 | < 0.001 | 6,324 |
| Juno − Uber cut, Feb–Oct 2019 | +0.0310 | 0.0042 | < 0.001 | 6,324 |
| Lyft − Uber cut, Feb–Oct 2019 | +0.1108 | 0.0025 | < 0.001 | 6,324 |
| Via trips per car ÷ Uber's (log gap) | −0.229 | 0.280 | 0.41 | 79 months |

Uber's annual cut rose from 9.5% (2019) to 24.2% (2025); Lyft's was 19.2% and 20.9%. Uber's subsidized share was
33.2% in 2019 and 14.6% in 2025. Lyft's operating margin was −59.1% over 2017–2021 and −10.9% over 2022–2025.

## Reproducing the results

```bash
pip install -r requirements.txt
python src/build_data.py --skip-trips       # small files only; the committed data/processed/ is enough
python src/chicken_egg.py
python src/platform_profits.py
```

`python src/build_data.py --force` rebuilds `data/processed/` from the 92 trip files (about 46 GB of downloads,
roughly 90 minutes). The small files are re-downloaded, so later TLC revisions can change the counts slightly.

## References

- Armstrong, M. (2006). Competition in two-sided markets. *RAND Journal of Economics* 37(3), 668–691.
- Caillaud, B. & Jullien, B. (2001). Competing cybermediaries. *European Economic Review* 45(4–6), 797–808.
- Caillaud, B. & Jullien, B. (2003). Chicken & egg: competition among intermediation service providers. *RAND
  Journal of Economics* 34(2), 309–328.
- Jullien, B. (2011). Competition in multi-sided markets: divide and conquer. *American Economic Journal:
  Microeconomics* 3(4), 186–220.
- Rochet, J.-C. & Tirole, J. (2003). Platform competition in two-sided markets. *Journal of the European Economic
  Association* 1(4), 990–1029.
- New York City Taxi and Limousine Commission. High Volume FHV trip record data dictionary (March 18, 2025);
  driver pay standard, Industry Notice 19-02 (January 11, 2019).
