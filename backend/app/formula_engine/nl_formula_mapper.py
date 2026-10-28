import re
from typing import Dict, Any, List, Optional
import pandas as pd

class NLFormulaMapper:
    """
    Translates plain English & business questions into validated Excel formula expressions
    or vectorized execution recipes without requiring users to type Excel syntax.
    """

    @classmethod
    def map_natural_language_to_formula(cls, query: str, columns: List[str]) -> Dict[str, Any]:
        q_lower = query.lower()
        cols_lower = {c.lower(): c for c in columns}

        # Find best matching measure
        matched_measure = None
        for key in ["sales", "revenue", "profit", "salary", "expenses", "quantity", "cost", "price", "amount", "discount"]:
            if key in q_lower:
                for c_low, c_orig in cols_lower.items():
                    if key in c_low:
                        matched_measure = c_orig
                        break
            if matched_measure:
                break

        # Fallback to first numeric measure if not found
        if not matched_measure and columns:
            matched_measure = columns[0]

        # 1. Profit Margin Percentage
        if "profit margin" in q_lower or "margin" in q_lower:
            profit_col = cls._find_column(columns, ["profit", "net_profit"])
            sales_col = cls._find_column(columns, ["sales", "revenue", "turnover"])
            if profit_col and sales_col:
                return {
                    "matched": True,
                    "formula": f"=ROUND((SUM([{profit_col}]) / SUM([{sales_col}])) * 100, 2)",
                    "intent": "profit_margin",
                    "explanation": f"Calculates total {profit_col} divided by total {sales_col} formatted as a percentage."
                }
            else:
                return {
                    "matched": False,
                    "error": "Dataset must contain both a profit column and a sales/revenue column to calculate profit margin.",
                    "intent": "profit_margin"
                }

        # 2. Total / Sum
        if any(w in q_lower for w in ["total", "sum", "overall", "evlo"]):
            if matched_measure:
                return {
                    "matched": True,
                    "formula": f"=SUM([{matched_measure}])",
                    "intent": "total",
                    "explanation": f"Calculates the grand total sum of column [{matched_measure}]."
                }

        # 3. Average / Mean
        if any(w in q_lower for w in ["average", "avg", "mean"]):
            if matched_measure:
                return {
                    "matched": True,
                    "formula": f"=ROUND(AVERAGE([{matched_measure}]), 2)",
                    "intent": "average",
                    "explanation": f"Calculates arithmetic mean of column [{matched_measure}]."
                }

        # 4. Highest / Maximum
        if any(w in q_lower for w in ["highest", "max", "maximum", "peak", "perusu"]):
            if matched_measure:
                return {
                    "matched": True,
                    "formula": f"=MAX([{matched_measure}])",
                    "intent": "max",
                    "explanation": f"Finds the maximum single transaction value in [{matched_measure}]."
                }

        # 5. Lowest / Minimum
        if any(w in q_lower for w in ["lowest", "min", "minimum", "kammi"]):
            if matched_measure:
                return {
                    "matched": True,
                    "formula": f"=MIN([{matched_measure}])",
                    "intent": "min",
                    "explanation": f"Finds the minimum value in [{matched_measure}]."
                }

        # 6. Count unique
        if any(w in q_lower for w in ["count unique", "distinct", "unique count", "unique customers"]):
            id_col = cls._find_column(columns, ["customer_id", "customer", "order_id", "employee_id", "id"])
            if id_col:
                return {
                    "matched": True,
                    "formula": f"=COUNTA(UNIQUE([{id_col}]))",
                    "intent": "unique_count",
                    "explanation": f"Counts distinct occurrences in [{id_col}]."
                }

        return {
            "matched": False,
            "error": "Could not automatically determine the formula recipe from natural language query.",
            "intent": "unknown"
        }

    @classmethod
    def _find_column(cls, columns: List[str], candidates: List[str]) -> Optional[str]:
        cols_lower = {c.lower(): c for c in columns}
        for cand in candidates:
            for c_low, c_orig in cols_lower.items():
                if cand in c_low:
                    return c_orig
        return None
