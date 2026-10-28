import time
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.dataset_manager import dataset_manager
from app.reports.excel_exporter import ExcelExporter
from app.reports.pdf_exporter import PDFExporter
from app.config import settings

router = APIRouter(prefix="/api/reports", tags=["Report & Export Centre"])

class ExportPdfRequest(BaseModel):
    title: Optional[str] = "Executive Analysis Summary"
    narrative: Optional[dict] = None
    kpis: Optional[list] = None

@router.get("/export/csv/{dataset_id}")
def export_csv(dataset_id: str):
    try:
        df = dataset_manager.get_dataset_dataframe(dataset_id)
        meta = dataset_manager.get_dataset(dataset_id)
        clean_name = meta["filename"].split(".")[0] if meta else "dataset"
        export_file = settings.EXPORT_DIR / f"{clean_name}_exported_{int(time.time())}.csv"
        df.to_csv(export_file, index=False)
        return FileResponse(export_file, media_type="text/csv", filename=export_file.name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV export failed: {str(e)}")

@router.get("/export/excel/{dataset_id}")
def export_excel(dataset_id: str):
    try:
        df = dataset_manager.get_dataset_dataframe(dataset_id)
        meta = dataset_manager.get_dataset(dataset_id)
        title = meta["filename"] if meta else "Dataset Report"
        path = ExcelExporter.export_dataset_report(df, report_title=title, metadata=meta)
        return FileResponse(
            path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=path.name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Excel export failed: {str(e)}")

@router.post("/export/pdf/{dataset_id}")
def export_pdf(dataset_id: str, req: ExportPdfRequest):
    try:
        meta = dataset_manager.get_dataset(dataset_id)
        if not meta:
            raise HTTPException(status_code=404, detail="Dataset not found")

        path = PDFExporter.export_summary_pdf(
            title=req.title or "Executive Analysis Report",
            kpis=req.kpis or [],
            narrative=req.narrative or {},
            row_count=meta["row_count"],
            table_name=meta["table_name"]
        )
        return FileResponse(path, media_type="application/pdf", filename=path.name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF export failed: {str(e)}")
