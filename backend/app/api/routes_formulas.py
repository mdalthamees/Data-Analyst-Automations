from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.dataset_manager import dataset_manager
from app.formula_engine.evaluator import FormulaEvaluator
from app.formula_engine.registry import FUNCTION_REGISTRY
from app.formula_engine.nl_formula_mapper import NLFormulaMapper

router = APIRouter(prefix="/api/formulas", tags=["Excel Formula Engine"])

class EvaluateFormulaRequest(BaseModel):
    formula: str
    dataset_id: Optional[str] = None

class MapNLFormulaRequest(BaseModel):
    query: str
    dataset_id: Optional[str] = None

@router.get("/registry")
def get_registry():
    """List all supported Excel functions, their syntax, categories, and support status."""
    by_family = {}
    for name, info in FUNCTION_REGISTRY.items():
        fam = info["family"]
        if fam not in by_family:
            by_family[fam] = []
        by_family[fam].append({"name": name, **info})

    return {
        "total_functions": len(FUNCTION_REGISTRY),
        "functions_by_family": by_family,
        "all_functions": [{"name": k, **v} for k, v in FUNCTION_REGISTRY.items()]
    }

@router.post("/evaluate")
def evaluate_formula(req: EvaluateFormulaRequest):
    df = None
    ds_id = req.dataset_id or dataset_manager.get_active_dataset_id()
    if ds_id:
        try:
            df = dataset_manager.get_dataset_dataframe(ds_id)
        except Exception:
            pass

    return FormulaEvaluator.evaluate_formula(req.formula, df=df)

@router.post("/map-natural-language")
def map_nl(req: MapNLFormulaRequest):
    ds_id = req.dataset_id or dataset_manager.get_active_dataset_id()
    columns = []
    if ds_id:
        meta = dataset_manager.get_dataset(ds_id)
        if meta:
            columns = [c["name"] for c in meta["profile"]["columns"]]

    mapping = NLFormulaMapper.map_natural_language_to_formula(req.query, columns)
    
    # If matched, evaluate it immediately
    eval_result = None
    if mapping.get("matched") and ds_id:
        df = dataset_manager.get_dataset_dataframe(ds_id)
        eval_result = FormulaEvaluator.evaluate_formula(mapping["formula"], df=df)

    return {
        "mapping": mapping,
        "evaluation": eval_result
    }
