from typing import Optional, List, Literal
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.dataset_manager import dataset_manager
from app.analytics.statistical_analysis import StatisticalAnalysis

router = APIRouter(prefix="/api/analytics", tags=["Statistical Analytics"])


class AutomaticAnalysisRequest(BaseModel):
    dataset_id: str
    columns: List[str] = Field(min_length=1, max_length=20)
    objective: Literal["auto", "distribution", "compare", "trend", "segments"] = "auto"
    date_column: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


def _json_number(value):
    if pd.isna(value) or not np.isfinite(float(value)):
        return None
    return round(float(value), 4)


def _detect_date(series: pd.Series, name: str = "") -> Optional[pd.Series]:
    if pd.api.types.is_datetime64_any_dtype(series):
        parsed = pd.to_datetime(series, errors="coerce")
    elif any(token in name.lower() for token in ("date", "time", "month", "year")):
        parsed = pd.to_datetime(series, errors="coerce")
    else:
        return None
    return parsed if parsed.notna().mean() >= 0.7 else None


@router.post("/automatic")
def automatic_analysis(req: AutomaticAnalysisRequest):
    try:
        meta = dataset_manager.get_dataset(req.dataset_id)
        if not meta:
            raise HTTPException(status_code=404, detail="Dataset not found")
        if len(set(req.columns)) != len(req.columns):
            raise HTTPException(status_code=400, detail="Choose distinct columns.")
        df = dataset_manager.get_dataset_dataframe(req.dataset_id)
        missing_columns = [column for column in req.columns if column not in df.columns]
        if missing_columns:
            raise HTTPException(status_code=400, detail=f"Unknown columns: {', '.join(missing_columns)}")

        selected = df.loc[:, req.columns].copy()
        date_col = req.date_column if req.date_column in df.columns else None
        if date_col and (req.date_from or req.date_to):
            parsed_filter = pd.to_datetime(df[date_col], errors="coerce")
            mask = parsed_filter.notna()
            if req.date_from:
                mask &= parsed_filter >= pd.to_datetime(req.date_from, errors="raise")
            if req.date_to:
                mask &= parsed_filter <= pd.to_datetime(req.date_to, errors="raise") + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
            selected = selected.loc[mask]

        columns = list(selected.columns)
        numeric: dict = {}
        dates: dict = {}
        for column in columns:
            series = selected[column]
            converted = pd.to_numeric(series, errors="coerce")
            if pd.api.types.is_numeric_dtype(series) or (series.notna().sum() and converted.notna().sum() / series.notna().sum() >= 0.85):
                numeric[column] = converted
                continue
            parsed_date = _detect_date(series, column)
            if parsed_date is not None:
                dates[column] = parsed_date

        result = {
            "supported": True, "columns_used": columns, "row_count": int(len(selected)),
            "analysis_type": "", "title": "", "summary": "", "limitations": [],
            "insights": [], "kpis": [], "chart": None, "table": {"columns": [], "rows": []}
        }

        def table_for(frame: pd.DataFrame):
            clean = frame.astype(object).where(pd.notna(frame), None)
            return {
                "columns": [str(c) for c in frame.columns],
                "rows": clean.to_dict(orient="records")
            }

        if selected.empty:
            result.update(supported=False, summary="No rows match the selected date range. Adjust the range and try again.")
            return result

        if len(columns) > 2:
            numeric_cols = [column for column in columns if column in numeric]
            date_cols = [column for column in columns if column in dates]
            category_cols = [column for column in columns if column not in numeric and column not in dates]
            if len(numeric_cols) == len(columns):
                values = pd.DataFrame({column: numeric[column] for column in numeric_cols})
                values = values.replace([np.inf, -np.inf], np.nan)
                stats = []
                for column in numeric_cols:
                    series = values[column].dropna()
                    stats.append({
                        "Measure": column,
                        "Total": _json_number(series.sum()) if len(series) else None,
                        "Average": _json_number(series.mean()) if len(series) else None,
                        "Median": _json_number(series.median()) if len(series) else None,
                        "Minimum": _json_number(series.min()) if len(series) else None,
                        "Maximum": _json_number(series.max()) if len(series) else None,
                        "Std. deviation": _json_number(series.std()) if len(series) else None,
                        "Valid values": int(series.count())
                    })
                chart_data = values[numeric_cols[:2]].dropna()
                play_key = None
                if date_col:
                    point_dates = _detect_date(df.loc[chart_data.index, date_col], date_col)
                    if point_dates is not None:
                        frames = point_dates.dt.to_period("M").astype(str)
                        if frames.nunique() > 1:
                            chart_data["frame"] = frames
                            play_key = "frame"
                if len(chart_data) > 1500:
                    chart_data = chart_data.sample(1500, random_state=7)
                chart_data = chart_data.rename(columns={numeric_cols[0]: "x", numeric_cols[1]: "y"})
                result.update(
                    analysis_type="relationship",
                    title="Numeric measures overview",
                    summary=f"Summarized {len(numeric_cols)} numeric columns across {len(values):,} rows. Pairwise association is descriptive, not causal.",
                    insights=[f"Correlation between {numeric_cols[0]} and {numeric_cols[1]} is {_json_number(values[numeric_cols[0]].corr(values[numeric_cols[1]]))}." if values[numeric_cols[0]].corr(values[numeric_cols[1]]) == values[numeric_cols[0]].corr(values[numeric_cols[1]]) else "Some selected columns have insufficient variation to calculate correlation."],
                    kpis=[{"label": f"Total {column}", "value": row["Total"]} for column, row in zip(numeric_cols, stats)],
                    chart={
                        "type": "scatter", "title": f"{numeric_cols[1]} vs {numeric_cols[0]}",
                        "x_key": "x", "y_key": "y",
                        "x_label": numeric_cols[0], "y_label": numeric_cols[1],
                        "data": chart_data.to_dict(orient="records"),
                        **({"play_key": play_key} if play_key else {})
                    } if len(numeric_cols) >= 2 and len(chart_data) >= 3 else None,
                    table=table_for(pd.DataFrame(stats))
                )
            elif date_cols and numeric_cols and not category_cols and len(date_cols) == 1:
                date_name = date_cols[0]
                frame_data = pd.DataFrame({"period": dates[date_name], **{column: numeric[column] for column in numeric_cols}})
                frame_data = frame_data.replace([np.inf, -np.inf], np.nan).dropna(subset=["period"])
                frame_data["Period"] = frame_data["period"].dt.to_period("M").dt.to_timestamp()
                frame = frame_data.groupby("Period", as_index=False)[numeric_cols].sum(min_count=1)
                if frame["Period"].nunique() < 2:
                    result.update(supported=False, summary="There are too few distinct dates to identify trends for these measures. Choose a wider date range.")
                    return result
                frame["Period"] = frame["Period"].dt.strftime("%Y-%m")
                totals = [{"label": f"Total {column}", "value": _json_number(frame[column].sum())} for column in numeric_cols]
                result.update(
                    analysis_type="trend", title="Selected measures over time",
                    summary=f"Monthly trends for {len(numeric_cols)} measures across {len(frame)} periods.",
                    insights=["Trends show change over time and do not establish its cause."],
                    kpis=totals,
                    chart={
                        "type": "line", "title": "Monthly trends", "x_key": "Period",
                        "y_key": numeric_cols[0], "y_keys": numeric_cols,
                        "x_label": "Month", "y_label": "Value", "data": frame.to_dict(orient="records")
                    },
                    table=table_for(frame)
                )
            elif category_cols and numeric_cols and not date_cols:
                measures = pd.DataFrame({column: numeric[column] for column in numeric_cols})
                measures = measures.replace([np.inf, -np.inf], np.nan)
                group_keys = selected[category_cols].fillna("(Missing)").astype(str)
                source = pd.concat([group_keys, measures], axis=1)
                aggregations = {column: ["sum", "mean", "count"] for column in numeric_cols}
                grouped = source.groupby(category_cols, dropna=False).agg(aggregations)
                grouped.columns = [f"{column} {stat}" for column, stat in grouped.columns]
                frame = grouped.reset_index()
                totals_columns = [f"{column} sum" for column in numeric_cols]
                frame = frame.sort_values(totals_columns[0], ascending=False, na_position="last").head(30)
                chart_frame = frame.copy()
                chart_frame["Group"] = chart_frame[category_cols].astype(str).agg(" / ".join, axis=1)
                result.update(
                    analysis_type="segments", title=f"Measures by {', '.join(category_cols)}",
                    summary=f"Compared {len(numeric_cols)} measures across {len(frame)} ranked groups.",
                    insights=[f"Top group by {numeric_cols[0]}: {chart_frame.iloc[0]['Group']}." if len(chart_frame) else "No grouped values are available."],
                    kpis=[{"label": f"Total {column}", "value": _json_number(measures[column].sum())} for column in numeric_cols] + [{"label": "Groups", "value": int(source.groupby(category_cols, dropna=False).ngroups)}],
                    chart={
                        "type": "bar", "title": f"{numeric_cols[0]} by selected groups",
                        "x_key": "Group", "y_key": totals_columns[0],
                        "y_keys": totals_columns, "x_label": "Group", "y_label": "Total",
                        "data": chart_frame.to_dict(orient="records")
                    },
                    table=table_for(frame)
                )
            elif len(category_cols) == len(columns):
                frame = selected.groupby(category_cols, dropna=False).size().rename("Records").reset_index()
                frame = frame.sort_values("Records", ascending=False).head(50)
                chart_frame = frame.copy()
                chart_frame["Group"] = chart_frame[category_cols].astype(str).agg(" / ".join, axis=1)
                result.update(
                    analysis_type="segments", title="Category combinations",
                    summary=f"Most frequent combinations across {len(frame)} groups.",
                    kpis=[{"label": "Combinations", "value": int(len(frame))}, {"label": "Records", "value": int(len(selected))}],
                    chart={"type": "bar", "title": "Records by category combination", "x_key": "Group", "y_key": "Records", "x_label": "Group", "y_label": "Records", "data": chart_frame.to_dict(orient="records")},
                    table=table_for(frame)
                )
            else:
                result.update(
                    supported=False,
                    summary="These selected columns mix data types that do not support one reliable combined analysis. Try numeric measures together, categories with numeric measures, or dates with numeric measures."
                )
                return result
        elif len(columns) == 1 and columns[0] in numeric:
            name = columns[0]
            values = numeric[name].replace([np.inf, -np.inf], np.nan).dropna()
            if values.empty:
                result.update(supported=False, summary=f"{name} has no usable numeric values to summarize.")
                return result
            counts, edges = np.histogram(values, bins=min(12, max(4, int(np.sqrt(len(values))))))
            chart_data = [
                {"range": f"{edges[i]:,.2f}–{edges[i + 1]:,.2f}", "count": int(counts[i])}
                for i in range(len(counts))
            ]
            q1, q3 = values.quantile([0.25, 0.75])
            outlier_count = int(((values < q1 - 1.5 * (q3 - q1)) | (values > q3 + 1.5 * (q3 - q1))).sum())
            result.update(
                analysis_type="distribution", title=f"{name} distribution",
                summary=f"Summary of {len(values):,} valid {name} values.",
                insights=[f"{outlier_count:,} values fall outside the usual interquartile range."],
                kpis=[
                    {"label": f"Total {name}", "value": _json_number(values.sum())},
                    {"label": f"Average", "value": _json_number(values.mean())},
                    {"label": "Median", "value": _json_number(values.median())},
                    {"label": "Minimum", "value": _json_number(values.min())},
                    {"label": "Maximum", "value": _json_number(values.max())},
                    {"label": "Std. deviation", "value": _json_number(values.std())}
                ],
                chart={"type": "bar", "title": f"Distribution of {name}", "x_key": "range", "y_key": "count", "x_label": name, "y_label": "Records", "data": chart_data},
                table=table_for(pd.DataFrame({"Statistic": ["Count", "Minimum", "Maximum", "Missing"], "Value": [int(values.count()), _json_number(values.min()), _json_number(values.max()), int(selected[name].isna().sum())]}))
            )
        elif len(columns) == 1 and columns[0] in dates:
            name = columns[0]
            dates_frame = dates[name].dropna().dt.to_period("M").astype(str).value_counts().sort_index()
            frame = dates_frame.rename_axis("Period").reset_index(name="Records")
            result.update(
                analysis_type="time", title=f"Records over time",
                summary=f"Records grouped by month across {len(frame)} periods.",
                chart={"type": "line", "title": f"Records by month", "x_key": "Period", "y_key": "Records", "x_label": "Month", "y_label": "Records", "data": frame.to_dict(orient="records")},
                kpis=[{"label": "Periods", "value": int(len(frame))}, {"label": "Records", "value": int(len(selected))}],
                table=table_for(frame)
            )
        elif len(columns) == 1:
            name = columns[0]
            counts = selected[name].fillna("(Missing)").astype(str).value_counts().head(20)
            frame = counts.rename_axis(name).reset_index(name="Records")
            result.update(
                analysis_type="categories", title=f"{name} breakdown",
                summary=f"{selected[name].nunique(dropna=True):,} distinct values; showing the most common {len(frame)}.",
                chart={"type": "bar", "title": f"Most common {name}", "x_key": name, "y_key": "Records", "x_label": name, "y_label": "Records", "data": frame.to_dict(orient="records")},
                kpis=[{"label": "Distinct values", "value": int(selected[name].nunique(dropna=True))}, {"label": "Most common", "value": str(counts.index[0]) if len(counts) else "—"}, {"label": "Records", "value": int(len(selected))}],
                table=table_for(frame)
            )
        else:
            numeric_cols = [c for c in columns if c in numeric]
            date_cols = [c for c in columns if c in dates]
            category_cols = [c for c in columns if c not in numeric and c not in dates]
            if len(numeric_cols) == 2:
                x_name, y_name = numeric_cols
                paired = pd.DataFrame({"x": numeric[x_name], "y": numeric[y_name]}).replace([np.inf, -np.inf], np.nan).dropna()
                if len(paired) < 3 or paired["x"].nunique() < 2 or paired["y"].nunique() < 2:
                    result.update(supported=False, summary="These columns do not contain enough varied numeric pairs for a meaningful relationship. Try a category with a numeric measure.")
                    return result
                corr = _json_number(paired["x"].corr(paired["y"]))
                sampled = paired.sample(min(len(paired), 1500), random_state=7)
                outlier_counts = []
                for measure_name in ("x", "y"):
                    q1, q3 = paired[measure_name].quantile([0.25, 0.75])
                    iqr = q3 - q1
                    outlier_counts.append(int(((paired[measure_name] < q1 - 1.5 * iqr) | (paired[measure_name] > q3 + 1.5 * iqr)).sum()))
                kpis = [
                    {"label": f"Total {x_name}", "value": _json_number(paired.x.sum())},
                    {"label": f"Total {y_name}", "value": _json_number(paired.y.sum())},
                    {"label": "Correlation", "value": corr},
                    {"label": "Unusual values", "value": max(outlier_counts)},
                    {"label": "Valid pairs", "value": int(len(paired))}
                ]
                name_map = {name.lower(): name for name in (x_name, y_name)}
                profit_name = next((name_map[key] for key in name_map if "profit" in key), None)
                sales_name = next((name_map[key] for key in name_map if any(token in key for token in ("sales", "revenue", "turnover"))), None)
                if profit_name and sales_name:
                    total_sales = paired["x" if profit_name == y_name else "y"].sum()
                    total_profit = paired["x" if profit_name == x_name else "y"].sum()
                    if total_sales:
                        kpis.append({"label": "Profit margin", "value": f"{(total_profit / total_sales * 100):.2f}%"})
                result.update(
                    analysis_type="relationship", title=f"{x_name} and {y_name}",
                    summary=f"Compared {len(paired):,} valid pairs. Correlation describes association, not causation.",
                    insights=[f"The relationship is {'positive' if corr is not None and corr > 0 else 'negative' if corr is not None and corr < 0 else 'near zero'} (correlation {corr})."],
                    kpis=kpis,
                    chart={"type": "scatter", "title": f"{y_name} vs {x_name}", "x_key": "x", "y_key": "y", "x_label": x_name, "y_label": y_name, "data": sampled.to_dict(orient="records")},
                    table=table_for(pd.DataFrame([{"Measure": x_name, "Total": _json_number(paired.x.sum()), "Average": _json_number(paired.x.mean())}, {"Measure": y_name, "Total": _json_number(paired.y.sum()), "Average": _json_number(paired.y.mean())}]))
                )
            elif date_cols and numeric_cols:
                date_name, measure = date_cols[0], numeric_cols[0]
                frame_data = pd.DataFrame({"period": dates[date_name], "value": numeric[measure]})
                frame_data = frame_data.replace([np.inf, -np.inf], np.nan).dropna()
                if len(frame_data) < 2 or frame_data["period"].nunique() < 2:
                    result.update(supported=False, summary="There are too few distinct dates to identify a trend. Choose another date column or a wider date range.")
                    return result
                frame_data["Period"] = frame_data["period"].dt.to_period("M").dt.to_timestamp()
                frame = frame_data.groupby("Period", as_index=False)["value"].sum().rename(columns={"Period": "Period", "value": measure})
                frame["Period"] = frame["Period"].dt.strftime("%Y-%m")
                frame["Growth %"] = frame[measure].pct_change().mul(100).round(2)
                growth = frame["Growth %"].dropna()
                result.update(
                    analysis_type="trend", title=f"{measure} over time",
                    summary=f"Monthly trend across {len(frame)} periods, using {len(frame_data):,} valid records.",
                    insights=[f"Most recent month changed {growth.iloc[-1]:.1f}% from the prior month." if len(growth) else "More periods are needed to calculate growth."],
                    kpis=[{"label": f"Total {measure}", "value": _json_number(frame[measure].sum())}, {"label": "Monthly average", "value": _json_number(frame[measure].mean())}, {"label": "Latest change", "value": f"{growth.iloc[-1]:.1f}%" if len(growth) else "—"}],
                    chart={"type": "line", "title": f"Monthly {measure}", "x_key": "Period", "y_key": measure, "x_label": "Month", "y_label": measure, "data": frame.to_dict(orient="records")},
                    table=table_for(frame)
                )
            elif category_cols and numeric_cols:
                dimension, measure = category_cols[0], numeric_cols[0]
                grouped = pd.DataFrame({"category": selected[dimension].fillna("(Missing)").astype(str), "value": numeric[measure]})
                grouped = grouped.replace([np.inf, -np.inf], np.nan).dropna(subset=["value"])
                frame = grouped.groupby("category", as_index=False)["value"].agg(
                    **{"Total": "sum", "Average": "mean", "Records": "count"}
                )
                frame = frame.rename(columns={"category": dimension})
                frame = frame.sort_values("Total", ascending=False).head(30).rename(columns={"Total": f"Total {measure}", "Average": f"Avg. {measure}"})
                total = float(grouped.value.sum())
                frame["Share %"] = (frame[f"Total {measure}"] / total * 100).round(2) if total else 0
                result.update(
                    analysis_type="segments", title=f"{measure} by {dimension}",
                    summary=f"Ranked {len(frame)} groups by total {measure}.",
                    insights=[f"{frame.iloc[0][dimension]} leads with {frame.iloc[0][f'Total {measure}']:,.2f}." if len(frame) else "No grouped values are available.", f"{int((frame[f'Total {measure}'] < 0).sum())} displayed groups have a negative total."],
                    kpis=[{"label": f"Total {measure}", "value": _json_number(grouped.value.sum())}, {"label": f"Top {dimension}", "value": str(frame.iloc[0][dimension]) if len(frame) else "—"}, {"label": "Groups", "value": int(grouped.category.nunique())}, {"label": "Records", "value": int(len(grouped))}],
                    chart={"type": "bar", "title": f"{measure} by {dimension}", "x_key": dimension, "y_key": f"Total {measure}", "x_label": dimension, "y_label": measure, "data": frame.to_dict(orient="records")},
                    table=table_for(frame)
                )
            elif len(category_cols) == 2:
                left, right = category_cols
                frame = selected.groupby([left, right], dropna=False).size().rename("Records").reset_index().sort_values("Records", ascending=False).head(50)
                result.update(
                    analysis_type="segments", title=f"{left} and {right} comparison",
                    summary=f"Most frequent combinations across {len(frame)} groups.",
                    chart={"type": "bar", "title": f"Records by {left} / {right}", "x_key": left, "y_key": "Records", "x_label": left, "y_label": "Records", "data": frame.groupby(left, as_index=False)["Records"].sum().to_dict(orient="records")},
                    kpis=[{"label": "Combinations", "value": int(len(frame))}, {"label": "Records", "value": int(len(selected))}],
                    table=table_for(frame)
                )
            else:
                result.update(supported=False, summary="These columns do not support a reliable combined analysis. Try one numeric column, a category with a numeric measure, or a date with a numeric measure.")
                return result

        expected_types = {
            "distribution": {"distribution"},
            "compare": {"relationship", "segments"},
            "trend": {"trend"},
            "segments": {"segments"}
        }
        expected = expected_types.get(req.objective)
        if expected and result["analysis_type"] not in expected:
            suggestion = {
                "distribution": "Choose one numeric column for a distribution.",
                "compare": "Choose two comparable numeric or categorical columns.",
                "trend": "Choose a date column and a numeric measure for a trend.",
                "segments": "Choose a category and a numeric measure to compare groups."
            }[req.objective]
            result.update(
                supported=False,
                summary=f"The selected data does not support this objective. {suggestion}",
                chart=None,
                kpis=[],
                insights=[],
                table={"columns": [], "rows": []}
            )
            return result
        invalid_count = int(selected.isna().sum().sum())
        invalid_count += sum(int((numeric[column].isna() & selected[column].notna()).sum()) for column in numeric)
        if invalid_count:
            result["limitations"].append(f"{invalid_count:,} missing or invalid selected values were excluded from calculations.")
        return result
    except HTTPException:
        raise
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=f"Unable to analyze the selected data: {exc}")

@router.get("/descriptive/{dataset_id}")
def get_descriptive_stats(dataset_id: str):
    try:
        return StatisticalAnalysis.get_descriptive_stats(dataset_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Dataset not found")

@router.get("/correlation/{dataset_id}")
def get_correlation(dataset_id: str):
    try:
        return StatisticalAnalysis.get_correlation_matrix(dataset_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Dataset not found")

@router.get("/pareto/{dataset_id}")
def get_pareto(
    dataset_id: str,
    dimension: str = Query(..., description="Categorical dimension to group by"),
    measure: str = Query(..., description="Numeric measure to sum")
):
    try:
        return StatisticalAnalysis.get_pareto_analysis(dataset_id, dimension, measure)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/anomalies/{dataset_id}")
def get_anomalies(
    dataset_id: str,
    measure: str = Query(..., description="Numeric measure to analyze for outliers"),
    threshold: float = Query(3.0, description="Z-Score threshold")
):
    try:
        return StatisticalAnalysis.get_anomalies(dataset_id, measure, threshold)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
