import os
import uuid
import json
import time
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

from app.config import settings
from app.core.duckdb_engine import duckdb_engine
from app.core.schema_profiler import SchemaProfiler

class DatasetManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatasetManager, cls).__new__(cls)
            cls._instance._datasets = {} # dataset_id -> metadata
            cls._active_dataset_id = None
        return cls._instance

    def list_datasets(self) -> List[Dict[str, Any]]:
        return list(self._datasets.values())

    def get_dataset(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        return self._datasets.get(dataset_id)

    def get_active_dataset_id(self) -> Optional[str]:
        return self._active_dataset_id

    def set_active_dataset_id(self, dataset_id: str) -> bool:
        if dataset_id in self._datasets:
            self._active_dataset_id = dataset_id
            return True
        return False

    def load_dataset_from_file(
        self,
        file_path: Path,
        original_filename: str,
        sheet_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Loads CSV, Excel, Parquet, or JSON into Pandas/DuckDB and computes schema profile.
        """
        dataset_id = str(uuid.uuid4())[:8]
        ext = file_path.suffix.lower()
        
        available_sheets = []
        df = None

        if ext == ".csv":
            df = self._read_csv_safe(file_path)
        elif ext in [".xlsx", ".xls"]:
            excel_file = pd.ExcelFile(file_path)
            available_sheets = excel_file.sheet_names
            target_sheet = sheet_name if (sheet_name and sheet_name in available_sheets) else available_sheets[0]
            df = pd.read_excel(file_path, sheet_name=target_sheet)
        elif ext == ".parquet":
            df = pd.read_parquet(file_path)
        elif ext == ".json":
            df = pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        # Ensure valid string column names
        df.columns = [str(c).strip() for c in df.columns]

        # Register in DuckDB
        table_name = f"ds_{dataset_id}"
        duckdb_engine.register_dataframe(table_name, df)
        original_table_name = f"original_{table_name}"
        duckdb_engine.register_dataframe(original_table_name, df.copy())

        # Profile schema
        profile = SchemaProfiler.profile_dataframe(df, table_name=table_name)

        meta = {
            "id": dataset_id,
            "table_name": table_name,
            "original_table_name": original_table_name,
            "filename": original_filename,
            "file_path": str(file_path),
            "file_size_bytes": file_path.stat().st_size if file_path.exists() else 0,
            "format": ext.replace(".", "").upper(),
            "selected_sheet": sheet_name or (available_sheets[0] if available_sheets else None),
            "available_sheets": available_sheets,
            "row_count": len(df),
            "column_count": len(df.columns),
            "created_at": time.time(),
            "profile": profile
        }

        self._datasets[dataset_id] = meta
        if self._active_dataset_id is None:
            self._active_dataset_id = dataset_id

        return meta

    def inspect_excel_sheets(self, file_path: Path) -> List[str]:
        """Inspect sheets available in an Excel workbook."""
        try:
            excel = pd.ExcelFile(file_path)
            return excel.sheet_names
        except Exception as e:
            raise ValueError(f"Failed to read Excel workbook: {str(e)}")

    def get_dataset_dataframe(self, dataset_id: str) -> pd.DataFrame:
        """Fetch active dataframe from DuckDB."""
        meta = self.get_dataset(dataset_id)
        if not meta:
            raise KeyError(f"Dataset {dataset_id} not found.")
        table_name = meta["table_name"]
        with duckdb_engine.connection_lock:
            return duckdb_engine.con.sql(f"SELECT * FROM {table_name}").df()

    def get_original_dataframe(self, dataset_id: str) -> pd.DataFrame:
        meta = self.get_dataset(dataset_id)
        if not meta:
            raise KeyError(f"Dataset {dataset_id} not found.")
        with duckdb_engine.connection_lock:
            return duckdb_engine.con.sql(
                f"SELECT * FROM {meta['original_table_name']}"
            ).df()

    def reset_dataset_to_original(self, dataset_id: str) -> Dict[str, Any]:
        original_df = self.get_original_dataframe(dataset_id)
        return self.update_dataset_dataframe(
            dataset_id, original_df, description="Reset to original dataset"
        )

    def update_dataset_dataframe(self, dataset_id: str, new_df: pd.DataFrame, description: str = "") -> Dict[str, Any]:
        """Update dataset with a cleaned or transformed DataFrame and refresh schema."""
        meta = self.get_dataset(dataset_id)
        if not meta:
            raise KeyError(f"Dataset {dataset_id} not found.")
        
        table_name = meta["table_name"]
        duckdb_engine.register_dataframe(table_name, new_df)
        
        # Re-profile
        profile = SchemaProfiler.profile_dataframe(new_df, table_name=table_name)
        
        meta["row_count"] = len(new_df)
        meta["column_count"] = len(new_df.columns)
        meta["profile"] = profile
        meta["last_updated_at"] = time.time()
        meta["last_action"] = description

        return meta

    def get_paginated_data(
        self,
        dataset_id: str,
        page: int = 1,
        page_size: int = 50,
        sort_by: Optional[str] = None,
        sort_desc: bool = False,
        search_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """Server-side virtualized data pagination using DuckDB."""
        meta = self.get_dataset(dataset_id)
        if not meta:
            raise KeyError(f"Dataset {dataset_id} not found.")
        
        table_name = meta["table_name"]
        cols = [c["name"] for c in meta["profile"]["columns"]]
        
        where_clauses = []
        if search_query and search_query.strip():
            clean_search = search_query.strip().replace("'", "''")
            # Search across string columns
            str_cols = [c["name"] for c in meta["profile"]["columns"] if c["inferred_type"] in ["string", "categorical", "identifier"]]
            if str_cols:
                clauses = [f"CAST(\"{col}\" AS VARCHAR) ILIKE '%{clean_search}%'" for col in str_cols[:8]]
                where_clauses.append(f"({' OR '.join(clauses)})")

        where_stmt = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        # Get filtered count
        count_sql = f"SELECT COUNT(*) FROM {table_name} {where_stmt}"
        with duckdb_engine.connection_lock:
            total_filtered_rows = duckdb_engine.con.sql(count_sql).fetchall()[0][0]

        order_stmt = ""
        if sort_by and sort_by in cols:
            direction = "DESC" if sort_desc else "ASC"
            order_stmt = f"ORDER BY \"{sort_by}\" {direction} NULLS LAST"

        offset = max(0, (page - 1) * page_size)
        query = f"SELECT * FROM {table_name} {where_stmt} {order_stmt} LIMIT {page_size} OFFSET {offset}"
        
        query_result = duckdb_engine.execute_query(query, max_rows=page_size)

        return {
            "dataset_id": dataset_id,
            "page": page,
            "page_size": page_size,
            "total_rows": total_filtered_rows,
            "total_pages": max(1, (total_filtered_rows + page_size - 1) // page_size),
            "columns": query_result["columns"],
            "rows": query_result["rows"]
        }

    def _read_csv_safe(self, file_path: Path) -> pd.DataFrame:
        """Robust CSV reader with encoding fallback and delimiter sniffing."""
        encodings = ["utf-8", "latin1", "cp1252", "iso-8859-1"]
        delimiters = [",", ";", "\t", "|"]
        
        # Detect delimiter using sample
        sample_bytes = b""
        with open(file_path, "rb") as f:
            sample_bytes = f.read(16384)

        chosen_encoding = "utf-8"
        for enc in encodings:
            try:
                sample_text = sample_bytes.decode(enc)
                chosen_encoding = enc
                break
            except UnicodeDecodeError:
                continue

        # Count candidate delimiters in sample
        delimiter = ","
        sample_text = sample_bytes.decode(chosen_encoding, errors="ignore")
        counts = {d: sample_text.count(d) for d in delimiters}
        if counts:
            delimiter = max(counts, key=counts.get)

        try:
            return pd.read_csv(file_path, sep=delimiter, encoding=chosen_encoding, low_memory=False)
        except Exception:
            # Fallback to python engine
            return pd.read_csv(file_path, sep=None, engine="python", encoding=chosen_encoding)

    def generate_sample_dataset(self, sample_type: str = "retail_sales", row_count: int = 5000) -> Dict[str, Any]:
        """
        Generates realistic production sample datasets for instant demonstration and testing.
        Supported types: 'retail_sales', 'financial_multisheet', 'hr_attrition', '100k_benchmark'.
        """
        np.random.seed(42)
        n = min(row_count, 150000)

        if sample_type == "retail_sales" or sample_type == "100k_benchmark":
            if sample_type == "100k_benchmark":
                n = 100000

            regions = ["South", "North", "East", "West", "Central"]
            categories = ["Technology", "Furniture", "Office Supplies"]
            sub_cats = {
                "Technology": ["Phones", "Laptops", "Accessories", "Copiers"],
                "Furniture": ["Chairs", "Tables", "Bookcases", "Furnishings"],
                "Office Supplies": ["Paper", "Binders", "Storage", "Appliances", "Art"]
            }
            cities = ["Chennai", "Bangalore", "Mumbai", "Delhi", "Hyderabad", "Kolkata", "Pune", "Coimbatore"]
            customer_segments = ["Consumer", "Corporate", "Home Office"]

            dates = pd.date_range(start="2024-01-01", periods=365, freq="D")
            
            chosen_cat = np.random.choice(categories, size=n)
            chosen_sub = [np.random.choice(sub_cats[c]) for c in chosen_cat]
            chosen_dates = np.random.choice(dates, size=n)
            formatted_dates = pd.to_datetime(chosen_dates).strftime("%Y-%m-%d").tolist()
            quantities = np.random.randint(1, 15, size=n)
            unit_prices = np.round(np.random.uniform(15.0, 1200.0, size=n), 2)
            discounts = np.random.choice([0.0, 0.05, 0.1, 0.15, 0.2, 0.3], size=n, p=[0.4, 0.2, 0.15, 0.1, 0.1, 0.05])
            sales = np.round(quantities * unit_prices * (1.0 - discounts), 2)
            
            # Profit margins varying by category, some negative
            margin_factor = np.random.normal(0.22, 0.18, size=n)
            profits = np.round(sales * margin_factor, 2)

            df = pd.DataFrame({
                "Order_ID": [f"ORD-{100000 + i}" for i in range(n)],
                "Order_Date": formatted_dates,
                "Customer_ID": [f"CUST-{np.random.randint(1001, 1001 + int(n*0.15))}" for _ in range(n)],
                "Customer_Segment": np.random.choice(customer_segments, size=n),
                "City": np.random.choice(cities, size=n),
                "Region": np.random.choice(regions, size=n),
                "Category": chosen_cat,
                "Sub_Category": chosen_sub,
                "Quantity": quantities,
                "Unit_Price": unit_prices,
                "Discount": discounts,
                "Sales": sales,
                "Profit": profits
            })

            # Add a few deliberate duplicate records for testing deduplication
            if n >= 50:
                duplicates = df.iloc[:5].copy()
                df = pd.concat([df, duplicates], ignore_index=True)

            file_path = settings.SAMPLES_DIR / f"retail_sales_{n}.csv"
            df.to_csv(file_path, index=False)
            return self.load_dataset_from_file(file_path, original_filename=f"Global_Retail_Sales_{n}.csv")

        elif sample_type == "financial_multisheet":
            # Multi-sheet Excel model
            months = ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06", 
                      "2024-07", "2024-08", "2024-09", "2024-10", "2024-11", "2024-12"]
            
            df_revenue = pd.DataFrame({
                "Month": months,
                "Software_Subscriptions": [120000, 125000, 132000, 140000, 145000, 155000, 160000, 168000, 175000, 185000, 195000, 210000],
                "Consulting_Services": [45000, 48000, 52000, 49000, 53000, 58000, 60000, 62000, 65000, 70000, 72000, 80000],
                "Hardware_Sales": [30000, 28000, 35000, 42000, 38000, 45000, 40000, 43000, 48000, 50000, 55000, 62000],
                "Total_Revenue": [195000, 201000, 219000, 231000, 236000, 258000, 260000, 273000, 288000, 305000, 322000, 352000]
            })

            df_expenses = pd.DataFrame({
                "Month": months,
                "R_and_D": [50000, 52000, 55000, 56000, 58000, 60000, 62000, 63000, 65000, 68000, 70000, 75000],
                "Sales_and_Marketing": [40000, 42000, 45000, 48000, 50000, 52000, 55000, 58000, 60000, 65000, 68000, 72000],
                "General_and_Admin": [25000, 25500, 26000, 26500, 27000, 27500, 28000, 28500, 29000, 29500, 30000, 31000],
                "Total_Opex": [115000, 119500, 126000, 130500, 135000, 139500, 145000, 149500, 154000, 162500, 168000, 178000]
            })

            file_path = settings.SAMPLES_DIR / "financial_model_multisheet.xlsx"
            with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                df_revenue.to_excel(writer, sheet_name="Revenue_Streams", index=False)
                df_expenses.to_excel(writer, sheet_name="Operating_Expenses", index=False)

            return self.load_dataset_from_file(file_path, original_filename="Financial_Model_MultiSheet.xlsx", sheet_name="Revenue_Streams")

        elif sample_type == "hr_attrition":
            departments = ["Engineering", "Sales", "Human Resources", "Finance", "Marketing", "Product"]
            education = ["Bachelor", "Master", "Doctorate", "Diploma"]
            
            df = pd.DataFrame({
                "Employee_ID": [f"EMP-{2000 + i}" for i in range(1200)],
                "Department": np.random.choice(departments, size=1200),
                "Education": np.random.choice(education, size=1200, p=[0.55, 0.35, 0.05, 0.05]),
                "Years_at_Company": np.random.randint(1, 15, size=1200),
                "Monthly_Salary": np.round(np.random.normal(7500, 2200, size=1200), 2),
                "Performance_Score": np.random.choice([1, 2, 3, 4, 5], size=1200, p=[0.05, 0.15, 0.50, 0.20, 0.10]),
                "OverTime": np.random.choice(["Yes", "No"], size=1200, p=[0.28, 0.72]),
                "Attrition": np.random.choice(["Yes", "No"], size=1200, p=[0.16, 0.84])
            })
            file_path = settings.SAMPLES_DIR / "hr_attrition_workforce.csv"
            df.to_csv(file_path, index=False)
            return self.load_dataset_from_file(file_path, original_filename="HR_Workforce_Attrition.csv")

        return self.generate_sample_dataset("retail_sales", 5000)

dataset_manager = DatasetManager()
