# Methods review of Caillaud and Jullien (2003)

**Paper.** Bernard Caillaud and Bruno Jullien, "Chicken & Egg: Competition among Intermediation Service
Providers," *RAND Journal of Economics* 34(2), Summer 2003, pp. 309–328.

**Statistical focus.** The paper has no data. The results that carry it are Proposition 1 (with exclusive
services the only equilibria have one intermediary serving everyone at zero profit) and Propositions 4 and 5 (with
nonexclusive services, intermediaries earn positive profits, and the most profitable two-firm equilibrium has one
firm with a low transaction fee and one with a high one).

**Review standard.** Internal consistency of the formal results, explicitness of the assumptions, and the
testability of the predictions.

**What was read.** The full published article (JSTOR stable URL 1593720), all twenty pages including the
appendix proofs of Propositions 1, 2 and 4 to 8. The companion working papers cited for omitted proofs (Caillaud
and Jullien 2001a, 2001b) were not read. Some displayed formulas in the copy read were partly illegible; those
are flagged below.

---

## Methods summary

The article is a two-stage game. Two intermediaries ("matchmakers"), I and E, with the same matching technology
set prices first; then a unit mass of buyers and a unit mass of sellers decide which intermediary to register
with. Each agent has exactly one valuable partner on the other side; an intermediary that has both partners in its
database finds the match with probability λ < 1, and matches at two intermediaries succeed or fail independently.
The gross gain from a match is normalized to 1 and is split by bargaining, with shares u₁ < 1/2 < u₂. Each
intermediary can charge each side a registration fee (which may be negative) and a total transaction fee t ≥ 0
when trade occurs. Serving one agent of side i costs cᵢ, with c = c₁ + c₂ < λ.

Because users' choices depend on what they expect others to do, many user allocations can follow any set of
prices. The authors resolve this with two devices: a monotonicity refinement (demand does not rise with one's
own price) and, for deviations, "pessimistic" beliefs against the deviating firm. Exclusive services (register
with at most one intermediary) are treated as a benchmark in Section 2; Section 3 allows multihoming; Section 4
discusses efficiency, profits, consumer welfare, an exclusivity-choice and entry game, and the role of
transaction fees; Section 5 removes transaction fees.

- **Research design.** Formal theory. Equilibrium characterization with existence and nonexistence results.
- **Sampling strategy, sample size, inclusion and exclusion criteria.** Do not apply. There is no sample. The
  introduction motivates the model with examples (esteel.com, portals, auction sites, a quotation from Jeff
  Bezos) but no observations are analyzed.
- **Independent and dependent variables.** In the theory's terms, the exogenous parameters are λ, u₁, u₂, c₁,
  c₂ and whether services are exclusive; the endogenous outcomes are prices (registration and transaction fees),
  the allocation of users across intermediaries, profits and welfare.
- **Statistical methods.** None. The "statistics" are propositions and their proofs.
- **Reported effect sizes.** None in the empirical sense. The propositions give closed-form profit levels and
  bounds, listed in the table.
- **Confidence intervals and p-values.** Do not apply.
- **Missing data treatment.** Does not apply.
- **Stated limitations.** Footnote 5 says efficiency refers only to the size of the externalities generated, with
  no variety gains and no distortion of trade by intermediation prices. Section 2 notes that transaction fees can
  be hard to collect when matched parties can bypass the intermediary, which motivates Section 5. The conclusion
  says the bargaining over the match surplus is held fixed and should be made to depend on the intermediaries'
  strategies, citing Rochet and Tirole (2001).

---

## Statistics extraction table

| Statistic | Value and unit | Source location | What it measures | What it does not establish |
|---|---|---|---|---|
| Dominant-firm profit with exclusive services | 0 (profit), with t = 1 and p₁ + p₂ = c − λ | Proposition 1, p. 314; proof in Appendix | That a monopolizing intermediary is fully disciplined by divide-and-conquer entry when users can register with only one firm | That real exclusive markets earn zero profit; the result relies on pessimistic beliefs, identical technologies and no entry cost |
| Condition for efficient multihoming | λ(1 − λ) > c | Section 3, p. 315; Propositions 3–5 | The extra matching probability from a second registration against its cost | Which side multihomes in practice; the model is symmetric in technology |
| Second-source profit bound | λ(1 − λ) − c per period | Section 3, p. 316; Proposition 2, p. 317 | The most an intermediary can earn as the backup matchmaker | Profits of a firm with a different technology (Section 4 treats λᴱ ≠ λᴵ informally) |
| First- or sole-source deviation profit | λ(1 − λ)u₂ + λ(u₁ + λu₂)tᴱ − c | Proposition 2, p. 317 | The entrant's payoff when it processes every transaction it matches | Equilibrium profits; it is a deviation payoff |
| Global multihoming equilibrium | Exists iff λ(1 − λ) > c; highest-profit equilibrium has tᴵ < tᴱ, each firm earning more than λ(1 − λ) − c | Proposition 4, pp. 317–318 | Endogenous differentiation: one low-fee first source, one high-fee second source | The exact profit expression was partly illegible in the copy read (see below) |
| Dominant-firm profit with multihoming | Positive and strictly below c, attainable with tᴵ = 0 | Proposition 5, p. 318 | That nonexclusivity lets a dominant firm keep a profit bounded by total marginal cost | That dominant platforms set zero transaction fees in practice |
| Market-sharing equilibrium without multihoming | Does not exist for generic costs (one knife-edge value of c excepted) | Proposition 6, p. 318 | Two active firms require some multihoming | Anything about partial multihoming shares |
| Market-sharing equilibrium profit, λ near 1 | An infimum of two expressions in uᵢ, uⱼ, cᵢ, cⱼ (exact form partly illegible), attained with nᴹᵢ = 1, half the single-homers at each firm and tᴵ = tᴱ = 0 | Proposition 8, p. 319 | Upper bound on aggregate profit with symmetric market sharing | Legibility of the exact expression in the copy read is limited |
| Total profit and consumer welfare in global multihoming | Total profit ≥ 2λ(1 − λ) − 2c; consumer welfare ≤ λ² | Footnote 35, p. 320 | That consumers do better under exclusivity (welfare λ − c) than under any nonexclusive equilibrium | A welfare ranking with heterogeneous users or differentiated platforms |
| No-transaction-fee global multihoming profit | λ(1 − λ) − c, symmetric | Proposition 9, p. 322 | Profit when only registration fees are available | Behavior when fees are partly enforceable |
| No-transaction-fee dominant-firm equilibrium | Exists iff c > λ(1 − λ)u₂; maximal profit c | Proposition 10, p. 323 | That banning transaction fees can raise dominant-firm profit | |
| No-transaction-fee market sharing, λ = 1 | Exists iff inf{c₁/u₁, c₂/u₂} < 1/2; maximal profit max{uₕ/2 − cₕ} | Proposition 11, p. 323 | Profit of market sharing without transaction fees | |
| eBay and Aucland final-value fees | eBay 5.25%, 2.75% or 1.5% of price by price band; Aucland 4% | Footnote 12, p. 311 | Contemporary examples of transaction fees, cited as motivation | Any estimate; these are illustrations |

---

## Interpretation notes

- The zero-profit result in Proposition 1 depends on the equilibrium-selection device. A dominant-firm price
  system is required to survive any deviation under beliefs that are as pessimistic as possible for the deviator.
  The authors say so (Section 2 and footnotes 23 and 28). With beliefs favorable to the incumbent the set of
  sustainable profits would differ. This is an explicit modeling choice, not an error.
- The model normalizes the match value to 1 and fixes the bargaining split. Users' utilities depend only on the
  total transaction fee, so the model makes no prediction about how a per-trade fee is divided between the two
  sides. A test that uses one side's price alone is not a test of the model.
- "Profit" in the model is the intermediation margin net of the marginal cost of registering users. It is
  neither accounting profit nor return on capital; fixed costs, development costs and advertising revenue
  (footnote 15 lets advertising enter as a negative cᵢ) are outside the formula.
- The exclusivity-choice discussion in Section 4 is explicitly simplified (pure equilibria only, entrant as second
  source) and its conclusions are stated as illustrations rather than propositions.
- Reporting issue, not an error: proofs of the existence part of Proposition 1 and of several Section 5 results
  are deferred to working papers. The journal article is not self-contained on these points.

---

## Unanswered questions

- How robust are the profit bounds when users are heterogeneous in their value of a match, or when platforms are
  horizontally differentiated? Armstrong (2006) and Rochet and Tirole (2003) take up versions of this.
- With partial multihoming (some users on both, some on one), which equilibrium type applies? The paper's
  equilibria have all-or-nothing multihoming on each side except in the mixed equilibria of Propositions 6 to 8.
- What happens with more than two intermediaries? Footnotes 33 and 34 state that the efficiency and profit
  conclusions extend to K firms, with the proof "available upon request."
- How do registration subsidies and transaction fees behave in a dynamic setting where beliefs evolve? The paper
  is static.

---

## Items requiring expert verification

- The displayed profit expressions in Proposition 4 (p. 318) and Proposition 5 (p. 318) were partly illegible in
  the copy read. This review records only what is stated unambiguously in the text: that the highest-profit
  global multihoming equilibrium has tᴵ < tᴱ with profits above λ(1 − λ) − c, and that the highest dominant-firm
  profit is strictly below c.
- The Proposition 8 approximation (p. 319) is recorded in its general form only.
- The extension of the results to K intermediaries (footnotes 33 and 34) rests on a proof not published in the
  article.

---

## Relation to the rerun in this repository

The repository does not reproduce the paper, which has no data to reproduce. It takes the paper's predictions
for nonexclusive services and checks them against New York City ride-hailing records: whether users multihome,
whether entrants that subsidize one side fail to win the other, and whether the larger platform charges the lower
per-trade fee, as the first-source and second-source equilibrium of Proposition 4 predicts.
