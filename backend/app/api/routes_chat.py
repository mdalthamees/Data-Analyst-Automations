from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.dataset_manager import dataset_manager
from app.ai.conversational_analyst import conversational_analyst

router = APIRouter(prefix="/api/chat", tags=["AI Analyst Chat"])

class ChatAskRequest(BaseModel):
    query: str
    session_id: Optional[str] = "default_session"
    dataset_id: Optional[str] = None

@router.post("/ask")
def ask_analyst(req: ChatAskRequest):
    dataset_id = req.dataset_id or dataset_manager.get_active_dataset_id()
    if not dataset_id:
        raise HTTPException(status_code=400, detail="No active dataset selected. Please upload or select a dataset first.")

    try:
        response = conversational_analyst.ask(
            session_id=req.session_id,
            dataset_id=dataset_id,
            query=req.query
        )
        return response
    except KeyError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
