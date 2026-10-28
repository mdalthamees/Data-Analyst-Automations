from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from app.core.dataset_manager import dataset_manager
from app.core.duckdb_engine import duckdb_engine

class StatisticalAnalysis:
    """
    Statistical and Business Intelligence Engine:
    Descriptive stats, Pearson correlation matrix, Pareto 80/20 distribution,
    segment driver analysis, and statistical anomaly detection.
    """

    @classmethod
    def get_descriptive_stats(cls, dataset_id: str) -> Dict[str, Any]:
        meta = dataset_manager.get_dataset(dataset_id)
        if not meta:
            raise KeyError(f"Dataset {dataset_id} not found.")

        df = dataset_manager.get_dataset_dataframe(dataset_id)
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        stats_list = []
        for col in num_cols:
            s = df[col].dropna()
            if len(s) == 0:
                continue
            
            mean_val = float(s.mean())
            std_val = float(s.std()) if len(s) > 1 else 0.0
            skew_val = float(s.skew()) if len(s) > 2 else 0.0

            stats_list.append({
                "column": col,
                "count": int(s.count()),
                "mean": round(mean_val, 2),
                "std": round(std_val, 2),
                "min": round(float(s.min()), 2),
                "q25": round(float(s.quantile(0.25)), 2),
                "median": round(float(s.median()), 2),
                "q75": round(float(s.quantile(0.75)), 2),
                "max": round(float(s.max()), 2),
                "skewness": round(skew_val, 2),
                "distribution_shape": "Normal" if abs(skew_val) < 0.5 else "Right Skewed" if skew_val > 0.5 else "Left Skewed"
            })

        return {
            "dataset_id": dataset_id,
            "numeric_columns_count": len(num_cols),
            "statistics": stats_list
        }

    @classmethod
    def get_correlation_matrix(cls, dataset_id: str) -> Dict[str, Any]:
        df = dataset_manager.get_dataset_dataframe(dataset_id)
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Limit to top 8 numeric cols to avoid clutter
        cols = num_cols[:8]
        if len(cols) < 2:
            return {"columns": cols, "matrix": []}

        corr = df[cols].corr().round(3)
        matrix = []
        for col1 in cols:
            row = {"variable": col1}
            for col2 in cols:
                row[col2] = float(corr.loc[col1, col2]) if not pd.isna(corr.loc[col1, col2]) else 0.0
            matrix.append(row)

        return {
            "columns": cols,
            "matrix": matrix
        }

    @classmethod
    def get_pareto_analysis(cls, dataset_id: str, dimension: str, measure: str) -> Dict[str, Any]:
        """
        Computes Pareto 80/20 distribution:
        Sorts categories descending by measure, calculates running total and cumulative percentage.
        """
        meta = dataset_manager.get_dataset(dataset_id)
        if not meta:
            raise KeyError(f"Dataset {dataset_id} not found.")

        table_name = meta["table_name"]
        sql = f"""
        WITH ranked AS (
            SELECT 
                "{dimension}" AS category,
                ROUND(SUM("{measure}"), 2) AS total_val
            FROM {table_name}
            WHERE "{dimension}" IS NOT NULL AND "{measure}" IS NOT NULL
            GROUP BY "{dimension}"
        ),
        cumulative AS (
            SELECT 
                category,
                total_val,
                SUM(total_val) OVER (ORDER BY total_val DESC) AS running_total,
                SUM(total_val) OVER () AS grand_total
            FROM ranked
        )
        SELECT 
            category,
            total_val,
            running_total,
            ROUND((running_total / NULLIF(grand_total, 0)) * 100, 2) AS cumulative_pct
        FROM cumulative
        ORDER BY total_val DESC
        LIMIT 25;
        """
        res = duckdb_engine.execute_query(sql)
        items = []
        vital_few_count = 0

        for r in res["rows"]:
            pct = float(r[3]) if r[3] is not None else 0.0
            if pct <= 80.0:
                vital_few_count += 1
            items.append({
                "category": str(r[0]),
                "value": float(r[1]),
                "running_total": float(r[2]),
                "cumulative_pct": pct
            })

        return {
            "dimension": dimension,
            "measure": measure,
            "items": items,
            "vital_few_count": max(1, vital_few_count),
            "summary": f"Top {max(1, vital_few_count)} {dimension} categories contribute approximately 80% of total {measure}."
        }

    @classmethod
    def get_anomalies(cls, dataset_id: str, measure: str, threshold: float = 3.0) -> Dict[str, Any]:
        """
        Z-Score anomaly detection on specific measure.
        """
        meta = dataset_manager.get_dataset(dataset_id)
        table_name = meta["table_name"]
        
        sql = f"""
        WITH stats AS (
            SELECT AVG("{measure}") AS mean_val, STDDEV_SAMP("{measure}") AS std_val FROM {table_name}
        )
        SELECT 
            *,
            ROUND(ABS(("{measure}" - stats.mean_val) / NULLIF(stats.std_val, 0)), 2) AS z_score
        FROM {table_name}, stats
        WHERE ABS(("{measure}" - stats.mean_val) / NULLIF(stats.std_val, 0)) > {threshold}
        ORDER BY z_score DESC
        LIMIT 50;
        """
        res = duckdb_engine.execute_query(sql)
        return {
            "measure": measure,
            "threshold": threshold,
            "anomaly_count": res["row_count"],
            "columns": res["columns"],
            "rows": res["rows"]
        }
