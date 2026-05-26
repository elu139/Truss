# Truss — Project Scope

> **Status:** Draft. This document locks in the *product* before the *engineering*. Once we agree on these answers, every downstream choice (which baselines, which features, which metrics) follows.

## 1. TL;DR

Truss is a **trust-aware fashion recommendation system** built on the H&M Personalized Fashion Recommendations dataset.

Where mainstream recommenders maximize short-term clicks, Truss treats **user trust**, **ad fatigue**, **recommendation diversity**, and **explainability** as first-class objectives alongside relevance. The thesis is that you can produce equally relevant recommendations *without* a persistent identity graph, and that doing so improves long-term engagement — a hypothesis we test through simulation.

## 2. Domain

**Choice:** H&M fashion e-commerce.

**Dataset:** [H&M Personalized Fashion Recommendations](https://www.kaggle.com/c/h-and-m-personalized-fashion-recommendations) — ~30M transactions over 2018-09 → 2020-09, ~105K articles, ~1.4M customers, customer attributes (age, postal region, club status), article metadata (product type, color, dept, section, garment group), text descriptions, and item images.

**Why fashion:**
- Catalog size is bounded (~100K items) — fits a solo project.
- Rich multi-modal signal: tabular + text + image.
- "Creepy retargeting" is the canonical real-world failure mode of fashion ads — strong narrative for the trust framing.
- Dataset is clean, well-documented, and recruiter-recognized.

## 3. Target Users (Personas)

Truss serves three states of the same shopper — we model them differently because each has a different signal budget.

| State | What we know | What we don't | Primary recsys challenge |
|---|---|---|---|
| **Anonymous visitor** | Device, time of day, coarse locale, current session click trail | Identity, history | Cold start; popularity + content similarity dominate |
| **Returning session** | Last N sessions of behavior (short window only) | Long-term identity, cross-device | Session-based / sequential recs |
| **Known customer** | Transactional history, demographics (age, club status) | Anything not in H&M's own data | Collaborative filtering, but with fatigue-aware reranking |

Critically: even for "known customers," Truss intentionally **does not build a long-lived behavioral fingerprint**. We use the H&M customer ID as a lookup key for *purchase history* only — not as the basis for inferred psychographic profiles. This is what makes us "privacy-aware" rather than just "less invasive."

## 4. Recommendation Scenarios

The H&M dataset doesn't tell us *where* recommendations get shown — that's a product decision we make. Picking too many scenarios fragments the project; picking too few makes the trust story weak. I propose **two scenarios** that together exercise the full system:

### Scenario A — Homepage "For You" rail (anonymous + returning)
- **User state:** anonymous or returning, no purchase necessarily intended.
- **Recsys job:** rank 12 items the user is most likely to engage with from a catalog of ~100K.
- **Privacy angle:** cold-start without ID-graph leakage. Uses only session signals + popularity + coarse demographics.
- **Why it matters:** this is where the "creepy ad" feeling is born. Get it right and the user feels seen but not surveilled.

### Scenario B — Post-purchase reranking ("you bought X, here's what comes next")
- **User state:** known customer who just purchased.
- **Recsys job:** what 12 items to suggest next — *without* hammering them with near-duplicates of what they just bought.
- **Privacy angle:** this is where fatigue modeling shines. The naive system shows "more black t-shirts" forever. Truss's fatigue model down-weights items too similar to recent purchases/views.
- **Why it matters:** this is the *measurable* trust story. We can simulate "show same item 5x → users disengage" and show our system avoids it.

**Deferred scenarios** (call out in the doc, but don't build): search ranking, email retargeting, cart upsell. These would be Phase-2 extensions in a real product.

## 5. What "Privacy-Aware" Means in Truss

This is the hardest definition in the doc. I'm intentionally narrow — "privacy-aware" can mean a hundred things, so we pick a specific, defensible interpretation.

In Truss, **privacy-aware** means all four of:

1. **No persistent identity-graph features.** We don't build a "user_embedding" that aggregates two years of behavior into a vector and uses it as the primary signal. When we use customer IDs, they're keys into *recent* behavior — windowed at **24 hours, 7 days, and 30 days**. Anything older is intentionally discarded from the live feature set. The three horizons serve different jobs:
   - **24h** — in-session / in-mission intent (what is this user shopping for *right now*).
   - **7d** — short-term taste (what categories or styles they've been gravitating to this week).
   - **30d** — stable seasonal preferences (what fits their broader pattern this season).
2. **Session-first ranking.** A 5-click session must be sufficient to produce meaningful recommendations *without* relying on the customer's long history. This is the "logged-out tomorrow" test.
3. **Fatigue and saturation controls.** Every recommended item carries a fatigue penalty that grows with recent exposures. Items hit a hard impression cap. This prevents the "shown 50x" failure mode.
4. **Per-recommendation explanations.** Every served item has a human-readable reason ("Because you viewed similar minimalist coats" / "Trending among similar shoppers this week"). No recommendation is a black-box surprise.

What **privacy-aware does NOT mean** in this project (to keep scope honest):
- Not differential privacy on training data (deferred — Phase 7 "FAANG-level" feature).
- Not federated learning (same).
- Not end-to-end encryption of the recommendation pipeline.
- Not GDPR-compliance audit — we're modeling the *principles*, not legal certification.

## 6. Success Metrics (high-level)

Full operational definitions go in `docs/metrics_definition.md` (Step 2 deliverable). Here we just commit to the *categories*:

| Category | What it measures | Example metrics |
|---|---|---|
| **Relevance** | Are recommendations the user would actually want? | Recall@12, MAP@12 (H&M comp metric), HitRate@12 |
| **Diversity** | Do recs cover varied items/categories? | Intra-list diversity (ILD), catalog coverage |
| **Novelty** | Are we showing new items, not just the obvious? | Mean item popularity (lower = more novel), serendipity |
| **Trust proxies** | Are we avoiding the "creepy" failure mode? | Fatigue score, repetition rate, impression saturation — computed per 24h / 7d / 30d horizon |
| **Simulated retention** | Would a fatigued user keep engaging? | 7-day simulated re-engagement (via fatigue model) |

The portfolio narrative is built around the comparison: **Baseline (relevance-only) vs Truss (trust-aware)** across all five categories. Truss should win or tie on relevance while strictly beating baselines on diversity, novelty, and trust proxies.

## 7. Out of Scope

Explicit non-goals — prevents scope creep:

- Real-time auction / RTB simulation
- Live A/B testing on real users (we do simulated A/B only)
- Image-based visual search (we use image *features*, not visual query)
- Cross-device identity stitching
- Production-grade SLAs (latency budget is "interactive demo," not "5ms p99")
- Mobile app or native UI (Streamlit dashboard is the demo surface)
- Cold-item cold-start (new items with no metadata — we assume metadata exists)
- Multi-language / localization

## 8. Constraints

- **Time:** soft target 2026-08-20 (~14 weeks).
- **Compute:** laptop + Colab for GPU. No persistent cloud infra.
- **Data:** H&M public dataset. We will synthesize *additional* exposure/fatigue events on top of real transactions (Step 4 in roadmap).
- **Team:** solo developer.
- **Scope discipline:** Phases 1–6 of the 20-step roadmap. Phase 7 features (bandits, RL, federated, DP, GNN) are explicitly deferred.

## 9. Decisions (resolved 2026-05-15)

1. **Two scenarios (A + B):** confirmed — Homepage rail + Post-purchase reranking.
2. **Four-pillar "privacy-aware" definition** (§5): confirmed.
3. **Time horizon:** **multi-horizon — 24h, 7d, 30d.** Each scenario picks which horizon dominates: post-purchase reranker is 24h-weighted; homepage rail blends 7d/30d. Features and trust-proxy metrics will be computed at all three horizons.
4. **MAP@12 as headline relevance metric:** confirmed (matches H&M competition).
5. **Deferred scenarios** (email retargeting, search ranking, cart upsell): confirmed deferred.
