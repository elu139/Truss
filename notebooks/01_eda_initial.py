# ---
# Initial EDA — H&M Personalized Fashion Recommendations
#
# This file uses the "# %%" cell-marker format. Open it in JupyterLab,
# VSCode (Python extension), or PyCharm and you'll get notebook-style cells.
# It's tracked as a .py for clean git diffs (no JSON, no embedded outputs).
#
# Goals of this pass:
#   1. Confirm the data loaded correctly and we understand the schema.
#   2. Get a feel for the shape of each table (rows, columns, dtypes, nulls).
#   3. Look at three things that drive every recsys decision later:
#        - Item popularity distribution (long-tail check)
#        - Customer activity distribution (heavy users vs lurkers)
#        - Temporal coverage (train/eval split sanity)
#   4. Spot-check the categorical fields we'll use as features
#      (product type, color, customer age, club status).
#
# What we DON'T do here:
#   - Session reconstruction (Step 4 — needs simulated events)
#   - Feature engineering (Step 5)
#   - Train/test splitting (will live in src/truss/data/)
#
# This is the "do I trust this data" pass, not the "extract signal" pass.
# ---

# %% [imports + paths]
from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl
import seaborn as sns

PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
RAW = PROJECT_ROOT / "data" / "raw"

sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (10, 4)

print(f"Project root: {PROJECT_ROOT}")
print(f"Raw data dir: {RAW}")
print(f"Files present: {sorted(p.name for p in RAW.iterdir() if p.is_file())}")

# %% [load tables]
# Polars throughout — transactions is ~30M rows, well beyond comfortable pandas territory.
# Smaller files could use pandas, but uniformity beats micro-optimization here.

articles = pl.read_csv(RAW / "articles.csv")
customers = pl.read_csv(RAW / "customers.csv")
transactions = pl.read_csv(
    RAW / "transactions_train.csv",
    schema_overrides={"article_id": pl.Utf8},  # keep leading zeros
    try_parse_dates=True,
)

print(f"articles:     {articles.shape}")
print(f"customers:    {customers.shape}")
print(f"transactions: {transactions.shape}")


# %% [schema and dtypes]
print("=== articles ===")
print(articles.schema)
print("\n=== customers ===")
print(customers.schema)
print("\n=== transactions ===")
print(transactions.schema)

# %% [missing values]
def null_report(df: pl.DataFrame, name: str) -> None:
    nulls = df.null_count().row(0)
    cols = df.columns
    nrows = df.height
    print(f"\n--- {name} (n={nrows:,}) ---")
    for col, n in zip(cols, nulls):
        if n > 0:
            print(f"  {col:35s}  {n:>10,}  ({100*n/nrows:5.1f}%)")

null_report(articles, "articles")
null_report(customers, "customers")
null_report(transactions, "transactions")
# WHY THIS MATTERS: nulls in customers.age affect age-segmentation features.
# Nulls in articles fields might force us to drop or impute for content-based recs.

# %% [temporal coverage]
date_range = transactions.select([
    pl.col("t_dat").min().alias("first"),
    pl.col("t_dat").max().alias("last"),
])
print(date_range)

daily = (
    transactions
    .group_by("t_dat")
    .agg(pl.len().alias("n_tx"))
    .sort("t_dat")
)
print(f"Days covered: {daily.height}")
print(f"Median daily tx: {daily['n_tx'].median():,.0f}")

ax = daily.to_pandas().plot(x="t_dat", y="n_tx", legend=False, title="Daily transactions")
ax.set_ylabel("transactions / day")
plt.tight_layout()
plt.show()
# WHY THIS MATTERS: confirms the train window per the Kaggle comp (2018-09-20 → 2020-09-22)
# and gives us the cadence for building the 24h/7d/30d horizons (scope §5).

# %% [item popularity — the long tail]
item_pop = (
    transactions
    .group_by("article_id")
    .agg(pl.len().alias("n_purchases"))
    .sort("n_purchases", descending=True)
)
print(f"Unique articles purchased: {item_pop.height:,} of {articles.height:,} in catalog "
      f"({100*item_pop.height/articles.height:.1f}%)")
print(f"Median purchases per article: {item_pop['n_purchases'].median():,.0f}")
print(f"99th-percentile purchases:    {item_pop['n_purchases'].quantile(0.99):,.0f}")

# Log-scale to see the long tail.
fig, ax = plt.subplots(figsize=(10, 4))
ax.loglog(range(1, item_pop.height + 1), item_pop["n_purchases"].to_list())
ax.set_xlabel("article rank (popularity)")
ax.set_ylabel("purchases (log)")
ax.set_title("Item popularity — long tail check")
plt.tight_layout()
plt.show()
# WHY THIS MATTERS: confirms (or refutes) the assumption that fashion has a heavy long tail.
# If yes — popularity baseline alone underserves most users; content-based and CF earn their keep.
# This is also why catalog coverage (metrics §2.2) is a non-trivial metric.

# %% [customer activity distribution]
cust_act = (
    transactions
    .group_by("customer_id")
    .agg(pl.len().alias("n_purchases"))
    .sort("n_purchases", descending=True)
)
print(f"Unique customers with ≥1 tx: {cust_act.height:,} of {customers.height:,} "
      f"({100*cust_act.height/customers.height:.1f}%)")
print(f"Median tx per active customer: {cust_act['n_purchases'].median():,.0f}")
print(f"Customers with 1 tx only:      "
      f"{cust_act.filter(pl.col('n_purchases') == 1).height:,} "
      f"({100*cust_act.filter(pl.col('n_purchases') == 1).height/cust_act.height:.1f}%)")

fig, ax = plt.subplots()
ax.hist(cust_act["n_purchases"].to_list(), bins=range(1, 50), edgecolor="white")
ax.set_xlabel("purchases per customer (capped at 50 for plot)")
ax.set_ylabel("# customers")
ax.set_title("Customer activity distribution")
plt.tight_layout()
plt.show()
# WHY THIS MATTERS: lots of one-shot customers means cold-start dominates the
# "returning session" persona (scope §3). The popularity baseline will look
# artificially strong on single-purchase customers — we need to evaluate
# separately by activity level.

# %% [article categoricals]
print("Top 15 product_type_name:")
print(
    articles.group_by("product_type_name")
    .agg(pl.len().alias("n"))
    .sort("n", descending=True)
    .head(15)
)

print("\nTop 15 colour_group_name:")
print(
    articles.group_by("colour_group_name")
    .agg(pl.len().alias("n"))
    .sort("n", descending=True)
    .head(15)
)

print("\nIndex/department coverage:")
print(
    articles.group_by("index_name")
    .agg(pl.len().alias("n_articles"))
    .sort("n_articles", descending=True)
)
# WHY THIS MATTERS: product_type / colour will likely seed ILD (metrics §2.1)
# as a fallback similarity until we have learned embeddings (Step 8).

# %% [customer attributes]
print("Customer age distribution:")
print(customers.select(pl.col("age").describe()))

print("\nClub member status:")
print(customers.group_by("club_member_status").agg(pl.len().alias("n")).sort("n", descending=True))

print("\nFashion news frequency:")
print(customers.group_by("fashion_news_frequency").agg(pl.len().alias("n")).sort("n", descending=True))

fig, ax = plt.subplots()
ax.hist(customers["age"].drop_nulls().to_list(), bins=range(15, 90), edgecolor="white")
ax.set_xlabel("age")
ax.set_ylabel("# customers")
ax.set_title("Customer age distribution")
plt.tight_layout()
plt.show()
# WHY THIS MATTERS: age is the only demographic we have. Scope §5 commits us to
# using it ONLY in aggregate / coarse buckets (not as a personal identifier).
# This plot tells us what bucket boundaries make sense (e.g., 16-25, 26-35, ...).

# %% [coverage cross-checks]
# How many catalog items are *never* purchased in the training window?
purchased = item_pop["article_id"].unique()
never_purchased = articles.filter(~pl.col("article_id").is_in(purchased))
print(f"Articles never purchased in train: {never_purchased.height:,} "
      f"({100*never_purchased.height/articles.height:.1f}%)")

# How many customers have ZERO transactions?
active = cust_act["customer_id"].unique()
inactive = customers.filter(~pl.col("customer_id").is_in(active))
print(f"Customers with zero transactions:  {inactive.height:,} "
      f"({100*inactive.height/customers.height:.1f}%)")
# WHY THIS MATTERS: the truly-inactive customers are exactly the "anonymous"
# persona at training time. We can use them as a synthetic cold-start pool for
# evaluating Scenario A (homepage rail).

# %% [summary]
print("=" * 60)
print("INITIAL EDA SUMMARY")
print("=" * 60)
print(f"  Articles in catalog:           {articles.height:>12,}")
print(f"  Articles ever purchased:       {item_pop.height:>12,}  ({100*item_pop.height/articles.height:.1f}%)")
print(f"  Customers in customers.csv:    {customers.height:>12,}")
print(f"  Active customers (≥1 tx):      {cust_act.height:>12,}  ({100*cust_act.height/customers.height:.1f}%)")
print(f"  Total transactions:            {transactions.height:>12,}")
print(f"  Date range:                    {transactions['t_dat'].min()} → {transactions['t_dat'].max()}")
print()
print("Findings that affect downstream design:")
print("  • Long-tail item popularity — popularity baseline alone is insufficient.")
print("  • Heavy share of single-purchase / inactive customers — cold-start dominates.")
print("  • product_type + colour_group are usable fallback similarity fields for ILD.")
print("  • customer.age is the only useful demographic — bucket coarsely per scope §5.")
print("  • Date range fits cleanly with the 24h/7d/30d horizon split.")
