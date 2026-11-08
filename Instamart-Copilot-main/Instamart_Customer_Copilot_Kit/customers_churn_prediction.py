"""Score the September 2025 customer cohort using the internal offline mock."""
from pathlib import Path

import pandas as pd

import mock_llm

ROOT = Path(__file__).resolve().parent
CLEAN = ROOT / "data" / "clean"
OUTPUTS = ROOT / "outputs"
CUTOFF = pd.Timestamp("2025-09-01")
HORIZON_END = pd.Timestamp("2025-10-01")
SCORE_FEATURES = [
    "recency",
    "frequency",
    "monetary",
    "avg_discount",
    "cancellation_rate",
    "avg_delivery",
    "tenure_days",
]


def build_customer_cohort() -> pd.DataFrame:
    """Build pre-September features and the observed September churn label."""
    required_files = [CLEAN / "customers.csv", CLEAN / "orders.csv"]
    missing_files = [path for path in required_files if not path.exists()]
    if missing_files:
        missing = ", ".join(str(path) for path in missing_files)
        raise FileNotFoundError(
            f"Clean project data is missing: {missing}. Run `python run_project.py` first."
        )

    customers = pd.read_csv(CLEAN / "customers.csv")
    orders = pd.read_csv(CLEAN / "orders.csv", parse_dates=["order_ts"])
    history = orders[orders["order_ts"] < CUTOFF].copy()
    completed = history[history["status"].eq("completed")].copy()

    cohort = completed.groupby("customer_id").agg(
        last_order=("order_ts", "max"),
        frequency=("order_id", "nunique"),
        monetary=("order_amount", "sum"),
        avg_discount=("discount_pct", "mean"),
        avg_delivery=("delivery_minutes", "mean"),
    ).reset_index()
    if cohort.empty:
        raise ValueError("No completed pre-September orders are available to build churn features.")

    cohort["recency"] = (CUTOFF - cohort.pop("last_order")).dt.days

    outcomes = (
        history[history["status"].isin(["completed", "cancelled"])]
        .groupby("customer_id")["status"]
        .agg(
            total_orders="count",
            cancelled_orders=lambda values: values.eq("cancelled").sum(),
        )
        .reset_index()
    )
    cohort = cohort.merge(outcomes, on="customer_id", how="left", validate="one_to_one")
    cohort["cancellation_rate"] = (
        cohort["cancelled_orders"] / cohort["total_orders"].clip(lower=1)
    )

    cohort = cohort.merge(customers, on="customer_id", how="left", validate="one_to_one")
    cohort["signup_date"] = pd.to_datetime(cohort["signup_date"], errors="raise")
    cohort["tenure_days"] = (CUTOFF - cohort["signup_date"]).dt.days

    september_orders = orders[
        orders["order_ts"].ge(CUTOFF)
        & orders["order_ts"].lt(HORIZON_END)
        & orders["status"].eq("completed")
    ]
    active_customers = set(september_orders["customer_id"])
    cohort["actual_churned_in_september_2025"] = (
        ~cohort["customer_id"].isin(active_customers)
    ).astype(int)
    return cohort


def predict_customer_churn() -> tuple[pd.DataFrame, dict[str, str]]:
    """Score each cohort customer via mock_llm and save scores and observed labels."""
    cohort = build_customer_cohort()
    observed_churn = cohort["actual_churned_in_september_2025"]
    numeric_features = cohort[SCORE_FEATURES].apply(pd.to_numeric, errors="coerce")
    medians = numeric_features.median()
    if medians.isna().any():
        invalid = ", ".join(medians.index[medians.isna()])
        raise ValueError(f"Cannot score churn because these features have no valid values: {invalid}")
    numeric_features = numeric_features.fillna(medians)

    scores = [
        mock_llm.predict_churn(row)
        for row in numeric_features.to_dict(orient="records")
    ]
    results = pd.DataFrame(
        {
            "customer_id": cohort["customer_id"],
            "churn_probability": [score["churn_probability"] for score in scores],
            "predicted_churn": [score["predicted_churn"] for score in scores],
            "risk_level": [score["risk_level"] for score in scores],
            "actual_churned_in_september_2025": observed_churn.to_numpy(),
        }
    ).sort_values(
        ["churn_probability", "customer_id"], ascending=[False, True]
    ).reset_index(drop=True)

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUTS / "customers_churn_prediction.csv"
    results.to_csv(output_path, index=False)
    print(f"Saved {len(results):,} customer scores to {output_path}")
    return results, {"scoring_method": "internal deterministic mock_llm heuristic"}


if __name__ == "__main__":
    predict_customer_churn()
