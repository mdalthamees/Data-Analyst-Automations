import re
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

class CleaningStudio:
    """
    Intelligent Data Cleaning Studio:
    Provides previews with before/after row diffs, affected counts, and reversible executions.
    """

    # --- Duplicates ---
    @classmethod
    def preview_remove_duplicates(cls, df: pd.DataFrame, subset_cols: Optional[List[str]] = None) -> Dict[str, Any]:
        before_count = len(df)
        cols = subset_cols if subset_cols and all(c in df.columns for c in subset_cols) else None
        
        dup_mask = df.duplicated(subset=cols, keep="first")
        dup_count = int(dup_mask.sum())
        after_count = before_count - dup_count
        
        sample_duplicates = []
        if dup_count > 0:
            sample_df = df[dup_mask].head(5)
            sample_duplicates = sample_df.to_dict(orient="records")

        return {
            "operation": "remove_duplicates",
            "before_rows": before_count,
            "after_rows": after_count,
            "affected_rows": dup_count,
            "percentage_affected": round((dup_count / before_count * 100), 2) if before_count > 0 else 0.0,
            "sample_duplicates": sample_duplicates,
            "requires_confirmation": True,
            "description": f"Found {dup_count} duplicate rows. Applying will preserve the first occurrence and remove {dup_count} records."
        }

    @classmethod
    def apply_remove_duplicates(cls, df: pd.DataFrame, subset_cols: Optional[List[str]] = None, keep: str = "first") -> Tuple[pd.DataFrame, Dict[str, Any]]:
        cols = subset_cols if subset_cols and all(c in df.columns for c in subset_cols) else None
        before = len(df)
        cleaned_df = df.drop_duplicates(subset=cols, keep=keep).reset_index(drop=True)
        after = len(cleaned_df)
        summary = {
            "action": "Removed duplicate records",
            "before_rows": before,
            "after_rows": after,
            "removed_rows": before - after
        }
        return cleaned_df, summary

    # --- Missing Values ---
    @classmethod
    def preview_impute_missing(
        cls, df: pd.DataFrame, column: str, strategy: str = "mean", fill_value: Any = None
    ) -> Dict[str, Any]:
        if column not in df.columns:
            raise KeyError(f"Column '{column}' not found.")
        
        series = df[column]
        missing_count = int(series.isna().sum())
        total_rows = len(df)

        calculated_fill = None
        if strategy == "mean":
            calculated_fill = round(float(pd.to_numeric(series, errors="coerce").mean()), 2)
        elif strategy == "median":
            calculated_fill = round(float(pd.to_numeric(series, errors="coerce").median()), 2)
        elif strategy == "mode":
            mode_series = series.mode()
            calculated_fill = mode_series[0] if len(mode_series) > 0 else "Unknown"
        elif strategy == "constant":
            calculated_fill = fill_value if fill_value is not None else 0
        elif strategy == "drop":
            calculated_fill = "Drop affected rows"

        return {
            "operation": "impute_missing",
            "column": column,
            "strategy": strategy,
            "missing_rows": missing_count,
            "total_rows": total_rows,
            "missing_percentage": round((missing_count / total_rows * 100), 2) if total_rows > 0 else 0.0,
            "replacement_value": calculated_fill,
            "description": f"Impute {missing_count} nulls in '{column}' using strategy '{strategy}' (value: {calculated_fill})."
        }

    @classmethod
    def apply_impute_missing(
        cls, df: pd.DataFrame, column: str, strategy: str = "mean", fill_value: Any = None
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        if column not in df.columns:
            raise KeyError(f"Column '{column}' not found.")
        
        df_clean = df.copy()
        series = df_clean[column]
        missing_count = int(series.isna().sum())

        if strategy == "drop":
            df_clean = df_clean.dropna(subset=[column]).reset_index(drop=True)
            return df_clean, {
                "action": f"Dropped {missing_count} rows with missing '{column}'",
                "affected_rows": missing_count
            }

        fill_val = fill_value
        if strategy == "mean":
            fill_val = pd.to_numeric(series, errors="coerce").mean()
        elif strategy == "median":
            fill_val = pd.to_numeric(series, errors="coerce").median()
        elif strategy == "mode":
            mode_s = series.mode()
            fill_val = mode_s[0] if len(mode_s) > 0 else ""
        elif strategy == "forward_fill":
            df_clean[column] = df_clean[column].ffill()
            return df_clean, {"action": f"Forward-filled {missing_count} values in '{column}'"}

        df_clean[column] = df_clean[column].fillna(fill_val)
        return df_clean, {
            "action": f"Imputed {missing_count} missing values in '{column}' with {fill_val}",
            "affected_rows": missing_count,
            "value": str(fill_val)
        }

    # --- Outlier Detection & Capping ---
    @classmethod
    def preview_detect_outliers(
        cls, df: pd.DataFrame, column: str, method: str = "iqr", threshold: float = 1.5
    ) -> Dict[str, Any]:
        if column not in df.columns:
            raise KeyError(f"Column '{column}' not found.")
        
        num_series = pd.to_numeric(df[column], errors="coerce").dropna()
        if len(num_series) < 4:
            return {"operation": "outliers", "outlier_count": 0, "description": "Insufficient numeric data for outlier analysis."}

        if method == "iqr":
            q25 = num_series.quantile(0.25)
            q75 = num_series.quantile(0.75)
            iqr = q75 - q25
            lower_bound = q25 - (threshold * iqr)
            upper_bound = q75 + (threshold * iqr)
        else: # z-score
            mean = num_series.mean()
            std = num_series.std()
            lower_bound = mean - (threshold * std)
            upper_bound = mean + (threshold * std)

        outlier_mask = (num_series < lower_bound) | (num_series > upper_bound)
        outlier_count = int(outlier_mask.sum())

        return {
            "operation": "detect_outliers",
            "column": column,
            "method": method,
            "threshold": threshold,
            "lower_bound": round(float(lower_bound), 2),
            "upper_bound": round(float(upper_bound), 2),
            "outlier_count": outlier_count,
            "outlier_percentage": round((outlier_count / len(num_series) * 100), 2),
            "sample_outliers": num_series[outlier_mask].head(5).tolist()
        }

    @classmethod
    def apply_handle_outliers(
        cls, df: pd.DataFrame, column: str, action: str = "cap", method: str = "iqr", threshold: float = 1.5
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        preview = cls.preview_detect_outliers(df, column, method, threshold)
        low = preview["lower_bound"]
        high = preview["upper_bound"]
        count = preview["outlier_count"]

        df_clean = df.copy()
        num_series = pd.to_numeric(df_clean[column], errors="coerce")

        if action == "cap":
            df_clean[column] = num_series.clip(lower=low, upper=high)
            desc = f"Capped {count} outliers in '{column}' between [{low}, {high}]."
        elif action == "drop":
            valid_mask = (num_series >= low) & (num_series <= high)
            df_clean = df_clean[valid_mask].reset_index(drop=True)
            desc = f"Removed {count} outlier rows outside [{low}, {high}] in '{column}'."
        else:
            # Flag with new column
            flag_col = f"{column}_is_outlier"
            df_clean[flag_col] = (num_series < low) | (num_series > high)
            desc = f"Flagged {count} outliers in new boolean column '{flag_col}'."

        return df_clean, {"action": desc, "affected_rows": count}

    # --- Date Standardization ---
    @classmethod
    def apply_standardize_dates(cls, df: pd.DataFrame, column: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        df_clean = df.copy()
        before = df_clean[column].copy()
        parsed = pd.to_datetime(df_clean[column], errors="coerce")
        converted_count = int(parsed.notna().sum())
        df_clean[column] = parsed.dt.strftime("%Y-%m-%d")
        
        return df_clean, {
            "action": f"Standardized dates in '{column}' to ISO YYYY-MM-DD",
            "converted_count": converted_count
        }

    # --- Text Normalization ---
    @classmethod
    def apply_normalize_text(cls, df: pd.DataFrame, column: str, operation: str = "trim") -> Tuple[pd.DataFrame, Dict[str, Any]]:
        df_clean = df.copy()
        s = df_clean[column].astype(str)
        
        if operation == "trim":
            df_clean[column] = s.str.strip().str.replace(r"\s+", " ", regex=True)
        elif operation == "uppercase":
            df_clean[column] = s.str.upper().str.strip()
        elif operation == "lowercase":
            df_clean[column] = s.str.lower().str.strip()
        elif operation == "titlecase":
            df_clean[column] = s.str.title().str.strip()

        return df_clean, {"action": f"Normalized text in '{column}' with '{operation}'"}

    # --- Column Operations ---
    @classmethod
    def apply_rename_column(cls, df: pd.DataFrame, old_name: str, new_name: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        if old_name not in df.columns:
            raise KeyError(f"Column '{old_name}' not found.")
        clean_new = new_name.strip()
        df_clean = df.rename(columns={old_name: clean_new})
        return df_clean, {"action": f"Renamed column '{old_name}' to '{clean_new}'"}

    @classmethod
    def apply_drop_columns(cls, df: pd.DataFrame, columns_to_drop: List[str]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        valid_cols = [c for c in columns_to_drop if c in df.columns]
        df_clean = df.drop(columns=valid_cols)
        return df_clean, {"action": f"Dropped columns: {', '.join(valid_cols)}", "dropped_columns": valid_cols}
