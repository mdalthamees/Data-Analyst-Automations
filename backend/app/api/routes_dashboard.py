from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.dataset_manager import dataset_manager
from app.analytics.dashboard_generator import DashboardGenerator

router = APIRouter(prefix="/api/dashboard", tags=["Dashboards"])

class GenerateDashboardRequest(BaseModel):
    dataset_id: Optional[str] = None
    title: Optional[str] = "Executive Overview Dashboard"
    selected_measures: Optional[List[str]] = None
    selected_dimensions: Optional[List[str]] = None

@router.post("/generate")
def generate_dashboard(req: GenerateDashboardRequest):
    dataset_id = req.dataset_id or dataset_manager.get_active_dataset_id()
    if not dataset_id:
        raise HTTPException(status_code=400, detail="No active dataset selected.")

    try:
        dash = DashboardGenerator.generate_dashboard(
            dataset_id=dataset_id,
            title=req.title,
            selected_measures=req.selected_measures,
            selected_dimensions=req.selected_dimensions
        )
        return dash
    except KeyError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard generation failed: {str(e)}")
