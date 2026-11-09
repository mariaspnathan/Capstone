# Customer Intelligence & Support Copilot — Teaching Kit

> Educational implementation of the supplied fictional Instamart-style capstone. All generated records are synthetic; no real customer data, hosted LLM, API key, or network call is needed.

## Learning outcomes
Students learn to (1) fetch/read CSV exports and audit data, (2) clean and persist trusted tables in SQLite, (3) write SQL and pandas analytics, (4) segment customers and train a leakage-aware lapse model, (5) redact PII and triage text with retries/output validation, and (6) retrieve policy passages and execute bounded database-backed tools.

## Setup and run
Python 3.11+ recommended.

Run the below commands based on the OS (Windows/Linux)

```bash
# Windows
python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python generate_data.py
python run_project.py
```
## Note
  All the functions in the PARTS (A to E) are called in the run_projects.py and step by step code can be run using jupyter notebook Customer_Intelligence_Support_Copilot.ipynb 

## Make sure that the right Kernal and .venv folder selected to run the jupyter notebook to run. 
For the notebook, open `notebooks/Customer_Intelligence_Support_Copilot.ipynb` in VS Code and choose **Select Kernel → Python Environments**. Select `Instamart_Customer_Copilot_Kit\.venv\Scripts\python.exe` (not a `.venv` at the outer workspace root), then run cells from top to bottom. The setup cell checks the active interpreter and derives the project root from that environment, so it does not depend on VS Code's current working directory.

## Streamlit browser based web page database application
The local dashboard in the browser will start automatically from this directory after installing the requirements and run_project.py:

The app includes an operations Overview, SQL Analysis for the examples in `sql/queries.sql`, searchable Product Master sourced from the SQLite `products` table, order history, customer insights, a policy assistant, and ticket triage. SQL examples run against the local SQLite database in read-only mode. All records and model responses are synthetic/offline. Use **Refresh local data** in the sidebar after regenerating the database.
left pane contains the below features to see the results in the right pane.
  1. Overview - Summary of the metrics and charts
  2. SQL Analysis - Run and test the sql on the tables resides in the instamart.db
  3. Producs - Query all the records from the product master table and can be apply conditions and sorting.
  4. Customers -  Query all the records and metrics from the Customer master table and can be apply conditions and sorting.
  5. Orders - Query all the records and metrics from the Sales Order transactions table and can be apply conditions and sorting.
  6. Customer Churn Prediction - View all the churn percentage for each customer and summary at top level.
  7. Support Copilet - It has two tab pages
   -  Policy assistant
        User can ask questions related to policy documents in the provide window.
   -  Ticket triage - It has two functions in the buttons
       1. Run Ticket Tirage
       2. Run Tirage Budget.

## Jupyter notebook file is provide to run step by step code
Open `notebooks/Customer_Intelligence_Support_Copilot.ipynb` and run cells from top to bottom. The notebook calls the same modules used by the scripts.

## Repository map
- `generate_data.py`: deterministic fictional CSV and policy generation.
- `app.py`: Streamlit dashboard and support copilot interface.
- `customers_churn_prediction.py`: scores the churn cohort using the internal offline mock and writes customer-level risk scores.
- `mock_llm.py`: offline stand-in for classification, policy answers and agent tool calls.
- `src/data_pipeline.py`: audit, clean, SQLite load, validation.
- `src/customer_models.py`: RFM, K-means, PCA, lapse model with train/test separation.
- `src/triage.py`: token guardrails, PII redaction, retries, response validation, routing.
- `src/policy_rag.py`: chunking, TF-IDF retrieval and grounded policy evaluation.
- `src/refund_agent.py`: order lookup, refund calculation, ledger and bounded tool loop.
- `sql/queries.sql`: seven SQL learning patterns.
- `outputs/`: generated artifacts; `state/`: agent checkpoint examples.

## How students should learn the data-fetching flow
1. `pd.read_csv("data/raw/orders.csv", keep_default_na=False)` loads local export rows. In a production project, a fetch function might download from an approved endpoint or query a warehouse, but this exercise intentionally uses local synthetic data and has no credentials.
2. Inspect shape, data types, null/blank counts, duplicate rows, keys and impossible values before cleaning.
3. Apply one documented cleaning rule at a time and compare row/value counts before and after.
4. Write clean CSVs for easy inspection and SQLite tables for repeatable SQL queries.
5. Run assertions before downstream modelling. A failed assertion should stop the pipeline rather than silently propagate bad data.

## Part A — Data foundation
The pipeline standardizes city/gender, treats invalid ages as missing, resolves duplicate orders by keeping the latest timestamp, imputes missing amounts from catalogue price, sets negative delivery times to missing and imputes only completed-order delivery durations by product category. Review every rule before teaching; the capstone handout's numeric checkpoints should be used as acceptance tests.

## Part B — Segments and lapse
RFM uses completed orders and a fixed snapshot date. K-means diagnostics compare K=2..8; the notebook starts with K=4 for interpretable teaching. Lapse features use orders strictly before 2025-09-01, while the label uses September outcomes. The pipeline uses a preprocessing Pipeline fitted on training rows, GridSearchCV and a saved joblib model. The Premium retention list is illustrative only because the Premium label uses the whole RFM window and is post-hoc; it is not a leakage-free evaluation.

## Part C — Ticket triage and privacy
Empty and overlong tickets are skipped before model calls. Email, phone and order ID patterns are redacted before prompting. Retries handle simulated transient errors. JSON category values are allow-listed; malformed outputs are accepted only when exactly one allowed category is detectable using `re.findall`. Human review receives guardrail/invalid/budget cases, fraud goes to security, premium customers go to the premium desk, and the rest go to the support queue. Running `python run_project.py` runs both the regular triage and a 1,000-token budget demonstration, generating `outputs/triage_results.csv` and `outputs/triage_budget_demo.csv`; the budget demo also replaces the `triage_budget_demo` table in `data/instamart.db`. The dashboard provides separate **Run Ticket Triage** and **Run Triage Budget** buttons for these workflows.

## Part D — Policy retrieval and refund tools
Policy documents are chunked with overlap, represented with `TfidfVectorizer`, and ranked using cosine similarity. The offline mock returns context-derived sentences. Refund rules are implemented in Python tools backed by SQLite: completed orders delivered in over 45 minutes qualify for a full refund; orders over INR 1000 escalate instead of auto-issuing. This is a teaching simulation, not a payment integration.

## Part E — Customer churn prediction
This stage scores the historical customer cohort using pre-September 2025 order data and compares the scores with observed September outcomes. It is separate from the trained lapse model in Part B: churn scoring uses the deterministic `mock_llm.predict_churn` heuristic, not a model fitted with scikit-learn. Its probabilities and risk levels are illustrative teaching outputs, not calibrated predictions.

The cohort contains customers with at least one completed order before September 1, 2025. The script derives these features from their pre-September history: recency, completed-order frequency and monetary total, average discount, cancellation rate, average delivery duration, and customer tenure. Missing feature values are filled with each feature's cohort median before scoring. The observed label is whether each customer had no completed order during September 2025. Since this label uses the same historical window being evaluated, the exported results describe that past cohort; they are not a forecast of future churn.

After running the setup and data preparation steps above, run the scoring script directly:

```bash
python customers_churn_prediction.py
```

It writes `outputs/customers_churn_prediction.csv`, with one row per customer and columns for `customer_id`, `churn_probability`, `predicted_churn`, `risk_level`, and `actual_churned_in_september_2025`. Rows are ordered from highest to lowest churn probability. To run it as part of the complete workflow, use `python run_project.py`; the pipeline executes this stage after Parts A–D and then starts the Streamlit dashboard. In the dashboard, open **Churn predictions** to generate or refresh scores and review risk summaries and customer-level results.

## GitHub suggestions
These public repositories/documentation projects are useful for learning concepts; do not copy a student's capstone solution. Adapt the patterns and cite the source in your notes:
- pandas documentation: https://github.com/pandas-dev/pandas — CSV loading, cleaning, groupby, pivot tables.
- scikit-learn: https://github.com/scikit-learn/scikit-learn — pipelines, preprocessing, clustering, model selection, metrics and TF-IDF.
- Python tutorial: https://github.com/python/cpython/tree/main/Doc/tutorial — Python fundamentals.
- Jupyter Notebook: https://github.com/jupyter/notebook — notebook workflow.
- SQLite: https://github.com/sqlite/sqlite — SQL database engine (official mirror).
- scikit-learn text feature extraction guide: https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction.
- streamlit: libraries to build the browser based web pages database applications using python code

## Limitations and next steps
- This is a teaching implementation and may need adjustment to match every numeric checkpoint in a strict grading rubric; compare actual outputs with the supplied brief and investigate differences rather than hardcoding expected answers.
- The offline mock model is deterministic rule-based simulation, not a real language model.
- The refund ledger is a local JSONL audit trail, not a real transaction system.
- Production work would add access controls, secure secret management, monitoring, schema contracts, data lineage, model drift checks and human approval workflows.
