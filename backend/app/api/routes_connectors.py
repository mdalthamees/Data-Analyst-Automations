from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.transformations.data_connectors import DatabaseConnector

router = APIRouter(prefix="/api/connectors", tags=["Database Connectors"])

class TestConnectionRequest(BaseModel):
    db_type: str # 'sqlite', 'postgresql', 'mysql'
    host: Optional[str] = "localhost"
    port: Optional[int] = None
    database: str
    username: Optional[str] = ""
    password: Optional[str] = ""

class ImportTableRequest(BaseModel):
    db_type: str
    host: Optional[str] = "localhost"
    port: Optional[int] = None
    database: str
    table_name: str
    username: Optional[str] = ""
    password: Optional[str] = ""
    max_rows: Optional[int] = 50000

@router.post("/test")
def test_connection(req: TestConnectionRequest):
    return DatabaseConnector.test_connection(
        db_type=req.db_type,
        host=req.host,
        port=req.port,
        database=req.database,
        username=req.username,
        password=req.password
    )

@router.post("/import")
def import_table(req: ImportTableRequest):
    try:
        return DatabaseConnector.import_table_as_dataset(
            db_type=req.db_type,
            host=req.host,
            port=req.port,
            database=req.database,
            table_name=req.table_name,
            username=req.username,
            password=req.password,
            max_rows=req.max_rows or 50000
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Table import failed: {str(e)}")
