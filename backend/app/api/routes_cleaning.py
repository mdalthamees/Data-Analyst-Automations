from typing import Optional, List, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import numpy as np
import pandas as pd

from app.core.dataset_manager import dataset_manager
from app.cleaning.cleaning_studio import CleaningStudio
from app.cleaning.transformation_history import TransformationHistory

router = APIRouter(prefix="/api/cleaning", tags=["Data Cleaning Studio"])

# In-memory history trackers per dataset: dataset_id -> TransformationHistory
histories = {}

def get_or_create_history(dataset_id: str) -> TransformationHistory:
    if dataset_id not in histories:
        df = dataset_manager.get_dataset_dataframe(dataset_id)
        histories[dataset_id] = TransformationHistory(df)
    return histories[dataset_id]

# Request Schemas
class PreviewDuplicatesRequest(BaseModel):
    dataset_id: Optional[str] = None
    subset_columns: Optional[List[str]] = None

class ApplyDuplicatesRequest(BaseModel):
    dataset_id: Optional[str] = None
    subset_columns: Optional[List[str]] = None
    keep: str = "first"

class PreviewImputeRequest(BaseModel):
    dataset_id: Optional[str] = None
    column: str
    strategy: str = "mean" # 'mean', 'median', 'mode', 'constant', 'drop'
    fill_value: Optional[Any] = None

class ApplyImputeRequest(BaseModel):
    dataset_id: Optional[str] = None
    column: str
    strategy: str = "mean"
    fill_value: Optional[Any] = None

class PreviewOutliersRequest(BaseModel):
    dataset_id: Optional[str] = None
    column: str
    method: str = "iqr"
    threshold: float = 1.5

class ApplyOutliersRequest(BaseModel):
    dataset_id: Optional[str] = None
    column: str
    action: str = "cap" # 'cap', 'drop', 'flag'
    method: str = "iqr"
    threshold: float = 1.5

@router.post("/duplicates/preview")
def preview_duplicates(req: PreviewDuplicatesRequest):
    ds_id = req.dataset_id or dataset_manager.get_active_dataset_id()
    df = dataset_manager.get_dataset_dataframe(ds_id)
    return CleaningStudio.preview_remove_duplicates(df, req.subset_columns)

@router.post("/duplicates/apply")
def apply_duplicates(req: ApplyDuplicatesRequest):
    ds_id = req.dataset_id or dataset_manager.get_active_dataset_id()
    df = dataset_manager.get_dataset_dataframe(ds_id)
    clean_df, summary = CleaningStudio.apply_remove_duplicates(df, req.subset_columns, req.keep)
    
    # Push to history
    hist = get_or_create_history(ds_id)
    hist.push(clean_df, f"Removed {summary.get('removed_rows', 0)} duplicates")

    # Update dataset
    updated_meta = dataset_manager.update_dataset_dataframe(ds_id, clean_df, description=summary["action"])
    return {
        "success": True,
        "summary": summary,
        "dataset": updated_meta
    }

@router.post("/impute/preview")
def preview_impute(req: PreviewImputeRequest):
    ds_id = req.dataset_id or dataset_manager.get_active_dataset_id()
    df = dataset_manager.get_dataset_dataframe(ds_id)
    return CleaningStudio.preview_impute_missing(df, req.column, req.strategy, req.fill_value)

@router.post("/impute/apply")
def apply_impute(req: ApplyImputeRequest):
    ds_id = req.dataset_id or dataset_manager.get_active_dataset_id()
    df = dataset_manager.get_dataset_dataframe(ds_id)
    clean_df, summary = CleaningStudio.apply_impute_missing(df, req.column, req.strategy, req.fill_value)

    hist = get_or_create_history(ds_id)
    hist.push(clean_df, summary["action"])

    updated_meta = dataset_manager.update_dataset_dataframe(ds_id, clean_df, description=summary["action"])
    return {
        "success": True,
        "summary": summary,
        "dataset": updated_meta
    }

@router.post("/outliers/preview")
def preview_outliers(req: PreviewOutliersRequest):
    ds_id = req.dataset_id or dataset_manager.get_active_dataset_id()
    df = dataset_manager.get_dataset_dataframe(ds_id)
    return CleaningStudio.preview_detect_outliers(df, req.column, req.method, req.threshold)

@router.post("/outliers/apply")
def apply_outliers(req: ApplyOutliersRequest):
    ds_id = req.dataset_id or dataset_manager.get_active_dataset_id()
    df = dataset_manager.get_dataset_dataframe(ds_id)
    clean_df, summary = CleaningStudio.apply_handle_outliers(df, req.column, req.action, req.method, req.threshold)

    hist = get_or_create_history(ds_id)
    hist.push(clean_df, summary["action"])

    updated_meta = dataset_manager.update_dataset_dataframe(ds_id, clean_df, description=summary["action"])
    return {
        "success": True,
        "summary": summary,
        "dataset": updated_meta
    }

@router.post("/dates/standardize")
def standardize_dates(column: str, dataset_id: Optional[str] = None):
    ds_id = dataset_id or dataset_manager.get_active_dataset_id()
    df = dataset_manager.get_dataset_dataframe(ds_id)
    clean_df, summary = CleaningStudio.apply_standardize_dates(df, column)

    hist = get_or_create_history(ds_id)
    hist.push(clean_df, summary["action"])

    updated_meta = dataset_manager.update_dataset_dataframe(ds_id, clean_df, description=summary["action"])
    return {"success": True, "summary": summary, "dataset": updated_meta}

@router.post("/text/normalize")
def normalize_text(column: str, operation: str = "trim", dataset_id: Optional[str] = None):
    ds_id = dataset_id or dataset_manager.get_active_dataset_id()
    df = dataset_manager.get_dataset_dataframe(ds_id)
    clean_df, summary = CleaningStudio.apply_normalize_text(df, column, operation)

    hist = get_or_create_history(ds_id)
    hist.push(clean_df, summary["action"])

    updated_meta = dataset_manager.update_dataset_dataframe(ds_id, clean_df, description=summary["action"])
    return {"success": True, "summary": summary, "dataset": updated_meta}

@router.post("/undo/{dataset_id}")
def undo_transformation(dataset_id: str):
    hist = get_or_create_history(dataset_id)
    prev_df = hist.undo()
    if prev_df is None:
        raise HTTPException(status_code=400, detail="No previous transformation state available to undo.")
    updated_meta = dataset_manager.update_dataset_dataframe(dataset_id, prev_df, description="Undo Action")
    return {"success": True, "message": "Undone successfully", "dataset": updated_meta}

@router.post("/redo/{dataset_id}")
def redo_transformation(dataset_id: str):
    hist = get_or_create_history(dataset_id)
    next_df = hist.redo()
    if next_df is None:
        raise HTTPException(status_code=400, detail="No forward transformation state available to redo.")
    updated_meta = dataset_manager.update_dataset_dataframe(dataset_id, next_df, description="Redo Action")
    return {"success": True, "message": "Redone successfully", "dataset": updated_meta}

@router.get("/history/{dataset_id}")
def get_history(dataset_id: str):
    hist = get_or_create_history(dataset_id)
    return {"history": hist.get_audit_log()}


@router.get("/quality/{dataset_id}")
def get_quality_report(dataset_id: str):
    try:
        df = dataset_manager.get_dataset_dataframe(dataset_id)
        original = dataset_manager.get_original_dataframe(dataset_id)
        meta = dataset_manager.get_dataset(dataset_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Dataset not found")

    checks = []
    sensitive_terms = ("email", "phone", "mobile", "address", "ssn", "social_security", "passport", "birth", "customer_id")
    profiled_dates = {
        column.get("name")
        for column in (meta.get("profile", {}).get("columns", []) if meta else [])
        if column.get("role") == "date" or column.get("inferred_type") == "date"
    }
    for column in df.columns:
        series = df[column]
        non_null = series.dropna()
        distinct = int(series.nunique(dropna=True))
        numeric = pd.to_numeric(series, errors="coerce")
        normalized_numbers = series.astype("string").str.strip()
        normalized_numbers = normalized_numbers.str.replace(r"[$€£₹¥,%\s]", "", regex=True)
        normalized_numbers = normalized_numbers.str.replace(r"^\((.*)\)$", r"-\1", regex=True)
        normalized_numeric = pd.to_numeric(normalized_numbers, errors="coerce")
        numeric_like = bool(len(non_null) and normalized_numeric.notna().sum() / len(non_null) >= 0.8)
        invalid_dates = 0
        if column in profiled_dates or any(term in str(column).lower() for term in ("date", "time", "month", "year")):
            parsed_dates = pd.to_datetime(non_null, errors="coerce")
            invalid_dates = int(parsed_dates.isna().sum())
        category_variations = []
        if series.dtype == object or pd.api.types.is_string_dtype(series):
            labels = non_null.astype(str).str.strip()
            normalized = labels.str.casefold()
            variation_counts = pd.DataFrame({"label": labels, "normalized": normalized}).groupby("normalized")["label"].nunique()
            varied = variation_counts[variation_counts > 1].index
            category_variations = [
                labels[normalized == key].drop_duplicates().head(4).tolist()
                for key in list(varied[:5])
            ]
        outlier_count = 0
        infinite_count = 0
        negative_count = 0
        if numeric_like:
            valid = normalized_numeric.replace([np.inf, -np.inf], np.nan).dropna()
            infinite_count = int(np.isinf(normalized_numeric.to_numpy(dtype=float, na_value=np.nan)).sum())
            negative_count = int((valid < 0).sum())
            if len(valid) >= 4:
                q1, q3 = valid.quantile([0.25, 0.75])
                spread = q3 - q1
                outlier_count = int(((valid < q1 - 1.5 * spread) | (valid > q3 + 1.5 * spread)).sum())
        checks.append({
            "column": str(column),
            "missing_count": int(series.isna().sum()),
            "missing_percentage": round(float(series.isna().mean() * 100), 2) if len(series) else 0,
            "whitespace_count": int(series.astype("string").str.strip().ne(series.astype("string")).fillna(False).sum()),
            "distinct_count": distinct,
            "constant": distinct <= 1,
            "high_cardinality": bool(len(df) and distinct / len(df) > 0.8),
            "potentially_sensitive": any(term in str(column).lower() for term in sensitive_terms),
            "numeric_parse_failures": int((normalized_numeric.isna() & series.notna()).sum()) if numeric_like else 0,
            "formatted_numeric_values": int((numeric.isna() & normalized_numeric.notna() & series.notna()).sum()) if numeric_like else 0,
            "invalid_dates": invalid_dates,
            "infinite_count": infinite_count,
            "negative_count": negative_count,
            "outlier_count": outlier_count,
            "category_variations": category_variations
        })

    business_keys = []
    for key in (meta.get("profile", {}).get("candidate_primary_keys", []) if meta else []):
        if key in df.columns:
            business_keys.append({"columns": [key], "duplicate_rows": int(df.duplicated(subset=[key]).sum())})
    return {
        "original": {"rows": int(len(original)), "columns": int(len(original.columns))},
        "current": {"rows": int(len(df)), "columns": int(len(df.columns))},
        "modified": not original.equals(df),
        "duplicate_rows": int(df.duplicated().sum()),
        "empty_rows": int(df.isna().all(axis=1).sum()),
        "empty_columns": [str(column) for column in df.columns if df[column].isna().all()],
        "business_key_duplicates": business_keys,
        "checks": checks
    }


@router.post("/reset/{dataset_id}")
def reset_to_original(dataset_id: str):
    try:
        original = dataset_manager.get_original_dataframe(dataset_id)
        histories[dataset_id] = TransformationHistory(original)
        updated_meta = dataset_manager.reset_dataset_to_original(dataset_id)
        return {"success": True, "dataset": updated_meta}
    except KeyError:
        raise HTTPException(status_code=404, detail="Dataset not found")
