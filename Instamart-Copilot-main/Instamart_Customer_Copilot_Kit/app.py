"""Streamlit dashboard for the local Instamart customer copilot teaching kit."""
from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st

import os
import subprocess
import sys  # <-- 1. Make sure sys is imported at the top

# 1. Establish absolute baseline directories relative to this app.py file
ROOT = Path(__file__).resolve().parent
SCRIPT_PATH = ROOT / "run_project.py"

# 2. Set the actual database and output paths your app uses
DB_PATH = ROOT / "data" / "instamart.db"
SEGMENTS_PATH = ROOT / "outputs" / "customer_segments.csv"
CHURN_PREDICTIONS_PATH = ROOT / "outputs" / "customers_churn_prediction.csv"
SQL_QUERIES_PATH = ROOT / "sql" / "queries.sql"

# 3. Check for the missing database once. If missing, generate it dynamically.
if not DB_PATH.exists():
    print("Database file missing. Running run_project.py setup script...")
    if SCRIPT_PATH.exists():
        # 2. Change "python" to sys.executable so it copies the active venv environment pathways
        subprocess.run([sys.executable, SCRIPT_PATH.as_posix()], check=True)
    else:
        raise FileNotFoundError(f"Setup script not found at {SCRIPT_PATH}")

st.set_page_config(
    page_title="Instamart | Customer Copilot",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --ink: #17231f;
        --muted: #78847e;
        --green: #147d52;
        --green-dark: #0c603e;
        --lime: #d7f36a;
        --canvas: #f5f7f4;
        --line: #e8ece8;
    }
    html, body, [class*="css"] { font-family: 'DM Sans', 'Segoe UI', sans-serif; color: var(--ink); }
    [data-testid="stAppViewContainer"] { background: var(--canvas); }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] {
        background: #fff;
        border-right: 1px solid var(--line);
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.4rem; }
    .block-container {
        max-width:100%;
        padding:2rem 1.5rem 3rem;
    }
    .block-container [data-testid="stHorizontalBlock"] {
        gap:1rem !important;
    }
    h1, h2, h3 { font-family: 'Manrope', 'Segoe UI', sans-serif; letter-spacing: -0.035em; color: var(--ink); }
    h1 { font-size: 2.25rem !important; font-weight: 800 !important; }
    h2 { font-size: 1.45rem !important; font-weight: 700 !important; }
    .brand { display:flex; align-items:center; gap:11px; padding: 0 0 1.5rem 0.3rem; }
    .brand-mark {
        width:42px; height:42px; border-radius:14px; display:grid; place-items:center;
        background:var(--lime); color:var(--green-dark); font-size:22px;
    }
    .brand-name { font-family:'Manrope','Segoe UI',sans-serif; font-size:16px; font-weight:800; line-height:1.2; }
    .brand-sub { color:var(--muted); font-size:11px; margin-top:3px; }
    .eyebrow {
        color:var(--green); font-size:11px; font-weight:700; letter-spacing:.14em;
        text-transform:uppercase; margin-bottom:8px;
    }
    .hero {
        background:linear-gradient(115deg,#124d38 0%,#167d53 68%,#209462 100%);
        border-radius:22px; color:white; padding:28px 32px; margin:4px 0 24px;
        box-shadow:0 12px 30px rgba(20,125,82,.12);
    }
    .hero h2 { color:white; margin:0 0 7px; font-size:24px !important; }
    .hero p { color:rgba(255,255,255,.78); margin:0; font-size:14px; }
    .hero-tag {
        display:inline-block; padding:6px 10px; margin-top:17px; border-radius:30px;
        color:#173821; background:var(--lime); font-size:11px; font-weight:700;
    }
    [data-testid="stMetric"] {
        background:white; border:1px solid var(--line); padding:17px 18px;
        border-radius:16px; box-shadow:0 3px 12px rgba(20,35,27,.025);
    }
    [data-testid="stMetricLabel"] p { color:var(--muted); font-size:12px; font-weight:600; }
    [data-testid="stMetricValue"] { font-family:'Manrope','Segoe UI',sans-serif; font-size:25px; font-weight:800; }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background:white; border:1px solid var(--line); border-radius:16px;
    }
    div[data-testid="stDataFrame"] {
        border:1px solid var(--line);
        border-radius:12px;
        overflow:visible;
    }
    div[data-testid="stDataFrame"] [class*="dvn-scroller"] {
        scrollbar-gutter:stable;
        scrollbar-color:#718078 #e8ece8;
        scrollbar-width:auto;
        padding-right:18px;
        box-sizing:border-box;
    }
    div[data-testid="stDataFrame"] [class*="dvn-scroller"]::-webkit-scrollbar {
        width:14px;
        height:14px;
    }
    div[data-testid="stDataFrame"] [class*="dvn-scroller"]::-webkit-scrollbar:horizontal {
        height:16px;
    }
    div[data-testid="stDataFrame"] [class*="dvn-scroller"]::-webkit-scrollbar-track {
        background:#e8ece8;
        border-radius:8px;
    }
    div[data-testid="stDataFrame"] [class*="dvn-scroller"]::-webkit-scrollbar-thumb {
        background:#718078;
        border:3px solid #e8ece8;
        border-radius:8px;
    }
    div[data-testid="stDataFrame"] [class*="dvn-scroller"]::-webkit-scrollbar-thumb:hover {
        background:#147d52;
    }
    div[data-testid="stDataFrame"] [class*="dvn-scroller"]::-webkit-scrollbar-thumb:horizontal {
        min-width:36px;
    }
    .section-note { color:var(--muted); font-size:13px; margin-top:-10px; margin-bottom:16px; }
    .sidebar-note {
        background:#f5f8f3; border:1px solid var(--line); border-radius:12px;
        padding:12px; color:var(--muted); font-size:11px; line-height:1.6;
    }
    .stButton > button[kind="primary"] {
        background:var(--green); border-color:var(--green); border-radius:10px;
        font-weight:700; min-height:42px;
    }
    .stButton > button[kind="primary"]:hover {
        background:var(--green-dark); border-color:var(--green-dark); color:white;
    }
    .st-key-run_triage button[kind="secondary"],
    .st-key-run_triage_budget button[kind="secondary"] {
        background:white;
        border:1px solid var(--green);
        color:var(--green);
    }
    .st-key-run_triage button[kind="secondary"]:hover,
    .st-key-run_triage_budget button[kind="secondary"]:hover {
        background:#edf7f1;
        border-color:var(--green-dark);
        color:var(--green-dark);
    }
    [data-testid="stTabs"] button { font-weight:600; }
    @media (max-width: 700px) {
        .block-container { padding:1rem 1rem 2rem; }
        .hero { padding:22px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}. Run `python run_project.py` first."
        )
    with sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True) as connection:
        customers = pd.read_sql_query("SELECT * FROM customers", connection)
        products = pd.read_sql_query("SELECT * FROM products", connection)
        orders = pd.read_sql_query("SELECT * FROM orders", connection)
    if orders.empty or customers.empty or products.empty:
        raise ValueError("The local database is missing customer, product, or order data.")
    orders["order_ts"] = pd.to_datetime(orders["order_ts"], errors="raise")
    orders["order_amount"] = pd.to_numeric(orders["order_amount"], errors="raise")
    orders["delivery_minutes"] = pd.to_numeric(orders["delivery_minutes"], errors="coerce")
    orders = orders.merge(products, on="product_id", how="left", validate="many_to_one")
    if SEGMENTS_PATH.exists():
        segments = pd.read_csv(SEGMENTS_PATH, keep_default_na=False)
        customers = customers.merge(
            segments[["customer_id", "segment_name"]],
            on="customer_id",
            how="left",
            validate="one_to_one",
        )
    if "segment_name" not in customers:
        customers["segment_name"] = "Unsegmented"
    customers["segment_name"] = customers["segment_name"].replace("", "Unsegmented").fillna("Unsegmented")
    return customers, products, orders


def page_heading(eyebrow: str, title: str, description: str) -> None:
    st.markdown(f'<div class="eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<p class="section-note">{description}</p>', unsafe_allow_html=True)


def format_inr(amount: float) -> str:
    return f"₹{amount:,.0f}"


def render_overview(customers: pd.DataFrame, orders: pd.DataFrame) -> None:
    st.markdown(
        """
        <div class="hero">
            <h2>Masai Student AI-ML Copilot Project by Maria S.P. Nathan A.M.</h2>
            <h4>Good data. Better customer moments.</h4>
            <p>Your operations snapshot, customer signals and support tools — all in one place.</p>
            <span class="hero-tag">● &nbsp;LOCAL DEMO · SYNTHETIC DATA</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    completed = orders[orders["status"].eq("completed")]
    latest = orders["order_ts"].max()
    start = latest.normalize() - pd.Timedelta(days=29)
    recent = orders[orders["order_ts"].between(start, latest)]
    previous_start = start - pd.Timedelta(days=30)
    previous = orders[orders["order_ts"].between(previous_start, start, inclusive="left")]
    order_delta = len(recent) - len(previous)
    revenue_now = recent.loc[recent["status"].eq("completed"), "order_amount"].sum()
    revenue_before = previous.loc[previous["status"].eq("completed"), "order_amount"].sum()
    revenue_delta = revenue_now - revenue_before
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Customers", f"{len(customers):,}")
    c2.metric("Orders · 30 days", f"{len(recent):,}", f"{order_delta:+,} vs prior 30 days")
    c3.metric("Completed sales · 30 days", format_inr(revenue_now), format_inr(revenue_delta))
    avg_delivery = completed["delivery_minutes"].mean()
    c4.metric("Avg. delivery", f"{avg_delivery:.0f} min" if pd.notna(avg_delivery) else "—")

    st.write("")
    left, right = st.columns([1.55, 1])
    with left:
        st.subheader("Order activity")
        daily = (
            recent.assign(day=recent["order_ts"].dt.date)
            .groupby("day", as_index=False)
            .agg(Orders=("order_id", "count"), Sales=("order_amount", "sum"))
            .set_index("day")
        )
        st.area_chart(daily[["Orders"]], color="#168052", height=265)
        st.caption(f"Daily orders · {start:%b %d}–{latest:%b %d, %Y}")
    with right:
        st.subheader("Category mix")
        category_mix = (
            completed.groupby("category")["order_id"]
            .count()
            .sort_values(ascending=False)
            .rename("Orders")
        )
        st.bar_chart(category_mix, color="#8abb54", height=265, horizontal=True)
        st.caption("Completed orders by product category")

    bottom_left, bottom_right = st.columns([1.15, 1])
    with bottom_left:
        st.subheader("Latest orders")
        latest_orders = orders.sort_values("order_ts", ascending=False).head(6)
        st.dataframe(
            latest_orders[
                ["order_id", "order_ts", "product_name", "status", "order_amount"]
            ].rename(
                columns={
                    "order_id": "Order",
                    "order_ts": "Placed",
                    "product_name": "Product",
                    "status": "Status",
                    "order_amount": "Amount (₹)",
                }
            ),
            hide_index=True,
            width="stretch",
        )
    with bottom_right:
        st.subheader("Customer segments")
        segment_counts = customers["segment_name"].value_counts().rename("Customers")
        st.bar_chart(segment_counts, color="#147d52", height=240, horizontal=True)
        st.caption("Segments are shown when the analytics pipeline has been run.")


def render_orders(orders: pd.DataFrame) -> None:
    page_heading("OPERATIONS", "Orders", "Search and explore the local order history.")
    min_date = orders["order_ts"].min().date()
    max_date = orders["order_ts"].max().date()
    f1, f2, f3 = st.columns([1, 1, 1.5])
    statuses = sorted(orders["status"].dropna().unique().tolist())
    with f1:
        status_filter = st.multiselect("Order status", statuses, default=statuses)
    with f2:
        categories = sorted(orders["category"].dropna().unique().tolist())
        category_filter = st.multiselect("Category", categories, default=categories)
    with f3:
        date_range = st.date_input(
            "Order date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
    search = st.text_input("Search orders", placeholder="Order ID, customer, or product")
    filtered = orders[
        orders["status"].isin(status_filter) & orders["category"].isin(category_filter)
    ].copy()
    if isinstance(date_range, tuple) and len(date_range) == 2:
        filtered = filtered[
            filtered["order_ts"].dt.date.between(date_range[0], date_range[1])
        ]
    if search.strip():
        query = search.strip().lower()
        match = (
            filtered["order_id"].astype(str).str.lower().str.contains(query, regex=False)
            | filtered["customer_id"].astype(str).str.lower().str.contains(query, regex=False)
            | filtered["product_name"].astype(str).str.lower().str.contains(query, regex=False)
        )
        filtered = filtered[match]
    c1, c2, c3 = st.columns(3)
    c1.metric("Matching orders", f"{len(filtered):,}")
    c2.metric("Completed sales", format_inr(filtered.loc[filtered["status"].eq("completed"), "order_amount"].sum()))
    c3.metric("Average basket", format_inr(filtered.loc[filtered["status"].eq("completed"), "order_amount"].mean()) if filtered["status"].eq("completed").any() else "—")
    st.dataframe(
        filtered.sort_values("order_ts", ascending=False)[
            [
                "order_id", "customer_id", "order_ts", "product_name", "category",
                "quantity", "status", "delivery_minutes", "order_amount",
            ]
        ].rename(
            columns={
                "order_id": "Order ID",
                "customer_id": "Customer",
                "order_ts": "Placed",
                "product_name": "Product",
                "category": "Category",
                "quantity": "Qty",
                "status": "Status",
                "delivery_minutes": "Delivery (min)",
                "order_amount": "Amount (₹)",
            }
        ),
        hide_index=True,
        width="stretch",
        height=520,
    )


def render_product_master(products: pd.DataFrame) -> None:
    page_heading(
        "CATALOGUE",
        "Product Master",
        "Browse product records loaded from the products table in the local database.",
    )
    categories = sorted(products["category"].dropna().unique().tolist())
    f1, f2 = st.columns([1, 1.5])
    with f1:
        category_filter = st.multiselect("Category", categories, default=categories)
    with f2:
        search = st.text_input("Search products", placeholder="Product ID or product name")

    filtered = products[products["category"].isin(category_filter)].copy()
    if search.strip():
        query = search.strip()
        matches = (
            filtered["product_id"].astype(str).str.contains(query, case=False, regex=False)
            | filtered["product_name"].astype(str).str.contains(query, case=False, regex=False)
        )
        filtered = filtered[matches]

    count, category_count, average_price = st.columns(3)
    count.metric("Products shown", f"{len(filtered):,}")
    category_count.metric("Categories shown", f"{filtered['category'].nunique():,}")
    average_price.metric(
        "Average listed price",
        format_inr(filtered["price_inr"].mean()) if not filtered.empty else "—",
    )
    st.dataframe(
        filtered.sort_values(["category", "product_name"])[
            ["product_id", "product_name", "category", "price_inr"]
        ].rename(
            columns={
                "product_id": "Product ID",
                "product_name": "Product",
                "category": "Category",
                "price_inr": "Price (₹)",
            }
        ),
        hide_index=True,
        width="stretch",
        height=520,
    )
    st.download_button(
        "Download product records",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="product_master.csv",
        mime="text/csv",
    )


def load_sql_queries() -> list[tuple[str, str]]:
    if not SQL_QUERIES_PATH.exists():
        raise FileNotFoundError(f"SQL query file not found: {SQL_QUERIES_PATH}")

    queries: list[tuple[str, str]] = []
    current_label = None
    statement_lines: list[str] = []
    for line in SQL_QUERIES_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("-- Q"):
            if statement_lines:
                raise ValueError(f"SQL query {current_label} is missing a semicolon.")
            current_label = stripped[2:].strip()
            statement_lines = []
            continue
        if current_label is None:
            continue
        statement_lines.append(line)
        if stripped.endswith(";"):
            statement = "\n".join(statement_lines).strip()
            statement = statement[:-1].strip()
            if ";" in statement:
                raise ValueError(f"SQL query {current_label} contains multiple statements.")
            if not statement.lower().startswith(("select", "with")):
                raise ValueError(f"SQL query {current_label} must be a read-only SELECT query.")
            queries.append((current_label, statement))
            current_label = None
            statement_lines = []

    if statement_lines:
        raise ValueError(f"SQL query {current_label} is missing a semicolon.")
    if not queries:
        raise ValueError(f"No labeled SQL queries were found in {SQL_QUERIES_PATH}.")
    return queries


def render_sql_analysis() -> None:
    page_heading(
        "DATA EXPLORATION",
        "SQL Analysis",
        "Run the prepared SQL examples against the local Instamart database and inspect each result.",
    )
    try:
        queries = load_sql_queries()
    except (OSError, ValueError) as error:
        st.error(f"Could not load SQL examples: {error}")
        return

    for index, (label, query) in enumerate(queries):
        st.subheader(label)
        st.code(query, language="sql")
        if st.button(f"Run {label.split(':', 1)[0]}", key=f"run_sql_query_{index}"):
            try:
                with sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True) as connection:
                    result = pd.read_sql_query(query, connection)
                st.session_state[f"sql_result_{index}"] = result
                st.session_state.pop(f"sql_error_{index}", None)
            except (sqlite3.Error, ValueError) as error:
                st.session_state.pop(f"sql_result_{index}", None)
                st.session_state[f"sql_error_{index}"] = str(error)

        query_error = st.session_state.get(f"sql_error_{index}")
        if query_error:
            st.error(f"Query failed: {query_error}")
        elif f"sql_result_{index}" in st.session_state:
            result = st.session_state[f"sql_result_{index}"]
            st.caption(f"{len(result):,} rows returned")
            st.dataframe(result, hide_index=True, width="stretch", height=320)


def render_customers(customers: pd.DataFrame, orders: pd.DataFrame) -> None:
    page_heading("CUSTOMER INTELLIGENCE", "Customers", "Understand customer activity, spend and segments.")
    completed = orders[orders["status"].eq("completed")]
    summary = completed.groupby("customer_id").agg(
        completed_orders=("order_id", "nunique"),
        lifetime_spend=("order_amount", "sum"),
        last_order=("order_ts", "max"),
        avg_delivery=("delivery_minutes", "mean"),
    )
    data = customers.merge(summary, on="customer_id", how="left")
    data["completed_orders"] = data["completed_orders"].fillna(0).astype(int)
    data["lifetime_spend"] = data["lifetime_spend"].fillna(0)
    cities = sorted(data["city"].dropna().unique().tolist())
    segments = sorted(data["segment_name"].dropna().unique().tolist())
    f1, f2, f3 = st.columns([1, 1, 1.5])
    with f1:
        city_filter = st.multiselect("City", cities, default=cities)
    with f2:
        segment_filter = st.multiselect("Segment", segments, default=segments)
    with f3:
        search = st.text_input("Find a customer", placeholder="Customer ID")
    filtered = data[data["city"].isin(city_filter) & data["segment_name"].isin(segment_filter)].copy()
    if search.strip():
        filtered = filtered[
            filtered["customer_id"].astype(str).str.contains(search.strip(), case=False, regex=False)
        ]
    c1, c2, c3 = st.columns(3)
    c1.metric("Customers shown", f"{len(filtered):,}")
    c2.metric("Completed orders", f"{filtered['completed_orders'].sum():,}")
    c3.metric("Customer spend", format_inr(filtered["lifetime_spend"].sum()))
    st.dataframe(
        filtered.sort_values("lifetime_spend", ascending=False)[
            [
                "customer_id", "city", "age", "gender", "segment_name",
                "completed_orders", "lifetime_spend", "last_order", "avg_delivery",
            ]
        ].rename(
            columns={
                "customer_id": "Customer ID",
                "city": "City",
                "age": "Age",
                "gender": "Gender",
                "segment_name": "Segment",
                "completed_orders": "Orders",
                "lifetime_spend": "Lifetime spend (₹)",
                "last_order": "Last order",
                "avg_delivery": "Avg. delivery (min)",
            }
        ),
        hide_index=True,
        width="stretch",
        height=520,
    )
    if "Unsegmented" in segment_filter:
        st.caption("Run `python run_project.py` to generate customer segment and lapse-model outputs.")


def render_churn_predictions() -> None:
    page_heading(
        "CUSTOMER INTELLIGENCE",
        "Churn predictions",
        "Explore rule-based churn risk scores for the observed September 2025 cohort.",
    )
    st.info(
        "These are deterministic, rule-based scores from the project's internal mock "
        "API using pre-September behavior. They are illustrative risk indicators, "
        "not a trained model or a forecast of future churn."
    )
    st.caption(
        "Customers without completed orders before September 2025 are not included "
        "because there is no prior purchase history to score."
    )
    if st.button("Generate / refresh predictions", type="primary", key="generate_churn"):
        try:
            from customers_churn_prediction import predict_customer_churn

            with st.spinner("Scoring customers with the internal churn heuristic..."):
                predictions, metrics = predict_customer_churn()
            st.session_state["churn_predictions"] = predictions
            st.session_state["churn_metrics"] = metrics
        except (OSError, sqlite3.Error, ValueError, RuntimeError) as error:
            st.error(f"Could not generate customer churn predictions: {error}")

    if "churn_predictions" in st.session_state:
        predictions = st.session_state["churn_predictions"].copy()
        metrics = st.session_state.get("churn_metrics", {})
    elif CHURN_PREDICTIONS_PATH.exists():
        try:
            predictions = pd.read_csv(CHURN_PREDICTIONS_PATH)
            metrics = {"scoring_method": "internal deterministic mock_llm heuristic"}
        except (OSError, ValueError) as error:
            st.error(f"Could not read the churn predictions CSV: {error}")
            return
    else:
        st.caption("No churn prediction CSV exists yet. Generate it here or run `python customers_churn_prediction.py`.")
        return

    if predictions.empty:
        st.warning("The churn predictions file contains no customer scores.")
        return
    probabilities = pd.to_numeric(predictions["churn_probability"], errors="coerce")
    if probabilities.isna().any():
        st.error("The churn predictions file contains invalid probability values.")
        return

    total, high_risk, predicted, average = st.columns(4)
    total.metric("Customers scored", f"{len(predictions):,}")
    high_risk.metric("High-risk customers", f"{predictions['risk_level'].eq('High').sum():,}")
    predicted.metric("Predicted churn", f"{predictions['predicted_churn'].sum():,}")
    average.metric("Average churn probability", f"{probabilities.mean():.1%}")
    if "scoring_method" in metrics:
        st.caption(f"Scoring method: {metrics['scoring_method']}.")

    st.subheader("Customer risk distribution")
    left, right = st.columns([1, 1.4])
    with left:
        st.bar_chart(
            predictions["risk_level"]
            .value_counts()
            .reindex(["High", "Medium", "Low"], fill_value=0)
            .rename("Customers"),
            color="#147d52",
            horizontal=True,
        )
    with right:
        risk_filter = st.multiselect(
            "Risk level",
            ["High", "Medium", "Low"],
            default=["High", "Medium", "Low"],
        )
        prediction_filter = st.selectbox(
            "Prediction",
            ["All customers", "Predicted churn", "Predicted active"],
        )
        filtered = predictions[predictions["risk_level"].isin(risk_filter)].copy()
        if prediction_filter == "Predicted churn":
            filtered = filtered[filtered["predicted_churn"].eq(1)]
        elif prediction_filter == "Predicted active":
            filtered = filtered[filtered["predicted_churn"].eq(0)]

    display_columns = [
        "customer_id",
        "churn_probability",
        "predicted_churn",
        "risk_level",
        "actual_churned_in_september_2025",
    ]
    st.dataframe(
        filtered[display_columns].rename(
            columns={
                "customer_id": "Customer ID",
                "churn_probability": "Churn probability",
                "predicted_churn": "Predicted churn (1 = yes)",
                "risk_level": "Risk level",
                "actual_churned_in_september_2025": "Observed September churn",
            }
        ).style.format({"Churn probability": "{:.4f}"}),
        hide_index=True,
        width="stretch",
        height=440,
    )
    st.download_button(
        "Download filtered predictions",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="customers_churn_prediction.csv",
        mime="text/csv",
    )


def set_triage_mode(mode: str) -> None:
    st.session_state["triage_mode"] = mode


def render_support() -> None:
    page_heading("SUPPORT DESK", "Support copilot", "Grounded policy answers and privacy-aware ticket triage.")
    policy_tab, triage_tab = st.tabs(["Policy assistant", "Ticket triage"])
    with policy_tab:
        st.markdown("Ask about refunds, delivery, payments or other documented policies.")
        question = st.text_area(
            "Your question",
            placeholder="For example: When does a late delivery qualify for a refund?",
            height=110,
            label_visibility="collapsed",
        )
        if st.button("Ask policy copilot", type="primary", key="policy_question"):
            if not question.strip():
                st.warning("Enter a question to search the policy documents.")
            else:
                try:
                    from src.policy_rag import PolicyRAG

                    with st.spinner("Searching the local policy documents..."):
                        result = PolicyRAG().answer(question.strip())
                    st.markdown("#### Answer")
                    st.info(result["answer"])
                    st.caption("Sources: " + ", ".join(result["sources"]))
                    with st.expander("Retrieved policy passages"):
                        for item in result["retrieved"]:
                            st.markdown(f"**{item['source']} · relevance {item['score']:.2f}**")
                            st.write(item["text"])
                except (OSError, sqlite3.Error, ValueError, RuntimeError) as error:
                    st.error(f"Could not answer from the local policy documents: {error}")
    with triage_tab:
        st.markdown(
            "Classify the synthetic ticket dataset using the existing redaction, retry, "
            "output-validation and routing pipeline."
        )
        st.warning(
            "Regular triage writes `outputs/triage_results.csv`. Budget triage writes "
            "`outputs/triage_budget_demo.csv` and replaces the `triage_budget_demo` table in `data/instamart.db`."
        )
        regular_button, budget_button = st.columns(2)
        triage_mode = st.session_state.get("triage_mode")
        with regular_button:
            run_regular = st.button(
                "Run Ticket Triage",
                type="primary" if triage_mode == "regular" else "secondary",
                key="run_triage",
                on_click=set_triage_mode,
                args=("regular",),
                width="stretch",
            )
        with budget_button:
            run_budget = st.button(
                "Run Triage Budget",
                type="primary" if triage_mode == "budget" else "secondary",
                key="run_triage_budget",
                on_click=set_triage_mode,
                args=("budget",),
                width="stretch",
            )
        if run_regular:
            try:
                from src.triage import FEW, run_pipeline

                with st.spinner("Redacting and classifying tickets..."):
                    results, summary = run_pipeline(prompt=FEW, token_budget=100000)
                st.session_state["triage_results"] = results
                st.session_state["triage_summary"] = summary
            except (OSError, ValueError, RuntimeError) as error:
                st.error(f"Ticket triage failed: {error}")
        if run_budget:
            try:
                from src.triage import FEW, run_pipeline

                with st.spinner("Running the 1,000-token budget demonstration..."):
                    results, summary = run_pipeline(prompt=FEW, token_budget=1000)
                st.session_state["triage_results"] = results
                st.session_state["triage_summary"] = summary
            except (OSError, ValueError, RuntimeError) as error:
                st.error(f"Ticket budget demo failed: {error}")
        if "triage_results" in st.session_state:
            results = st.session_state["triage_results"]
            summary = st.session_state["triage_summary"]
            mode = st.session_state.get("triage_mode", "regular")
            m1, m2, m3 = st.columns(3)
            m1.metric("Tickets processed", f"{len(results):,}")
            m2.metric("Tokens used", f"{summary['tokens']:,}")
            human_review_statuses = [
                "flagged_invalid_output", "flagged_long", "skipped_empty"
            ]
            if mode == "budget":
                human_review_statuses.append("budget_exhausted")
                st.caption(
                    f"Budget demo saved to `outputs/{summary['output_file']}` and "
                    f"SQLite table `{summary['database_table']}` in `data/instamart.db`."
                )
            m3.metric(
                "Human review",
                f"{sum(summary['status_counts'].get(status, 0) for status in human_review_statuses):,}",
            )
            st.caption("PII redactions: " + " · ".join(f"{key}: {value}" for key, value in summary["redactions"].items()))
            selected_route = st.selectbox("Filter by route", ["All routes"] + sorted(results["route"].unique()))
            shown = results if selected_route == "All routes" else results[results["route"].eq(selected_route)]
            st.dataframe(shown, hide_index=True, width="stretch", height=400)


def main() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="brand">
                <div class="brand-mark">🛒</div>
                <div>
                    <div class="brand-name">instamart</div>
                    <div class="brand-sub">CUSTOMER COPILOT</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        selection = st.radio(
            "WORKSPACE",
            [
                "Overview",
                "SQL Analysis",
                "Products",
                "Customers",
                "Orders",
                "Customer Churn Prediction",
                "Support Copilot",
            ],
            label_visibility="visible",
        )
        st.divider()
        if st.button("↻  Refresh local data", width="stretch"):
            st.cache_data.clear()
            st.rerun()
        st.markdown(
            '<div class="sidebar-note">Offline teaching demo<br>'
            'Local database · synthetic records<br>No external model or API calls</div>',
            unsafe_allow_html=True,
        )
    try:
        customers, products, orders = load_data()
    except (OSError, sqlite3.Error, ValueError) as error:
        st.error(f"Unable to load the local Instamart data: {error}")
        st.stop()
    if selection == "Overview":
        render_overview(customers, orders)
    elif selection == "SQL Analysis":
        render_sql_analysis()
    elif selection == "Orders":
        render_orders(orders)
    elif selection == "Products":
        render_product_master(products)
    elif selection == "Customers":
        render_customers(customers, orders)
    elif selection == "Customer Churn Prediction":
        render_churn_predictions()
    else:
        render_support()


if __name__ == "__main__":
    main()
