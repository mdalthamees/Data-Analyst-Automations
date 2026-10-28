from typing import Optional, List, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.duckdb_engine import duckdb_engine

router = APIRouter(prefix="/api/sql", tags=["SQL Analytics Workspace"])

class ExecuteSQLRequest(BaseModel):
    query: str
    max_rows: Optional[int] = 500
    enforce_readonly: Optional[bool] = True

@router.post("/execute")
def execute_sql(req: ExecuteSQLRequest):
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    result = duckdb_engine.execute_query(
        query=req.query,
        max_rows=req.max_rows or 500,
        enforce_readonly=req.enforce_readonly if req.enforce_readonly is not None else True
    )
    return result

@router.post("/explain")
def explain_sql(req: ExecuteSQLRequest):
    plan = duckdb_engine.explain_query(req.query)
    return {"query": req.query, "plan": plan}

@router.get("/tables")
def list_tables():
    return {"tables": duckdb_engine.list_tables()}

@router.get("/schema/{table_name}")
def get_schema(table_name: str):
    try:
        return {"table_name": table_name, "schema": duckdb_engine.get_table_schema(table_name)}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Table schema error: {str(e)}")
