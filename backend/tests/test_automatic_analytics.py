import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.main import app
from app.core.dataset_manager import dataset_manager


client = TestClient(app)


def test_automatic_analysis_supports_segments_and_relationships():
    dataset = dataset_manager.generate_sample_dataset("retail_sales", 80)

    segments = client.post("/api/analytics/automatic", json={
        "dataset_id": dataset["id"],
        "columns": ["Region", "Sales"]
    })
    assert segments.status_code == 200
    assert segments.json()["analysis_type"] == "segments"
    assert segments.json()["table"]["rows"]
    assert segments.json()["chart"]["data"]

    relationship = client.post("/api/analytics/automatic", json={
        "dataset_id": dataset["id"],
        "columns": ["Sales", "Profit"]
    })
    assert relationship.status_code == 200
    assert relationship.json()["analysis_type"] == "relationship"
    assert "Correlation describes association, not causation." in relationship.json()["summary"]

    multi_measure = client.post("/api/analytics/automatic", json={
        "dataset_id": dataset["id"],
        "columns": ["Sales", "Profit", "Quantity"]
    })
    assert multi_measure.status_code == 200
    assert len(multi_measure.json()["table"]["rows"]) == 3

    animated_scatter = client.post("/api/analytics/automatic", json={
        "dataset_id": dataset["id"],
        "columns": ["Sales", "Profit", "Quantity"],
        "date_column": "Order_Date"
    })
    assert animated_scatter.status_code == 200
    assert animated_scatter.json()["chart"]["play_key"] == "frame"
    assert len({point["frame"] for point in animated_scatter.json()["chart"]["data"]}) > 1

    multi_segment = client.post("/api/analytics/automatic", json={
        "dataset_id": dataset["id"],
        "columns": ["Region", "Category", "Sales", "Profit"]
    })
    assert multi_segment.status_code == 200
    assert multi_segment.json()["analysis_type"] == "segments"
    assert multi_segment.json()["table"]["rows"]

    multi_trend = client.post("/api/analytics/automatic", json={
        "dataset_id": dataset["id"],
        "columns": ["Order_Date", "Sales", "Profit"]
    })
    assert multi_trend.status_code == 200
    assert multi_trend.json()["analysis_type"] == "trend"
    assert len(multi_trend.json()["chart"]["y_keys"]) == 2


def test_cleaning_preserves_original_and_can_reset_working_copy():
    dataset = dataset_manager.generate_sample_dataset("retail_sales", 80)
    original_rows = dataset["row_count"]

    applied = client.post("/api/cleaning/duplicates/apply", json={"dataset_id": dataset["id"]})
    assert applied.status_code == 200
    assert applied.json()["dataset"]["row_count"] < original_rows

    quality = client.get(f"/api/cleaning/quality/{dataset['id']}")
    assert quality.status_code == 200
    assert quality.json()["modified"] is True
    assert quality.json()["original"]["rows"] == original_rows

    reset = client.post(f"/api/cleaning/reset/{dataset['id']}")
    assert reset.status_code == 200
    assert reset.json()["dataset"]["row_count"] == original_rows
    assert client.get(f"/api/cleaning/quality/{dataset['id']}").json()["modified"] is False


def test_dataset_queries_use_independent_duckdb_cursors():
    dataset = dataset_manager.generate_sample_dataset("retail_sales", 80)
    paginated = dataset_manager.get_paginated_data(dataset["id"], page=1, page_size=50)
    assert paginated["total_rows"] == dataset["row_count"]
    assert len(paginated["rows"]) == 50
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(
            lambda _: dataset_manager.get_dataset_dataframe(dataset["id"]).shape,
            range(24)
        ))
    assert all(shape == (dataset["row_count"], dataset["column_count"]) for shape in results)
