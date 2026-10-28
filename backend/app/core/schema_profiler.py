import re
import datetime
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

class SchemaProfiler:
    """
    Intelligent Data Profiler:
    Infers data types, detects primary keys, identifies missing values and duplicates,
    classifies columns (measure, dimension, temporal, identifier), computes a 0-100 quality score,
    and generates automated analysis recommendations.
    """

    CURRENCY_REGEX = re.compile(r"^[\$\€\£\¥\₹]\s*-?\d+(?:,\d{3})*(?:\.\d+)?$|^-?\d+(?:,\d{3})*(?:\.\d+)?\s*[\$\€\£\¥\₹]$")
    PERCENT_REGEX = re.compile(r"^-?\d+(?:\.\d+)?\s*%$")
    DATE_REGEX = re.compile(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}(?:\s+\d{1,2}:\d{2}(?:\:\d{2})?)?$|^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$")

    @classmethod
    def profile_dataframe(cls, df: pd.DataFrame, table_name: str = "dataset") -> Dict[str, Any]:
        row_count = len(df)
        col_count = len(df.columns)
        
        # Calculate duplicate rows
        duplicate_rows_count = int(df.duplicated().sum()) if row_count > 0 else 0
        duplicate_pct = round((duplicate_rows_count / row_count * 100), 2) if row_count > 0 else 0.0

        columns_profile = []
        candidate_primary_keys = []
        candidate_measures = []
        candidate_dimensions = []
        candidate_dates = []

        total_cells = row_count * col_count if (row_count and col_count) else 1
        total_missing_cells = 0

        for col in df.columns:
            series = df[col]
            missing_count = int(series.isna().sum())
            total_missing_cells += missing_count
            missing_pct = round((missing_count / row_count * 100), 2) if row_count > 0 else 0.0
            
            # Non-null sample values for inspection
            non_null = series.dropna()
            distinct_count = int(non_null.nunique())
            sample_values = [cls._serialize_sample(v) for v in non_null.head(5).tolist()]

            # Detect semantic type
            semantic_type, standard_dtype = cls._infer_column_type(non_null, series.dtype, col)

            # Classify analytical role
            role = cls._classify_role(col, semantic_type, distinct_count, row_count)
            if role == "measure":
                candidate_measures.append(col)
            elif role == "dimension":
                candidate_dimensions.append(col)
            elif role == "date":
                candidate_dates.append(col)

            # Check primary key feasibility
            is_pk_candidate = False
            if distinct_count == row_count and missing_count == 0 and row_count > 0:
                is_pk_candidate = True
                candidate_primary_keys.append(col)

            # Basic descriptive stats
            stats = {}
            if semantic_type in ["numeric", "currency", "percentage"] and len(non_null) > 0:
                try:
                    num_series = pd.to_numeric(
                        non_null.astype(str).str.replace(r"[\$,\€\£\¥\₹% ]", "", regex=True),
                        errors="coerce"
                    ).dropna()
                    if len(num_series) > 0:
                        stats = {
                            "min": round(float(num_series.min()), 2),
                            "max": round(float(num_series.max()), 2),
                            "mean": round(float(num_series.mean()), 2),
                            "median": round(float(num_series.median()), 2),
                            "std": round(float(num_series.std()), 2) if len(num_series) > 1 else 0.0
                        }
                except Exception:
                    pass

            columns_profile.append({
                "name": str(col),
                "inferred_type": semantic_type,
                "raw_dtype": str(series.dtype),
                "role": role,
                "missing_count": missing_count,
                "missing_percentage": missing_pct,
                "distinct_count": distinct_count,
                "is_primary_key_candidate": is_pk_candidate,
                "sample_values": sample_values,
                "stats": stats
            })

        # Calculate Data Quality Score (0-100)
        completeness_score = max(0.0, 100.0 - (total_missing_cells / total_cells * 100.0))
        uniqueness_score = max(0.0, 100.0 - duplicate_pct)
        # Type consistency penalty (placeholder, minimal invalid values)
        consistency_score = 98.0
        overall_quality_score = round(
            (completeness_score * 0.45) + (uniqueness_score * 0.35) + (consistency_score * 0.20),
            1
        )

        quality_summary = {
            "overall_score": overall_quality_score,
            "completeness_score": round(completeness_score, 1),
            "uniqueness_score": round(uniqueness_score, 1),
            "consistency_score": round(consistency_score, 1),
            "total_rows": row_count,
            "total_columns": col_count,
            "duplicate_rows": duplicate_rows_count,
            "duplicate_percentage": duplicate_pct,
            "total_missing_cells": total_missing_cells,
            "missing_cells_percentage": round((total_missing_cells / total_cells * 100), 2)
        }

        # Generate intelligent recommendations
        recommendations = cls._generate_recommendations(
            candidate_measures, candidate_dimensions, candidate_dates, row_count, duplicate_rows_count
        )

        return {
            "table_name": table_name,
            "row_count": row_count,
            "column_count": col_count,
            "columns": columns_profile,
            "candidate_primary_keys": candidate_primary_keys,
            "candidate_measures": candidate_measures,
            "candidate_dimensions": candidate_dimensions,
            "candidate_dates": candidate_dates,
            "quality_summary": quality_summary,
            "recommendations": recommendations
        }

    @classmethod
    def _infer_column_type(cls, non_null_series: pd.Series, raw_dtype, col_name: str) -> Tuple[str, str]:
        col_lower = str(col_name).lower()
        
        # Check boolean
        if pd.api.types.is_bool_dtype(raw_dtype):
            return "boolean", "boolean"
        
        # Check datetime
        if pd.api.types.is_datetime64_any_dtype(raw_dtype):
            return "datetime", "datetime"

        if len(non_null_series) == 0:
            return "string", "string"

        # Check if numeric
        if pd.api.types.is_numeric_dtype(raw_dtype):
            # Check if likely an ID
            if "id" in col_lower.split("_") or col_lower.endswith("id") or "code" in col_lower:
                return "identifier", "numeric"
            # Check if percentage
            if "pct" in col_lower or "percent" in col_lower or "margin" in col_lower:
                return "percentage", "numeric"
            return "numeric", "numeric"

        # String samples check
        samples = [str(x).strip() for x in non_null_series.head(30)]
        
        # Check currency
        if any(cls.CURRENCY_REGEX.match(s) for s in samples) or any(k in col_lower for k in ["sales", "revenue", "profit", "price", "cost", "salary", "amount"]):
            # Check if mostly numbers when stripped
            try:
                cleaned = [s.replace("$", "").replace("€", "").replace("£", "").replace("₹", "").replace(",", "") for s in samples]
                pd.to_numeric(cleaned)
                return "currency", "numeric"
            except Exception:
                pass

        # Check percentage
        if any(cls.PERCENT_REGEX.match(s) for s in samples):
            return "percentage", "numeric"

        # Check date string
        if any(k in col_lower for k in ["date", "time", "day", "month", "year", "created", "timestamp", "dob"]):
            try:
                pd.to_datetime(samples, errors="raise")
                return "date", "datetime"
            except Exception:
                pass

        if any(cls.DATE_REGEX.match(s) for s in samples[:5]):
            try:
                pd.to_datetime(samples, errors="raise")
                return "date", "datetime"
            except Exception:
                pass

        # Check boolean strings
        bool_set = {"true", "false", "0", "1", "yes", "no", "y", "n"}
        if all(s.lower() in bool_set for s in samples):
            return "boolean", "boolean"

        # Check identifier
        if "id" in col_lower.split("_") or col_lower.endswith("id") or col_lower == "id" or "code" in col_lower or "sku" in col_lower:
            return "identifier", "string"

        return "categorical" if non_null_series.nunique() < 50 else "string", "string"

    @classmethod
    def _classify_role(cls, col_name: str, semantic_type: str, distinct_count: int, total_rows: int) -> str:
        col_lower = str(col_name).lower()
        if semantic_type in ["date", "datetime"]:
            return "date"
        if semantic_type == "identifier":
            return "identifier"
        if semantic_type in ["numeric", "currency", "percentage"]:
            # If high cardinality integer with "id" in name
            if ("id" in col_lower or "code" in col_lower) and distinct_count > (total_rows * 0.8):
                return "identifier"
            return "measure"
        if semantic_type in ["categorical", "boolean", "string"]:
            return "dimension"
        return "dimension"

    @classmethod
    def _generate_recommendations(
        cls, measures: List[str], dimensions: List[str], dates: List[str], row_count: int, duplicate_rows: int
    ) -> List[Dict[str, Any]]:
        recs = []

        if duplicate_rows > 0:
            recs.append({
                "type": "cleaning",
                "title": f"Deduplicate {duplicate_rows} redundant rows",
                "description": f"Dataset contains {duplicate_rows} exact duplicate rows. Consider cleaning before running statistical aggregations.",
                "action": "remove_duplicates"
            })

        if measures and dates:
            primary_measure = measures[0]
            primary_date = dates[0]
            recs.append({
                "type": "trend",
                "title": f"Time-Series Trend: {primary_measure} over {primary_date}",
                "description": f"Plot monthly and seasonal movement of {primary_measure} over {primary_date}.",
                "chart_type": "line",
                "x_axis": primary_date,
                "y_axis": primary_measure
            })

        if measures and dimensions:
            dim = dimensions[0]
            meas = measures[0]
            recs.append({
                "type": "ranking",
                "title": f"Top Performing {dim} by {meas}",
                "description": f"Identify the highest and lowest contribution across {dim}.",
                "chart_type": "bar",
                "x_axis": dim,
                "y_axis": meas
            })

        if len(measures) >= 2:
            m1, m2 = measures[0], measures[1]
            recs.append({
                "type": "correlation",
                "title": f"Correlation Analysis: {m1} vs {m2}",
                "description": f"Examine linear relationship and scatter distribution between {m1} and {m2}.",
                "chart_type": "scatter",
                "x_axis": m1,
                "y_axis": m2
            })

        if dates and measures:
            recs.append({
                "type": "forecasting",
                "title": f"6-Month Forecast for {measures[0]}",
                "description": "Generate projected trend lines and 95% confidence intervals based on historical patterns.",
                "chart_type": "forecast",
                "target_column": measures[0],
                "date_column": dates[0]
            })

        return recs

    @classmethod
    def _serialize_sample(cls, val):
        if val is None or pd.isna(val):
            return None
        if isinstance(val, (datetime.date, datetime.datetime)):
            return val.isoformat()
        if isinstance(val, (np.integer, int)):
            return int(val)
        if isinstance(val, (np.floating, float)):
            return round(float(val), 2)
        return str(val)
