import time
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from app.core.dataset_manager import dataset_manager
from app.core.duckdb_engine import duckdb_engine
from app.ai.intent_parser import IntentParser
from app.ai.llm_orchestrator import LLMOrchestrator

class ConversationalAnalyst:
    """
    Autonomous Data Analyst conversational engine:
    Translates English & Tanglish questions into real DuckDB computations,
    validates results, maintains multi-turn context, formats dynamic charts,
    and produces explainable, verifiable insights.
    """

    def __init__(self):
        # Conversation sessions: session_id -> context dict
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def ask(self, session_id: str, dataset_id: str, query: str) -> Dict[str, Any]:
        meta = dataset_manager.get_dataset(dataset_id)
        if not meta:
            raise KeyError(f"Dataset {dataset_id} not found.")

        table_name = meta["table_name"]
        columns_profile = meta["profile"]["columns"]
        col_names = [c["name"] for c in columns_profile]

        # Retrieve existing conversation session context
        session_ctx = self._sessions.get(session_id, {
            "history": [],
            "last_intent": None,
            "last_measures": None,
            "last_dimension": None,
            "active_filters": {}
        })

        # Parse intent
        intent_plan = IntentParser.parse_intent(query, columns_profile, conversation_context=session_ctx)
        intent = intent_plan.get("intent")

        result_payload = {}

        # 1. CLEAN_DUPLICATES
        if intent == "CLEAN_DUPLICATES":
            from app.cleaning.cleaning_studio import CleaningStudio
            df = dataset_manager.get_dataset_dataframe(dataset_id)
            preview = CleaningStudio.preview_remove_duplicates(df)
            result_payload = {
                "type": "cleaning_preview",
                "title": "Duplicate Records Analysis",
                "preview": preview,
                "summary": f"Detected {preview['affected_rows']} duplicate rows in the dataset.",
                "requires_action": True,
                "action_type": "confirm_deduplication",
                "kpi_cards": [
                    {"label": "Total Rows", "value": preview["before_rows"], "formatted_value": f"{preview['before_rows']:,}"},
                    {"label": "Duplicate Rows", "value": preview["affected_rows"], "formatted_value": f"{preview['affected_rows']:,}"},
                    {"label": "Clean Row Count", "value": preview["after_rows"], "formatted_value": f"{preview['after_rows']:,}"}
                ]
            }

        # 2. PROFIT_MARGIN (Without Excel formulas)
        elif intent == "PROFIT_MARGIN":
            p_col = intent_plan.get("profit_column") or "Profit"
            s_col = intent_plan.get("sales_column") or "Sales"

            if p_col in col_names and s_col in col_names:
                sql = f"SELECT SUM(\"{p_col}\") AS total_profit, SUM(\"{s_col}\") AS total_sales, ROUND((SUM(\"{p_col}\") / NULLIF(SUM(\"{s_col}\"), 0)) * 100, 2) AS profit_margin_pct FROM {table_name}"
                res = duckdb_engine.execute_query(sql)
                if res["success"] and res["rows"]:
                    row = res["rows"][0]
                    t_profit, t_sales, margin_pct = row[0], row[1], row[2]
                    result_payload = {
                        "type": "metric_card",
                        "title": "Profit Margin Calculation",
                        "summary": f"Computed Profit Margin is {margin_pct}% (Total Profit: ${t_profit:,.2f} on Total Sales: ${t_sales:,.2f}).",
                        "kpi_cards": [
                            {"label": "Profit Margin", "value": margin_pct, "formatted_value": f"{margin_pct}%", "highlight": True},
                            {"label": "Total Profit", "value": t_profit, "formatted_value": f"${t_profit:,.2f}"},
                            {"label": "Total Sales", "value": t_sales, "formatted_value": f"${t_sales:,.2f}"}
                        ],
                        "verification_trace": {
                            "formula": f"(SUM([{p_col}]) / SUM([{s_col}])) * 100",
                            "sql": sql,
                            "execution_engine": "DuckDB",
                            "execution_time_ms": res["execution_time_ms"]
                        }
                    }
            else:
                result_payload = {
                    "type": "error",
                    "error": f"Required fields for profit margin (Sales, Profit) could not be identified automatically in columns: {', '.join(col_names[:6])}."
                }

        # 3. TOP_N / BOTTOM_N RANKING
        elif intent == "TOP_N":
            dim = intent_plan["dimension"]
            meas = intent_plan["measure"]
            limit = intent_plan["limit"]
            asc = intent_plan.get("ascending", False)
            direction = "ASC" if asc else "DESC"

            if dim in col_names and meas in col_names:
                sql = f"SELECT \"{dim}\" AS dimension, ROUND(SUM(\"{meas}\"), 2) AS metric FROM {table_name} GROUP BY \"{dim}\" ORDER BY metric {direction} LIMIT {limit}"
                res = duckdb_engine.execute_query(sql)
                chart_data = [{"name": str(r[0]), "value": float(r[1]) if r[1] is not None else 0.0} for r in res["rows"]]
                
                result_payload = {
                    "type": "chart",
                    "chart_type": "bar",
                    "title": f"Top {limit} {dim} by {meas}",
                    "summary": f"Showing top {len(chart_data)} {dim} ranked by total {meas}.",
                    "chart_data": chart_data,
                    "kpi_cards": [
                        {"label": f"Top {dim}", "value": chart_data[0]["name"] if chart_data else "N/A", "formatted_value": str(chart_data[0]["name"]) if chart_data else "N/A"},
                        {"label": f"Peak {meas}", "value": chart_data[0]["value"] if chart_data else 0, "formatted_value": f"${chart_data[0]['value']:,.2f}" if chart_data else "$0"}
                    ],
                    "verification_trace": {
                        "sql": sql,
                        "execution_engine": "DuckDB",
                        "rows_processed": meta["row_count"],
                        "execution_time_ms": res["execution_time_ms"]
                    }
                }
                session_ctx["last_dimension"] = dim
                session_ctx["last_measures"] = [meas]

        # 4. TIME_SERIES / MONTHLY TREND
        elif intent == "TIME_SERIES":
            date_col = intent_plan.get("date_column")
            meas = intent_plan.get("measure") or "Sales"

            if date_col in col_names and meas in col_names:
                sql = f"SELECT STRFTIME(CAST(\"{date_col}\" AS DATE), '%Y-%m') AS period, ROUND(SUM(\"{meas}\"), 2) AS total_val FROM {table_name} WHERE \"{date_col}\" IS NOT NULL GROUP BY period ORDER BY period ASC LIMIT 36"
                res = duckdb_engine.execute_query(sql)
                chart_data = [{"period": str(r[0]), "value": float(r[1]) if r[1] is not None else 0.0} for r in res["rows"]]

                result_payload = {
                    "type": "chart",
                    "chart_type": "area",
                    "title": f"Monthly {meas} Trend",
                    "summary": f"Calculated monthly trajectory for {meas} over {len(chart_data)} time periods.",
                    "chart_data": chart_data,
                    "kpi_cards": [
                        {"label": f"Total {meas}", "value": sum(c['value'] for c in chart_data), "formatted_value": f"${sum(c['value'] for c in chart_data):,.2f}"},
                        {"label": "Periods Tracked", "value": len(chart_data), "formatted_value": str(len(chart_data))}
                    ],
                    "verification_trace": {
                        "sql": sql,
                        "execution_engine": "DuckDB",
                        "execution_time_ms": res["execution_time_ms"]
                    }
                }
                session_ctx["last_measures"] = [meas]

        # 5. CORRELATION / RELATIONSHIP
        elif intent == "CORRELATION":
            m1 = intent_plan.get("measure_x")
            m2 = intent_plan.get("measure_y")
            if m1 in col_names and m2 in col_names:
                sql = f"SELECT ROUND(CORR(\"{m1}\", \"{m2}\"), 4) AS correlation_coeff FROM {table_name}"
                res = duckdb_engine.execute_query(sql)
                corr_val = res["rows"][0][0] if res["rows"] else 0.0
                
                # Fetch sample points for scatter plot
                scatter_sql = f"SELECT \"{m1}\" AS x, \"{m2}\" AS y FROM {table_name} WHERE \"{m1}\" IS NOT NULL AND \"{m2}\" IS NOT NULL LIMIT 150"
                scatter_res = duckdb_engine.execute_query(scatter_sql)
                points = [{"x": float(r[0]), "y": float(r[1])} for r in scatter_res["rows"]]

                strength = "strong positive" if corr_val > 0.7 else "moderate positive" if corr_val > 0.3 else "weak/none" if abs(corr_val) <= 0.3 else "moderate negative" if corr_val < -0.3 else "strong negative"

                result_payload = {
                    "type": "chart",
                    "chart_type": "scatter",
                    "title": f"Relationship: {m1} vs {m2}",
                    "summary": f"Correlation coefficient is {corr_val} ({strength} relationship). Note: Correlation does not imply direct causation.",
                    "chart_data": points,
                    "kpi_cards": [
                        {"label": "Pearson Correlation", "value": corr_val, "formatted_value": str(corr_val), "highlight": True},
                        {"label": "Sample Points", "value": len(points), "formatted_value": str(len(points))}
                    ],
                    "verification_trace": {
                        "sql": sql,
                        "correlation": corr_val,
                        "execution_engine": "DuckDB"
                    }
                }

        # 6. ROOT CAUSE / VARIANCE ANALYSIS
        elif intent == "ROOT_CAUSE":
            target = intent_plan.get("target_metric") or "Profit"
            dim = intent_plan.get("dimension") or "Category"
            
            # Segment breakdown to find loss-making or declining segments
            sql = f"SELECT \"{dim}\" AS segment, ROUND(SUM(\"{target}\"), 2) AS total_val, COUNT(*) AS count FROM {table_name} GROUP BY \"{dim}\" ORDER BY total_val ASC"
            res = duckdb_engine.execute_query(sql)
            segments = [{"name": str(r[0]), "value": float(r[1]), "count": int(r[2])} for r in res["rows"]]
            
            underperforming = [s for s in segments if s["value"] < 0]
            desc = f"Identified {len(underperforming)} loss-making {dim} segments dragging down overall {target}." if underperforming else f"All {dim} segments have positive net {target}. Lowest contributor is {segments[0]['name']}."

            result_payload = {
                "type": "chart",
                "chart_type": "bar",
                "title": f"Root Cause & Variance: {target} by {dim}",
                "summary": desc,
                "chart_data": segments,
                "kpi_cards": [
                    {"label": f"Lowest {dim}", "value": segments[0]["name"], "formatted_value": str(segments[0]["name"])},
                    {"label": f"Segment {target}", "value": segments[0]["value"], "formatted_value": f"${segments[0]['value']:,.2f}"}
                ],
                "verification_trace": {
                    "sql": sql,
                    "execution_engine": "DuckDB"
                }
            }

        # 7. CREATE_DASHBOARD
        elif intent == "CREATE_DASHBOARD":
            from app.analytics.dashboard_generator import DashboardGenerator
            dash = DashboardGenerator.generate_dashboard(dataset_id, title="Auto-Generated Executive Dashboard")
            result_payload = {
                "type": "dashboard",
                "title": dash["title"],
                "dashboard": dash,
                "summary": f"Generated interactive dashboard with {len(dash['kpis'])} KPI cards and {len(dash['charts'])} dynamic charts.",
                "kpi_cards": dash["kpis"]
            }

        # 8. FOLLOWUP_FILTER (e.g. "Now show only Chennai")
        elif intent == "FOLLOWUP_FILTER":
            filter_col = intent_plan["filter_column"]
            filter_val = intent_plan["filter_value"]
            measures_list = intent_plan.get("measures") or ["Sales"]
            prev_meas = measures_list[0] if measures_list else "Sales"
            
            clean_val = filter_val.replace("'", "''")
            sql = f"SELECT ROUND(SUM(\"{prev_meas}\"), 2) AS total_val, COUNT(*) AS row_cnt FROM {table_name} WHERE CAST(\"{filter_col}\" AS VARCHAR) ILIKE '%{clean_val}%'"
            res = duckdb_engine.execute_query(sql)
            
            t_val = res["rows"][0][0] if res["rows"] and res["rows"][0][0] is not None else 0.0
            r_cnt = res["rows"][0][1] if res["rows"] else 0

            result_payload = {
                "type": "metric_card",
                "title": f"Filtered Analysis ({filter_col} = {filter_val})",
                "summary": f"Filtered to '{filter_val}' ({r_cnt:,} records). Total {prev_meas} is ${t_val:,.2f}.",
                "kpi_cards": [
                    {"label": f"Filtered {prev_meas}", "value": t_val, "formatted_value": f"${t_val:,.2f}", "highlight": True},
                    {"label": "Filtered Records", "value": r_cnt, "formatted_value": f"{r_cnt:,}"}
                ],
                "verification_trace": {
                    "sql": sql,
                    "filter": f"{filter_col} ILIKE '%{filter_val}%'",
                    "execution_engine": "DuckDB"
                }
            }

        # 9. GENERAL AGGREGATION FALLBACK (e.g. "Show total sales and average profit", "total sales evlo")
        else:
            meas_list = intent_plan.get("measures", ["Sales"])
            dim = intent_plan.get("dimension")
            session_ctx["last_measures"] = meas_list
            session_ctx["last_dimension"] = dim

            agg_selects = []
            kpis = []
            for m in meas_list:
                agg_selects.append(f"ROUND(SUM(\"{m}\"), 2) AS sum_{m}")
                agg_selects.append(f"ROUND(AVG(\"{m}\"), 2) AS avg_{m}")

            if dim and dim in col_names:
                sql = f"SELECT \"{dim}\" AS dimension, {', '.join(agg_selects)} FROM {table_name} GROUP BY \"{dim}\" ORDER BY sum_{meas_list[0]} DESC LIMIT 15"
                res = duckdb_engine.execute_query(sql)
                chart_data = [{"name": str(r[0]), "value": float(r[1]) if r[1] is not None else 0.0} for r in res["rows"]]
                result_payload = {
                    "type": "chart",
                    "chart_type": "bar",
                    "title": f"{meas_list[0]} by {dim}",
                    "summary": f"Calculated totals for {', '.join(meas_list)} aggregated across {dim}.",
                    "chart_data": chart_data,
                    "kpi_cards": [
                        {"label": f"Total {meas_list[0]}", "value": sum(c['value'] for c in chart_data), "formatted_value": f"${sum(c['value'] for c in chart_data):,.2f}"}
                    ],
                    "verification_trace": {"sql": sql, "execution_engine": "DuckDB"}
                }
            else:
                sql = f"SELECT {', '.join(agg_selects)} FROM {table_name}"
                res = duckdb_engine.execute_query(sql)
                if res["success"] and res["rows"]:
                    row = res["rows"][0]
                    idx = 0
                    for m in meas_list:
                        s_val, a_val = row[idx], row[idx + 1]
                        kpis.append({"label": f"Total {m}", "value": s_val, "formatted_value": f"${s_val:,.2f}" if s_val is not None else "$0"})
                        kpis.append({"label": f"Average {m}", "value": a_val, "formatted_value": f"${a_val:,.2f}" if a_val is not None else "$0"})
                        idx += 2

                result_payload = {
                    "type": "metric_card",
                    "title": f"Aggregation Results: {', '.join(meas_list)}",
                    "summary": f"Aggregated {len(meas_list)} measures across all {meta['row_count']:,} records in {meta['filename']}.",
                    "kpi_cards": kpis,
                    "verification_trace": {
                        "sql": sql,
                        "execution_engine": "DuckDB",
                        "execution_time_ms": res.get("execution_time_ms", 0)
                    }
                }

        # Update session memory
        session_ctx["last_intent"] = intent
        session_ctx["history"].append({"query": query, "intent": intent})
        self._sessions[session_id] = session_ctx

        # Generate business narrative summary
        narrative = LLMOrchestrator.generate_narrative_summary(query, result_payload, meta)
        result_payload["narrative"] = narrative

        # Suggested follow-up queries
        result_payload["suggested_followups"] = self._generate_suggested_followups(intent, columns_profile)

        return result_payload

    def _generate_suggested_followups(self, intent: str, columns: List[Dict[str, Any]]) -> List[str]:
        dims = [c["name"] for c in columns if c.get("role") == "dimension"]
        dim_name = dims[0] if dims else "Category"
        
        if intent == "AGGREGATION":
            return [
                f"Break down by {dim_name}",
                "Month-wise sales trend kaatu",
                "Calculate profit margin",
                "Find unusual transactions"
            ]
        elif intent == "TOP_N":
            return [
                "Now show only the top 5",
                "Compare this year with last year",
                "Profit yen decrease aachu?",
                "Create an executive dashboard"
            ]
        elif intent == "TIME_SERIES":
            return [
                "Forecast sales for the next six months",
                "Which region performs best?",
                "Identify loss-making products"
            ]
        return [
            "Total sales evlo?",
            "Month-wise sales trend kaatu",
            "Top 10 products eduthu kudu",
            "Duplicate rows remove pannu"
        ]

conversational_analyst = ConversationalAnalyst()
