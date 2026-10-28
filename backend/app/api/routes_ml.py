from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.dataset_manager import dataset_manager
from app.analytics.forecasting_ml import ForecastingAndML

router = APIRouter(prefix="/api/ml", tags=["Forecasting & Machine Learning"])

class ForecastRequest(BaseModel):
    dataset_id: Optional[str] = None
    target_measure: str
    date_column: str
    periods_ahead: int = 6

class SegmentationRequest(BaseModel):
    dataset_id: Optional[str] = None
    features: List[str]
    n_clusters: int = 3

@router.post("/forecast")
def forecast(req: ForecastRequest):
    ds_id = req.dataset_id or dataset_manager.get_active_dataset_id()
    if not ds_id:
        raise HTTPException(status_code=400, detail="No active dataset selected.")

    try:
        return ForecastingAndML.generate_time_series_forecast(
            dataset_id=ds_id,
            target_measure=req.target_measure,
            date_column=req.date_column,
            periods_ahead=req.periods_ahead
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/segmentation")
def segment(req: SegmentationRequest):
    ds_id = req.dataset_id or dataset_manager.get_active_dataset_id()
    if not ds_id:
        raise HTTPException(status_code=400, detail="No active dataset selected.")

    try:
        return ForecastingAndML.run_customer_segmentation(
            dataset_id=ds_id,
            feature_columns=req.features,
            n_clusters=req.n_clusters
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
