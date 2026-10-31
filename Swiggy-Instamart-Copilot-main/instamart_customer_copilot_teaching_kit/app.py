"""Streamlit dashboard for the local Instamart customer copilot teaching kit."""
from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "instamart.db"
SEGMENTS_PATH = ROOT / "outputs" / "customer_segments.csv"
CHURN_PREDICTIONS_PATH = ROOT / "outputs" / "customers_churn_prediction.csv"

# Automatically run the data build script if the database is missing
if not os.path.exists(DB_PATH):
    print("Database missing. Running setup script...")
    subprocess.run(["python", "run_project.py"], check=True)

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
    .block-container { max-width: 1440px; padding-top: 2rem; padding-bottom: 3rem; }
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
    div[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:12px; overflow:hidden; }
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
            <h2>Good data. Better customer moments.</h2>
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
        except (OSError, ValueError, RuntimeError) as error:
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
        ).style.format({"Churn probability": "{:.1%}"}),
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
                except (OSError, ValueError, RuntimeError) as error:
                    st.error(f"Could not answer from the local policy documents: {error}")
    with triage_tab:
        st.markdown(
            "Classify the synthetic ticket dataset using the existing redaction, retry, "
            "output-validation and routing pipeline."
        )
        st.warning("Ticket processing may update `outputs/triage_results.csv`.")
        if st.button("Run ticket triage", type="primary", key="run_triage"):
            try:
                from src.triage import FEW, run_pipeline

                with st.spinner("Redacting and classifying tickets..."):
                    results, summary = run_pipeline(prompt=FEW, token_budget=100000)
                st.session_state["triage_results"] = results
                st.session_state["triage_summary"] = summary
            except (OSError, ValueError, RuntimeError) as error:
                st.error(f"Ticket triage failed: {error}")
        if "triage_results" in st.session_state:
            results = st.session_state["triage_results"]
            summary = st.session_state["triage_summary"]
            m1, m2, m3 = st.columns(3)
            m1.metric("Tickets processed", f"{len(results):,}")
            m2.metric("Tokens used", f"{summary['tokens']:,}")
            m3.metric("Human review", f"{summary['status_counts'].get('flagged_invalid_output', 0) + summary['status_counts'].get('flagged_long', 0) + summary['status_counts'].get('skipped_empty', 0):,}")
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
            ["Overview", "Orders", "Customers", "Churn predictions", "Support copilot"],
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
    elif selection == "Orders":
        render_orders(orders)
    elif selection == "Customers":
        render_customers(customers, orders)
    elif selection == "Churn predictions":
        render_churn_predictions()
    else:
        render_support()


if __name__ == "__main__":
    main()
