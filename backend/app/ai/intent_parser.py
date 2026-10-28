import re
from typing import Dict, Any, List, Optional, Tuple

class IntentParser:
    """
    Intelligent NLP Intent Parser supporting Natural English and Tanglish (Tamil-English):
    - "Total sales evlo?" -> Intent: AGGREGATE, Measure: Sales, Agg: SUM
    - "Month-wise sales trend kaatu." -> Intent: TIME_SERIES, Dimension: Date, Measure: Sales
    - "Top 10 products eduthu kudu." -> Intent: TOP_N, Limit: 10, Dimension: Product, Measure: Sales/Profit
    - "Profit yen decrease aachu?" -> Intent: ROOT_CAUSE, Target: Profit
    - "Automatic dashboard create pannu." -> Intent: CREATE_DASHBOARD
    - "Duplicate rows remove pannu." -> Intent: CLEAN_DUPLICATES
    - "Excel formula illama profit calculate pannu." -> Intent: CALCULATE_METRIC, Target: Profit
    - "Now show only Chennai" -> Intent: FOLLOWUP_FILTER, Filter: City = Chennai
    """

    # Keyword mappings for Tanglish & English
    TANGLISH_TOTAL = ["evlo", "yevlo", "ethana", "total", "sum", "kootu", "motham", "overall"]
    TANGLISH_TREND = ["kaatu", "kaattu", "trend", "month-wise", "monthly", "over time", "pathu kudu", "varusham"]
    TANGLISH_TOP = ["eduthu kudu", "top", "perusu", "highest", "first", "best", "munnadi"]
    TANGLISH_WHY = ["yen", "yean", "ethanaala", "why", "decrease aachu", "reason", "declining", "drop"]
    TANGLISH_DASHBOARD = ["dashboard", "create pannu", "undakku", "seithu kudu", "kattu"]
    TANGLISH_CLEAN = ["remove pannu", "clean pannu", "thooku", "delete", "remove", "clean", "duplicate"]
    TANGLISH_FORMULA = ["formula illama", "without formula", "calculate pannu", "kandu pidi"]

    @classmethod
    def parse_intent(
        cls,
        query: str,
        available_columns: List[Dict[str, Any]],
        conversation_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        q_raw = query.strip()
        q = q_raw.lower()

        # Map column candidates
        col_names = [c["name"] for c in available_columns]
        measures = [c["name"] for c in available_columns if c.get("role") == "measure"]
        dimensions = [c["name"] for c in available_columns if c.get("role") == "dimension"]
        dates = [c["name"] for c in available_columns if c.get("role") == "date"]

        # Check for conversational follow-up (e.g. "Now show only Chennai", "Filter by Technology")
        if conversation_context and cls._is_follow_up(q):
            return cls._handle_follow_up(q, conversation_context, available_columns)

        # 1. Clean Duplicates Intent
        if any(w in q for w in ["duplicate", "duplicate rows", "duplicates"]) and any(w in q for w in ["remove", "find", "clean", "remove pannu", "thooku", "detect"]):
            return {
                "intent": "CLEAN_DUPLICATES",
                "original_query": q_raw,
                "action": "preview_duplicates",
                "explanation": "Identify and preview redundant duplicate rows in the dataset for removal confirmation."
            }

        # 2. Missing Values Intent
        if any(w in q for w in ["missing", "null", "empty cells", "nan"]) and any(w in q for w in ["detect", "find", "show", "count", "view"]):
            return {
                "intent": "DETECT_MISSING",
                "original_query": q_raw,
                "action": "detect_missing",
                "explanation": "Scan columns for missing and null values."
            }

        # 3. Create Dashboard Intent
        if "dashboard" in q or any(w in q for w in ["executive view", "summary view", "overview"]):
            return {
                "intent": "CREATE_DASHBOARD",
                "original_query": q_raw,
                "dashboard_type": "sales" if "sales" in q else "executive",
                "explanation": "Generate a dynamic multi-chart analytical dashboard driven by the dataset schema."
            }

        # 4. Profit Margin / Formula Intent (Without Excel formulas)
        if "profit margin" in q or ("margin" in q and "profit" in q) or "formula illama profit" in q:
            profit_col = cls._find_matching_col(col_names, ["profit", "net_profit"])
            sales_col = cls._find_matching_col(col_names, ["sales", "revenue", "turnover"])
            return {
                "intent": "PROFIT_MARGIN",
                "original_query": q_raw,
                "profit_column": profit_col,
                "sales_column": sales_col,
                "explanation": "Compute profit margin percentage directly without requiring Excel formulas."
            }

        # 5. Root Cause / Declining Revenue / Why did profit drop
        if any(w in q for w in cls.TANGLISH_WHY) or "declining" in q or "loss" in q:
            target_metric = cls._find_matching_col(measures, ["profit", "sales", "revenue"]) or (measures[0] if measures else None)
            dim_candidate = dimensions[0] if dimensions else None
            return {
                "intent": "ROOT_CAUSE",
                "original_query": q_raw,
                "target_metric": target_metric,
                "dimension": dim_candidate,
                "explanation": f"Investigate underlying segment drivers and variance explaining changes in {target_metric}."
            }

        # 6. Forecasting Intent
        if any(w in q for w in ["forecast", "predict", "next six months", "future", "projection"]):
            target_meas = cls._find_matching_col(measures, ["sales", "revenue", "profit"]) or (measures[0] if measures else None)
            date_col = dates[0] if dates else None
            periods = 6
            if "3 months" in q or "quarter" in q: periods = 3
            elif "12 months" in q or "year" in q: periods = 12
            return {
                "intent": "FORECAST",
                "original_query": q_raw,
                "target_metric": target_meas,
                "date_column": date_col,
                "forecast_periods": periods,
                "explanation": f"Generate a {periods}-month predictive forecast with confidence intervals for {target_meas}."
            }

        # 7. Relationship / Correlation / Scatter Intent
        if any(w in q for w in ["relationship", "correlation", "scatter", "vs", "versus"]):
            m1 = cls._find_matching_col(measures, ["discount", "price", "quantity", "cost"]) or (measures[0] if measures else None)
            m2 = cls._find_matching_col(measures, ["profit", "sales", "revenue"]) or (measures[1] if len(measures) > 1 else m1)
            return {
                "intent": "CORRELATION",
                "original_query": q_raw,
                "measure_x": m1,
                "measure_y": m2,
                "explanation": f"Analyze relationship and correlation coefficient between {m1} and {m2}."
            }

        # 8. Anomaly / Unusual Transactions
        if any(w in q for w in ["unusual", "anomaly", "anomalies", "outlier", "outliers"]):
            target_meas = cls._find_matching_col(measures, ["sales", "profit", "amount", "salary"]) or (measures[0] if measures else None)
            return {
                "intent": "ANOMALY_DETECTION",
                "original_query": q_raw,
                "target_metric": target_meas,
                "explanation": f"Detect statistical anomalies and unusual transactions in {target_meas} using IQR and Z-scores."
            }

        # 9. Top N / Bottom N Ranking Intent
        if any(w in q for w in cls.TANGLISH_TOP) or "bottom" in q or "top" in q or "best" in q or "worst" in q:
            limit = 10
            match_num = re.search(r"\b(top|bottom)\s*(\d+)\b", q)
            if match_num:
                limit = int(match_num.group(2))
            
            is_asc = "bottom" in q or "worst" in q or "loss-making" in q or "lowest" in q
            
            # Find dimension (e.g. products, region, customer)
            target_dim = cls._find_matching_col(dimensions, ["sub_category", "category", "product", "region", "city", "customer_segment", "department"]) or (dimensions[0] if dimensions else "Category")
            target_meas = cls._find_matching_col(measures, ["profit", "sales", "revenue", "salary"]) or (measures[0] if measures else "Sales")
            
            return {
                "intent": "TOP_N",
                "original_query": q_raw,
                "dimension": target_dim,
                "measure": target_meas,
                "limit": limit,
                "ascending": is_asc,
                "explanation": f"Retrieve {'bottom' if is_asc else 'top'} {limit} {target_dim} ranked by {target_meas}."
            }

        # 10. Time Series / Month-wise Trend
        if any(w in q for w in cls.TANGLISH_TREND) or "month" in q or "monthly" in q or "trend" in q or "over time" in q:
            date_col = dates[0] if dates else cls._find_matching_col(col_names, ["date", "order_date", "month", "created_at"])
            target_meas = cls._find_matching_col(measures, ["sales", "revenue", "profit"]) or (measures[0] if measures else None)
            return {
                "intent": "TIME_SERIES",
                "original_query": q_raw,
                "date_column": date_col,
                "measure": target_meas,
                "aggregation": "SUM",
                "explanation": f"Compute monthly trend analysis for {target_meas} over time."
            }

        # 11. Multi-metric Aggregation (e.g. "Show total sales and average profit", "total sales evlo")
        meas_list = []
        for m in measures:
            if m.lower() in q:
                meas_list.append(m)
        if not meas_list:
            # Check keywords like sales, profit
            for kw in ["sales", "profit", "revenue", "quantity", "discount", "salary"]:
                match_col = cls._find_matching_col(measures, [kw])
                if match_col and match_col not in meas_list:
                    meas_list.append(match_col)

        if not meas_list and measures:
            meas_list = [measures[0]]

        # Check if dimension grouping requested (e.g. "by region", "across categories")
        group_dim = None
        for d in dimensions:
            if d.lower() in q or f"by {d.lower()}" in q or f"across {d.lower()}" in q:
                group_dim = d
                break

        return {
            "intent": "AGGREGATION",
            "original_query": q_raw,
            "measures": meas_list,
            "dimension": group_dim,
            "explanation": f"Compute statistical aggregations for {', '.join(meas_list)}" + (f" grouped by {group_dim}" if group_dim else "") + "."
        }

    @classmethod
    def _is_follow_up(cls, q: str) -> bool:
        follow_up_starters = ["now show", "now filter", "only", "filter by", "what about", "and for", "now break down", "compare with"]
        return any(q.startswith(s) or f" {s} " in f" {q} " for s in follow_up_starters)

    @classmethod
    def _handle_follow_up(
        cls,
        q: str,
        context: Dict[str, Any],
        available_columns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        dimensions = [c["name"] for c in available_columns if c.get("role") == "dimension"]
        
        # Check for filter value in query (e.g. "Now show only Chennai", "only Technology")
        filter_col = None
        filter_val = None

        clean_q = re.sub(r"^(now show|now filter|only|filter by|show only)\s+", "", q).strip()
        
        # Check if clean_q matches any column sample or dimension
        for c in available_columns:
            for s in c.get("sample_values", []):
                if s and str(s).lower() in clean_q:
                    filter_col = c["name"]
                    filter_val = str(s)
                    break
            if filter_col:
                break

        # Fallback keyword match
        if not filter_col:
            for dim in dimensions:
                if dim.lower() in clean_q:
                    filter_col = dim
                    filter_val = clean_q.replace(dim.lower(), "").strip()

        prev_intent = context.get("last_intent") or "AGGREGATION"
        prev_measures = context.get("last_measures") or ["Sales"]
        prev_dimension = context.get("last_dimension") or "Category"

        return {
            "intent": "FOLLOWUP_FILTER",
            "original_query": q,
            "filter_column": filter_col or "City",
            "filter_value": filter_val or clean_q,
            "base_intent": prev_intent,
            "measures": prev_measures,
            "dimension": prev_dimension,
            "explanation": f"Applying contextual filter: {filter_col or 'Filter'} = '{filter_val or clean_q}' on previous analysis."
        }

    @classmethod
    def _find_matching_col(cls, columns: List[str], candidates: List[str]) -> Optional[str]:
        cols_lower = {c.lower(): c for c in columns}
        for cand in candidates:
            cand_l = cand.lower()
            for c_low, c_orig in cols_lower.items():
                if cand_l == c_low or cand_l in c_low or c_low in cand_l:
                    return c_orig
        return None
