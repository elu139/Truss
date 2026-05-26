# Truss — Metrics Definition

Operational definitions for every metric Truss reports. Each metric has: what it measures, the math, units/range, direction (↑/↓ better), why we care, and where it lives in the codebase.

This doc is the contract that evaluation code in `src/truss/eval/` implements. If a number gets reported on the dashboard or in the case study, its definition lives here.

## Notation

- $u$ — user (anonymous session ID *or* customer ID, depending on scenario)
- $i$ — item (H&M `article_id`)
- $R_u$ — list of items recommended to $u$ (length $K$, typically $K=12$)
- $T_u$ — ground-truth relevant items for $u$ (purchases in the eval window)
- $E_{u,i,w}$ — number of impressions of item $i$ shown to user $u$ within time window $w \in \{24h, 7d, 30d\}$
- $\mathcal{C}$ — full item catalog
- $\text{sim}(i, j) \in [0, 1]$ — content similarity between items (cosine on item features)

## Ground truth and the relevance vs. trust split

A subtle but important point about how we evaluate Truss:

- **Relevance metrics** (Recall, MAP, HitRate) score recommendations against **real H&M purchases** held out from training. This is the same ground truth as the Kaggle competition — purchases in the final 7 days of the dataset.
- **Trust / fatigue / diversity metrics** score recommendations against **synthesized impression events** (generated in Step 4 of the roadmap). H&M's public data only includes purchases — no impressions or clicks. We have to simulate the "this user was shown item X five times this week" signal in order to evaluate trust.

Call this out in the case study: relevance is empirical; trust is simulated under stated assumptions. The comparison "baseline vs Truss" is fair because both systems are evaluated against the same simulated exposure stream.

---

## 1. Relevance metrics

### 1.1 Recall@K

$$\text{Recall@K}(u) = \frac{|R_u^{(K)} \cap T_u|}{|T_u|}, \quad \text{Recall@K} = \frac{1}{|U|} \sum_u \text{Recall@K}(u)$$

- **Range:** [0, 1] — ↑ better
- **What it measures:** what fraction of the user's real purchases did we surface in the top K?
- **Why we care:** the "did we find them" baseline. Insensitive to ranking order within top-K.
- **Caveat:** treats positions 1 and K identically — use MAP if order matters.

### 1.2 MAP@12 (headline metric)

Average Precision @ K for one user, with $\text{rel}(k) = 1$ if the $k$-th rec is in $T_u$:

$$\text{AP@K}(u) = \frac{1}{\min(K, |T_u|)} \sum_{k=1}^{K} \text{Precision@k}(u) \cdot \text{rel}(k)$$

$$\text{MAP@K} = \frac{1}{|U|} \sum_u \text{AP@K}(u)$$

- **Range:** [0, 1] — ↑ better
- **What it measures:** position-weighted precision; relevant items higher up score more.
- **Why we care:** **this is the H&M Kaggle competition's official metric** — lets us benchmark against public leaderboards.
- **K = 12** by convention (H&M comp default).

### 1.3 HitRate@K

$$\text{HitRate@K} = \frac{1}{|U|} \sum_u \mathbb{1}[|R_u^{(K)} \cap T_u| > 0]$$

- **Range:** [0, 1] — ↑ better
- **What it measures:** fraction of users for whom we found at least one relevant item.
- **Why we care:** most interpretable for a non-ML audience ("we hit something for X% of users").

---

## 2. Diversity & coverage

### 2.1 Intra-List Diversity (ILD)

For one user's rec list $R_u^{(K)}$:

$$\text{ILD}(R_u) = \frac{2}{K(K-1)} \sum_{i, j \in R_u, i < j} (1 - \text{sim}(i, j))$$

Averaged across users.

- **Range:** [0, 1] — ↑ better
- **What it measures:** how varied a single rec list is (pairwise dissimilarity).
- **Similarity function:** cosine on a fixed item feature vector (content embeddings from Step 8, falling back to one-hot on product type/dept/color before then).
- **Why we care:** prevents "all 12 recs are black t-shirts." Direct anti-monoculture metric.

### 2.2 Catalog Coverage

$$\text{Coverage} = \frac{|\bigcup_u R_u|}{|\mathcal{C}|}$$

- **Range:** [0, 1] — ↑ better
- **What it measures:** what fraction of the catalog the system *ever* recommends.
- **Why we care:** if a system only ever recommends the top-1000 items, it's not personalizing — it's hammering the head. Coverage forces the system to use the long tail.

---

## 3. Novelty

### 3.1 Mean Item Popularity (lower is more novel)

For item $i$, let $p(i)$ = number of users who purchased $i$ / total users in training data.

$$\text{Novelty}(R_u) = \frac{1}{K} \sum_{i \in R_u} -\log_2 p(i)$$

Averaged across users.

- **Range:** [0, $\log_2|U|$] — ↑ more novel
- **What it measures:** the rarer the recommended items, the higher the novelty score.
- **Why we care:** distinguishes systems that "personalize" by just predicting popular items from systems that actually find niche fit.

### 3.2 Serendipity@K

$$\text{Serendipity@K}(u) = \frac{|\{i \in R_u : i \in T_u \text{ and } \text{sim}(i, H_u) < \tau\}|}{K}$$

where $H_u$ is the user's purchase history and $\tau$ is a similarity threshold (default 0.5).

- **Range:** [0, 1] — ↑ better
- **What it measures:** items that are **relevant AND unexpected** — different from what the user has bought before.
- **Why we care:** the "surprise me" axis. Helps the system avoid filter-bubble dynamics.
- **Caveat:** serendipity has many definitions in the literature; we pick this one (relevant ∩ low-similarity-to-history) for clarity. Document the choice in the case study.

---

## 4. Trust proxies (the Truss differentiator)

All trust metrics are reported at **three horizons** — 24h, 7d, 30d — per the scope doc decision. Each captures a different abuse mode.

### 4.1 Repetition Rate (per horizon $w$)

$$\text{RepRate}_w(u) = \frac{|\{i \in R_u : E_{u, i, w} \geq 1\}|}{K}$$

- **Range:** [0, 1] — ↓ better
- **What it measures:** fraction of current recs that the user has *already seen* in window $w$.
- **Per-horizon meaning:**
  - **24h:** are we re-showing items from this session? (Usually want this very low.)
  - **7d:** are we cycling the same items all week?
  - **30d:** are we ever giving the user something new?

### 4.2 Impression Saturation (per horizon $w$)

$$\text{Saturation}_w(u) = \max_{i \in R_u} E_{u, i, w}$$

Reported as a distribution across users (median, p95, max).

- **Range:** [0, ∞) — ↓ better
- **What it measures:** the most-shown single item in window $w$. Detects the "we showed this same coat 30 times" failure mode that a mean wouldn't catch.
- **Hard cap policy:** Truss enforces $\text{Saturation}_{24h} \leq 3$, $\text{Saturation}_{7d} \leq 8$ via the reranker (these are the policy levers).

### 4.3 Fatigue Score (per horizon $w$)

A learned model output:

$$\text{Fatigue}_w(u, i) = P(\text{user disengages with } i \mid \text{exposure history at horizon } w)$$

- **Range:** [0, 1] — ↓ better when *reported* (high fatigue is bad). The reranker *uses* fatigue as a penalty (multiplicatively or additively on relevance score).
- **Model:** XGBoost or logistic regression (Step 11). Features: $E_{u, i, 24h}$, $E_{u, i, 7d}$, $E_{u, i, 30d}$, recency, item popularity, category-level exposure counts.
- **Labels:** synthesized skip / non-engagement events from the simulated exposure stream.
- **Why we care:** this is the *active* trust signal — not just a passive measurement but an input to ranking.

### 4.4 Mean Fatigue per Recommendation List

$$\text{ListFatigue}_w(R_u) = \frac{1}{K} \sum_{i \in R_u} \text{Fatigue}_w(u, i)$$

The summary stat we plot vs. relevance to show the relevance/trust tradeoff curve.

---

## 5. Simulated Retention

The capstone metric — does avoiding fatigue actually improve long-term engagement?

### 5.1 7-day Simulated Re-engagement

Setup:
- Simulate 7 days of daily sessions per user.
- On each day, the user is shown $K$ recs from the system being evaluated.
- Daily session-end probability is a function of $\text{ListFatigue}_{24h}$: higher fatigue → higher probability of disengaging permanently for the rest of the simulation.

$$\text{SimRetention} = \frac{|\text{users still active on day 7}|}{|\text{users active on day 1}|}$$

- **Range:** [0, 1] — ↑ better
- **Why we care:** ties trust directly to a business outcome (retention). The story: "engagement-only baseline gets X% retention; trust-aware Truss gets X+5%."
- **Caveat:** retention is *simulated under stated assumptions about how fatigue causes disengagement*. We document the simulation parameters and run sensitivity analysis in the case study.
- **Hypothesis grounding:** the fatigue → disengagement link is the project's [core hypothesis](PROJECT_SCOPE.md#1b-core-hypothesis). Empirical support (ad fatigue research, banner blindness, diversity-retention studies) is collected in [`research_basis.md`](research_basis.md). The simulation's disengagement function should be parameterized using effect sizes from those studies, not invented numbers — the case study cites them explicitly.

---

## 6. Reporting conventions

- **K = 12** for all top-K metrics (matches H&M comp).
- **All trust metrics** reported at all three horizons (24h / 7d / 30d) in tables; the dashboard defaults to 7d.
- **Reported precision:** relevance metrics to 4 decimals (consistent with H&M leaderboard); trust metrics to 3 decimals.
- **Per-segment breakdowns** for the case study: anonymous / returning / known customer (the three personas from scope §3).

## 7. What lives where

| Module | Metrics |
|---|---|
| `src/truss/eval/relevance.py` | Recall@K, MAP@K, HitRate@K |
| `src/truss/eval/diversity.py` | ILD, Coverage |
| `src/truss/eval/novelty.py` | Mean popularity novelty, Serendipity |
| `src/truss/eval/trust.py` | RepRate, Saturation, Fatigue (uses model from `src/truss/models/`), ListFatigue |
| `src/truss/eval/retention.py` | Simulated 7-day retention |

A single `src/truss/eval/report.py` orchestrates: takes recs + ground truth + impression stream → returns one results dataframe with every metric for every horizon. That dataframe is the input to the dashboard.
