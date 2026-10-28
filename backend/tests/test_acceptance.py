import pytest
import sys
import os
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
from fastapi.testclient import TestClient

from app.main import app

from app.core.dataset_manager import dataset_manager
from app.core.duckdb_engine import duckdb_engine
from app.formula_engine.functions import ExcelFunctions, ExcelError
from app.formula_engine.evaluator import FormulaEvaluator

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def setup_test_data():
    # Pre-generate retail sales sample for tests
    meta = dataset_manager.generate_sample_dataset("retail_sales", 5000)
    dataset_manager.set_active_dataset_id(meta["id"])
    return meta

# --- Test 1: 100,000 rows processing ---
def test_100k_rows_dataset():
    # Benchmark 100,000 rows CSV creation and DuckDB ingestion
    meta_100k = dataset_manager.generate_sample_dataset("100k_benchmark", 100000)
    assert meta_100k["row_count"] >= 100000
    assert meta_100k["column_count"] >= 10
    
    # Query over full 100,000 rows in DuckDB
    res = duckdb_engine.execute_query(f"SELECT COUNT(*), SUM(Sales) FROM {meta_100k['table_name']}")
    assert res["success"] is True
    assert res["rows"][0][0] >= 100000
    assert res["rows"][0][1] > 0

# --- Test 2: Multi-Sheet Excel Workbook ---
def test_multisheet_excel():
    meta_excel = dataset_manager.generate_sample_dataset("financial_multisheet")
    assert meta_excel["format"] in ["XLSX", "XLS"]
    assert len(meta_excel["available_sheets"]) >= 2
    assert "Revenue_Streams" in meta_excel["available_sheets"]
    assert "Operating_Expenses" in meta_excel["available_sheets"]

# --- Test 3: "Calculate total sales and average profit" ---
def test_total_sales_and_avg_profit():
    active_id = dataset_manager.get_active_dataset_id()
    resp = client.post("/api/chat/ask", json={
        "query": "Calculate total sales and average profit",
        "dataset_id": active_id
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "kpi_cards" in data
    assert any("sales" in k["label"].lower() for k in data["kpi_cards"])
    assert any("profit" in k["label"].lower() for k in data["kpi_cards"])

# --- Test 4: "Create a monthly sales dashboard" ---
def test_monthly_sales_dashboard():
    active_id = dataset_manager.get_active_dataset_id()
    resp = client.post("/api/chat/ask", json={
        "query": "Create a monthly sales dashboard",
        "dataset_id": active_id
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "dashboard"
    assert "dashboard" in data
    assert len(data["dashboard"]["charts"]) >= 2
    assert len(data["dashboard"]["kpis"]) >= 2

# --- Test 5: "Find the top 10 products by profit" ---
def test_top_10_products_by_profit():
    active_id = dataset_manager.get_active_dataset_id()
    resp = client.post("/api/chat/ask", json={
        "query": "Find the top 10 products by profit",
        "dataset_id": active_id
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "chart"
    assert "chart_data" in data
    assert len(data["chart_data"]) <= 10
    # Verify values are sorted descending
    vals = [c["value"] for c in data["chart_data"]]
    assert vals == sorted(vals, reverse=True)

# --- Test 6: "Calculate profit margin without using Excel formulas" ---
def test_profit_margin_without_formulas():
    active_id = dataset_manager.get_active_dataset_id()
    resp = client.post("/api/chat/ask", json={
        "query": "Calculate profit margin without using Excel formulas",
        "dataset_id": active_id
    })
    assert resp.status_code == 200
    data = resp.json()
    assert any("margin" in k["label"].lower() for k in data["kpi_cards"])
    assert "verification_trace" in data

# --- Test 7: Find and remove duplicates with preview & confirmation ---
def test_duplicate_preview_and_apply():
    active_id = dataset_manager.get_active_dataset_id()
    # 1. Preview
    resp_prev = client.post("/api/cleaning/duplicates/preview", json={"dataset_id": active_id})
    assert resp_prev.status_code == 200
    preview = resp_prev.json()
    assert preview["requires_confirmation"] is True
    assert preview["affected_rows"] >= 0

    # 2. Apply confirmation
    resp_apply = client.post("/api/cleaning/duplicates/apply", json={"dataset_id": active_id})
    assert resp_apply.status_code == 200
    res_data = resp_apply.json()
    assert res_data["success"] is True
    assert res_data["summary"]["after_rows"] <= res_data["summary"]["before_rows"]

# --- Test 8: Follow-up conversational question ("Now show only Chennai") ---
def test_conversational_followup():
    active_id = dataset_manager.get_active_dataset_id()
    session_id = "test_conv_session"
    # Step 1: Base question
    client.post("/api/chat/ask", json={
        "query": "Show total sales and profit",
        "session_id": session_id,
        "dataset_id": active_id
    })
    # Step 2: Follow-up
    resp2 = client.post("/api/chat/ask", json={
        "query": "Now show only Chennai",
        "session_id": session_id,
        "dataset_id": active_id
    })
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert "Chennai" in data2["title"]
    assert "verification_trace" in data2

# --- Test 9: SQL aggregation verified against independent calculation ---
def test_sql_aggregation_verification():
    active_id = dataset_manager.get_active_dataset_id()
    df = dataset_manager.get_dataset_dataframe(active_id)
    expected_sum = round(float(df["Sales"].sum()), 2)

    meta = dataset_manager.get_dataset(active_id)
    sql_resp = client.post("/api/sql/execute", json={
        "query": f"SELECT ROUND(SUM(Sales), 2) FROM {meta['table_name']}"
    })
    assert sql_resp.status_code == 200
    sql_val = sql_resp.json()["rows"][0][0]
    assert abs(sql_val - expected_sum) < 0.05

# --- Test 10: Forecast with validation results and limitations ---
def test_time_series_forecasting():
    active_id = dataset_manager.get_active_dataset_id()
    resp = client.post("/api/ml/forecast", json={
        "dataset_id": active_id,
        "target_measure": "Sales",
        "date_column": "Order_Date",
        "periods_ahead": 6
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "forecast_data" in data
    assert "validation_metrics" in data
    assert "model_assumptions" in data
    assert data["validation_metrics"]["rmse"] >= 0

# --- Test 11: Export cleaned dataset and verify row count & structure ---
def test_export_cleaned_dataset():
    active_id = dataset_manager.get_active_dataset_id()
    resp = client.get(f"/api/reports/export/excel/{active_id}")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# --- Test 12: Excel Formula Engine Parity against known results ---
def test_formula_engine_functions():
    # SUM, AVERAGE, MIN, MAX
    assert ExcelFunctions.sum(10, 20, 30) == 60
    assert ExcelFunctions.average(10, 20, 30) == 20
    assert ExcelFunctions.min(10, 5, 20) == 5
    assert ExcelFunctions.max(10, 5, 20) == 20

    # Criteria functions
    data_range = [10, 20, 30, 40, 50]
    assert ExcelFunctions.sumif(data_range, ">25") == 120
    assert ExcelFunctions.countif(data_range, ">25") == 3

    # XLOOKUP
    keys = ["A", "B", "C"]
    vals = [100, 200, 300]
    assert ExcelFunctions.xlookup("B", keys, vals) == 200
    assert ExcelFunctions.xlookup("Z", keys, vals, if_not_found="Not Found") == "Not Found"

    # Edge cases: blanks and errors
    assert ExcelFunctions.countblank(["A", "", None, 10]) == 2
    assert ExcelFunctions.iferror("#DIV/0!", 0) == 0

    # Evaluator formula test
    res = FormulaEvaluator.evaluate_formula("=SUM(10, 20, 30)")
    assert res["success"] is True
    assert res["result"] == 60

# --- Test 13: Unsupported column and ambiguous request handling ---
def test_unsupported_and_ambiguous_queries():
    # Ambiguous or non-existent column
    active_id = dataset_manager.get_active_dataset_id()
    resp = client.post("/api/formulas/evaluate", json={
        "formula": "=SUM([NonExistentColumnXYZ])",
        "dataset_id": active_id
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert "#REF!" in data.get("error_code", "")

# --- Test 14: All major API endpoints check ---
def test_api_endpoints_health_and_registry():
    # Health
    r1 = client.get("/api/health")
    assert r1.status_code == 200
    assert r1.json()["status"] == "healthy"

    # Registry
    r2 = client.get("/api/formulas/registry")
    assert r2.status_code == 200
    assert r2.json()["total_functions"] >= 40

    # SQL Tables
    r3 = client.get("/api/sql/tables")
    assert r3.status_code == 200
    assert "tables" in r3.json()
