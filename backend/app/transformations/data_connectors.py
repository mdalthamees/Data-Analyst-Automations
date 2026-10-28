import time
from typing import Dict, Any, List, Optional
import sqlalchemy
from sqlalchemy import create_engine, inspect, text
import pandas as pd

from app.core.dataset_manager import dataset_manager

class DatabaseConnector:
    """
    Enterprise Data Source Connectors:
    Provides read-only connections to SQLite, PostgreSQL, and MySQL.
    Tests credentials, introspects tables, and extracts data into DataPilot.
    """

    @classmethod
    def test_connection(
        cls,
        db_type: str,
        host: Optional[str] = "localhost",
        port: Optional[int] = None,
        database: str = "",
        username: Optional[str] = "",
        password: Optional[str] = ""
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()
        conn_str = cls._build_connection_string(db_type, host, port, database, username, password)

        try:
            engine = create_engine(conn_str, pool_pre_ping=True, connect_args={"timeout": 5} if db_type == "sqlite" else {})
            with engine.connect() as conn:
                conn.execute(text("SELECT 1;"))
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            
            # List tables
            inspector = inspect(engine)
            tables = inspector.get_table_names()

            return {
                "success": True,
                "message": f"Successfully connected to {db_type.upper()} database '{database}'.",
                "tables": tables,
                "table_count": len(tables),
                "latency_ms": elapsed_ms
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Connection failed: {str(e)}",
                "latency_ms": round((time.perf_counter() - start_time) * 1000, 2)
            }

    @classmethod
    def import_table_as_dataset(
        cls,
        db_type: str,
        host: Optional[str],
        port: Optional[int],
        database: str,
        table_name: str,
        username: Optional[str] = "",
        password: Optional[str] = "",
        max_rows: int = 50000
    ) -> Dict[str, Any]:
        conn_str = cls._build_connection_string(db_type, host, port, database, username, password)
        engine = create_engine(conn_str)
        
        # Read limited rows safely
        clean_table = table_name.replace("'", "").replace(";", "")
        query = f"SELECT * FROM {clean_table} LIMIT {max_rows}"
        df = pd.read_sql(query, con=engine)
        
        # Save temporary CSV and register
        from app.config import settings
        temp_path = settings.UPLOAD_DIR / f"db_{clean_table}_{int(time.time())}.csv"
        df.to_csv(temp_path, index=False)

        return dataset_manager.load_dataset_from_file(
            temp_path,
            original_filename=f"{database}.{clean_table} ({db_type.upper()})"
        )

    @classmethod
    def _build_connection_string(
        cls, db_type: str, host: Optional[str], port: Optional[int], database: str, user: Optional[str], password: Optional[str]
    ) -> str:
        db_low = db_type.lower()
        if db_low == "sqlite":
            return f"sqlite:///{database}"
        elif db_low == "postgresql" or db_low == "postgres":
            p = port or 5432
            return f"postgresql://{user}:{password}@{host}:{p}/{database}"
        elif db_low == "mysql":
            p = port or 3306
            return f"mysql+pymysql://{user}:{password}@{host}:{p}/{database}"
        raise ValueError(f"Unsupported database type '{db_type}'")
