# Truss — Research Basis

The empirical literature that grounds Truss's [core hypothesis](PROJECT_SCOPE.md#1b-core-hypothesis): repeated exposure to similar recommendations degrades user trust and long-term engagement.

**Why this doc exists:** the simulated retention metric in `metrics_definition.md` §5 depends on a fatigue → disengagement function. That function shouldn't use invented effect sizes — it should be parameterized from published research. Every citation below should answer one of: *what is the effect, how large is it, in what domain, what was the methodology?*

Reviewers (and recruiters) reading the case study will want to see this — it's what separates a portfolio project from a hand-wave.

## How to use this doc

When you find a relevant paper:
1. Add it under the appropriate heading below.
2. Include: full citation, one-sentence summary, the *specific quantitative result* you're using, and how it informs Truss (which metric? which threshold? which simulation parameter?).
3. If the paper supplies a number that goes into code (e.g. a decay rate, a fatigue half-life), reference this doc by section in the code comment.

---

## 1. Ad fatigue and exposure-repetition effects

> The claim: repeated impressions of the same/similar ads reduce attention, click probability, and brand affinity.

*(Add citations here as you find them. Suggested search terms: "advertising wear-out," "ad fatigue effect size," "frequency capping," "Schmidt Eisend meta-analysis," "two-factor theory advertising repetition.")*

- **[Placeholder]** —
  - Citation:
  - Effect size:
  - Truss application:

## 2. Banner blindness and attention decay

> The claim: users actively filter out repeated visual patterns even when those patterns contain relevant content.

*(Suggested search: "banner blindness eye tracking," "Benway Lane," "Nielsen Norman banner blindness," modern updates.)*

- **[Placeholder]**

## 3. Recommendation diversity ↔ user satisfaction / retention

> The claim: more diverse recommendation lists yield higher long-term satisfaction even when short-term relevance is comparable.

*(Suggested search: "intra-list diversity user study," "Castells Hurley diversity recsys," "Ziegler topic diversification," "filter bubble retention," "Anderson Diakopoulos diversity.")*

- **[Placeholder]**

## 4. Personalization paradox and the "creepy" threshold

> The claim: personalization improves engagement up to a point, then degrades it as users become aware of surveillance.

*(Suggested search: "personalization privacy paradox," "creepy line advertising," "Aguirre persuasion knowledge," "Tucker personalized advertising effectiveness.")*

- **[Placeholder]**

## 5. Trust, explanation, and transparency in recommenders

> The claim: explanations and transparency increase user trust and willingness to engage with recommendations.

*(Suggested search: "explainable recommendation user study," "Tintarev Masthoff explanation recsys," "Pu Chen evaluating recommender systems.")*

- **[Placeholder]**

## 6. Cognitive load and choice overload in recommendation interfaces

> The claim: too many or too narrowly-personalized recommendations increase decision fatigue and reduce conversion.

*(Suggested search: "Bollen choice overload recommender," "Iyengar Lepper jam study" (foundational), "consumer choice overload meta-analysis.")*

- **[Placeholder]**

---

## Translating research into simulation parameters

Once §1–§6 have real citations, populate this table — it's the bridge from literature to code.

| Simulation parameter | Value | Source (§/citation) | Notes |
|---|---|---|---|
| Daily disengagement probability per unit of `ListFatigue_24h` | TBD | TBD | Feeds `src/truss/eval/retention.py` |
| Fatigue half-life (impressions → effect decays to 50%) | TBD | TBD | Feeds fatigue model in `src/truss/models/` |
| Saturation threshold where attention drops sharply | TBD | TBD | Validates hard cap in metrics §4.2 |
| Diversity → retention slope | TBD | TBD | Sets expected magnitude of Truss's retention lift over baseline |

A defensible project doesn't need every cell filled with a single canonical paper — but it does need every cell to point *somewhere*, and to flag where the literature is thin (and the case study notes that as a limitation).
