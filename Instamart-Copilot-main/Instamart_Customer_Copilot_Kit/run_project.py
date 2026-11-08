"""Run all project stages in sequence. Use this after installing requirements."""
from pathlib import Path
import subprocess
import sys

from src.data_pipeline import audit,clean_data,validate
from src.customer_models import rfm_and_segments,build_lapse_model
from src.triage import run_pipeline,FEW
from src.policy_rag import PolicyRAG,evaluate
from customers_churn_prediction import predict_customer_churn

ROOT=Path(__file__).resolve().parent


def main():
    print("\n=== PART A: AUDIT / CLEAN / VALIDATE ===")
    audit(); clean_data(); validate()
    print("\n=== PART B: SEGMENTS ===")
    rfm,diagnostics,profile,pca=rfm_and_segments()
    print("K-means diagnostics:\n",diagnostics.to_string(index=False))
    print("Segment profile:\n",profile.to_string(index=False)); print("PCA explained variance:",pca)
    print("Lapse model summary:",build_lapse_model())
    print("\n=== PART C: TRIAGE ===")
    triage,summary=run_pipeline(prompt=FEW,token_budget=100000)
    print(summary); print(triage.head().to_string(index=False))
    print("\n=== PART C2: TRIAGE TOKEN-BUDGET DEMO ===")
    budget_demo,budget_summary=run_pipeline(prompt=FEW,token_budget=1000)
    print(budget_summary)
    print("Budget demo results: outputs/triage_budget_demo.csv; SQLite table: triage_budget_demo")
    print(budget_demo.head().to_string(index=False))
    print("\n=== PART D: POLICY RAG ===")
    rag=PolicyRAG(); print("chunks:",len(rag.chunks)); print(evaluate(rag).to_string(index=False))
    print("\n=== PART E: CUSTOMER CHURN PREDICTION ===")
    predictions,metrics=predict_customer_churn()
    print("Churn model metrics:",metrics)
    print(predictions.head(10).to_string(index=False))
    print("\nProject pipeline finished. Review outputs/ and data/instamart.db.")
    print("Starting the Streamlit dashboard at http://localhost:8501. Press Ctrl+C to stop.")
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(ROOT / "app.py")],
        cwd=ROOT,
        check=True,
    )


if __name__=="__main__": main()
