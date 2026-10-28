import duckdb
import time
import re
import threading
from typing import Dict, Any, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class DuckDBEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DuckDBEngine, cls).__new__(cls)
            cls._instance._init_engine()
        return cls._instance

    def _init_engine(self):
        # In-memory analytical DuckDB instance with configured threads & memory
        self.con = duckdb.connect(database=":memory:")
        self.connection_lock = threading.RLock()
        self.con.execute("PRAGMA threads=4;")
        self.con.execute("PRAGMA memory_limit='2GB';")
        self._registered_tables = {}
        logger.info("DuckDB engine initialized successfully.")

    def register_dataframe(self, table_name: str, df):
        """Register a Pandas or Polars DataFrame into DuckDB."""
        safe_name = self._sanitize_identifier(table_name)
        # Drop if exists
        with self.connection_lock:
            self.con.execute(f"DROP VIEW IF EXISTS {safe_name};")
            self.con.register(safe_name, df)
            self._registered_tables[safe_name] = {
                "type": "dataframe",
                "registered_at": time.time()
            }
        return safe_name

    def register_parquet(self, table_name: str, parquet_path: str):
        """Register a Parquet file as a DuckDB view."""
        safe_name = self._sanitize_identifier(table_name)
        norm_path = parquet_path.replace("\\", "/")
        with self.connection_lock:
            self.con.execute(f"CREATE OR REPLACE VIEW {safe_name} AS SELECT * FROM read_parquet('{norm_path}');")
            self._registered_tables[safe_name] = {
                "type": "parquet",
                "path": parquet_path,
                "registered_at": time.time()
            }
        return safe_name

    def execute_query(
        self,
        query: str,
        params: Optional[List[Any]] = None,
        max_rows: int = 1000,
        enforce_readonly: bool = True
    ) -> Dict[str, Any]:
        """
        Execute an analytical SQL query with safeguards, timing, and formatting.
        """
        clean_query = query.strip().rstrip(";")
        
        # Enforce read-only if requested
        if enforce_readonly:
            upper_q = clean_query.upper()
            forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "ATTACH", "COPY", "INSTALL", "LOAD", "PRAGMA"]
            for word in forbidden:
                # Check keyword boundary
                if re.search(rf"\b{word}\b", upper_q):
                    raise ValueError(f"Write or administrative command '{word}' is not permitted in read-only mode.")

        start_time = time.perf_counter()
        try:
            with self.connection_lock:
                rel = self.con.sql(clean_query, params=params) if params else self.con.sql(clean_query)
            
                # Fetch column metadata
                columns = rel.columns
                col_types = [str(t) for t in rel.types]

                # Limit rows for preview/safety
                limited_rel = rel.limit(max_rows + 1)
                rows = limited_rel.fetchall()
            
            has_more = len(rows) > max_rows
            if has_more:
                rows = rows[:max_rows]

            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            
            # Convert values to JSON-serializable types
            serialized_rows = []
            for row in rows:
                serialized_rows.append([self._serialize_val(val) for val in row])

            return {
                "success": True,
                "columns": columns,
                "types": col_types,
                "rows": serialized_rows,
                "row_count": len(serialized_rows),
                "has_more": has_more,
                "execution_time_ms": elapsed_ms
            }
        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return {
                "success": False,
                "error": str(e),
                "columns": [],
                "rows": [],
                "row_count": 0,
                "execution_time_ms": elapsed_ms
            }

    def explain_query(self, query: str) -> str:
        """Get the execution plan for a SQL query."""
        try:
            with self.connection_lock:
                res = self.con.sql(f"EXPLAIN {query}").fetchall()
            if res and len(res) > 0:
                return "\n".join([str(r[1]) if len(r) > 1 else str(r[0]) for r in res])
            return "No plan available"
        except Exception as e:
            return f"Error explaining query: {str(e)}"

    def list_tables(self) -> List[str]:
        """List all registered tables and views in DuckDB."""
        try:
            with self.connection_lock:
                res = self.con.sql("SHOW TABLES;").fetchall()
            return [r[0] for r in res]
        except Exception:
            return list(self._registered_tables.keys())

    def get_table_schema(self, table_name: str) -> List[Dict[str, str]]:
        """Return schema columns and types for a table."""
        safe_name = self._sanitize_identifier(table_name)
        with self.connection_lock:
            res = self.con.sql(f"DESCRIBE {safe_name};").fetchall()
        return [{"column_name": r[0], "column_type": str(r[1]), "null": str(r[2])} for r in res]

    def _sanitize_identifier(self, name: str) -> str:
        clean = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        if clean and clean[0].isdigit():
            clean = f"t_{clean}"
        return clean or "table_default"

    def _serialize_val(self, val: Any) -> Any:
        import datetime
        import numpy as np
        if val is None:
            return None
        if isinstance(val, (datetime.date, datetime.datetime)):
            return val.isoformat()
        if isinstance(val, (np.integer, np.int64, np.int32)):
            return int(val)
        if isinstance(val, (np.floating, np.float64, np.float32)):
            if np.isnan(val) or np.isinf(val):
                return None
            return float(val)
        if isinstance(val, bytes):
            return str(val)
        return val

duckdb_engine = DuckDBEngine()
