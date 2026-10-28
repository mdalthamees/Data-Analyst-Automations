import shutil
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from pydantic import BaseModel

from app.config import settings
from app.core.dataset_manager import dataset_manager

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])

class GenerateSampleRequest(BaseModel):
    sample_type: str = "retail_sales" # 'retail_sales', 'financial_multisheet', 'hr_attrition', '100k_benchmark'
    row_count: int = 5000

@router.get("/")
def list_datasets():
    datasets = dataset_manager.list_datasets()
    active_id = dataset_manager.get_active_dataset_id()
    return {
        "datasets": datasets,
        "active_dataset_id": active_id
    }

@router.get("/{dataset_id}")
def get_dataset(dataset_id: str):
    meta = dataset_manager.get_dataset(dataset_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return meta

@router.post("/active/{dataset_id}")
def set_active_dataset(dataset_id: str):
    success = dataset_manager.set_active_dataset_id(dataset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"success": True, "active_dataset_id": dataset_id}

@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    sheet_name: Optional[str] = Form(None)
):
    ext = Path(file.filename).suffix.lower()
    if ext not in [".csv", ".xlsx", ".xls", ".parquet", ".json"]:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}'. Allowed: CSV, XLSX, XLS, PARQUET, JSON")

    dest_path = settings.UPLOAD_DIR / file.filename
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Check if Excel with multiple sheets
        if ext in [".xlsx", ".xls"] and not sheet_name:
            sheets = dataset_manager.inspect_excel_sheets(dest_path)
            if len(sheets) > 1:
                # Still load first sheet, but return sheets list for switching
                meta = dataset_manager.load_dataset_from_file(dest_path, original_filename=file.filename, sheet_name=sheets[0])
                meta["has_multiple_sheets"] = True
                meta["available_sheets"] = sheets
                return meta

        meta = dataset_manager.load_dataset_from_file(dest_path, original_filename=file.filename, sheet_name=sheet_name)
        return meta
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process dataset: {str(e)}")

@router.post("/sample")
def generate_sample(req: GenerateSampleRequest):
    try:
        meta = dataset_manager.generate_sample_dataset(req.sample_type, req.row_count)
        return meta
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate sample dataset: {str(e)}")

@router.get("/{dataset_id}/data")
def get_dataset_data(
    dataset_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=5, le=500),
    sort_by: Optional[str] = Query(None),
    sort_desc: bool = Query(False),
    search: Optional[str] = Query(None)
):
    try:
        data = dataset_manager.get_paginated_data(
            dataset_id=dataset_id,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_desc=sort_desc,
            search_query=search
        )
        return data
    except KeyError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query data: {str(e)}")
