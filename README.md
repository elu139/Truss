# Truss

A privacy-aware, trust-modeled fashion recommendation system.

Most product recommenders optimize engagement at all costs — clicks today, churn tomorrow. **Truss** is built on the opposite premise: that user trust, ad fatigue, and recommendation diversity are first-class objectives alongside relevance.

Built on the [H&M Personalized Fashion Recommendations](https://www.kaggle.com/c/h-and-m-personalized-fashion-recommendations) dataset.

## Status

🚧 Early development — Phase 1: Product Definition.

## Stack

- **Data:** pandas, polars, DuckDB
- **Models:** scikit-learn, implicit, LightFM, sentence-transformers, XGBoost
- **Serving:** FastAPI
- **Dashboard:** Streamlit
- **Infra:** Docker, GitHub Actions
- **GPU work:** Google Colab

## Repo layout

```
data/        # raw / processed / external — gitignored
docs/        # scope, metrics, architecture, case study
notebooks/   # EDA and exploration
src/truss/   # importable package: data, features, models, eval, serving
scripts/     # standalone CLIs (data download, training)
tests/       # pytest
```

## Roadmap

See [`initial_idea.txt`](initial_idea.txt) for the full 20-step plan across 7 phases.
