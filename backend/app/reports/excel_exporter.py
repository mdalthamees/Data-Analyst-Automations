import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from app.config import settings

class ExcelExporter:
    """
    Professional Excel Report Generator:
    Creates multi-sheet, presentation-grade workbooks with custom styles,
    KPI summary blocks, auto-fitted columns, and formula preservation.
    """

    @classmethod
    def export_dataset_report(
        cls,
        df: pd.DataFrame,
        report_title: str,
        kpis: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        timestamp = int(time.time())
        filename = f"DataPilot_Report_{timestamp}.xlsx"
        export_path = settings.EXPORT_DIR / filename

        wb = openpyxl.Workbook()
        
        # Header style: Dark charcoal with red accent
        header_fill = PatternFill(start_color="18181B", end_color="18181B", fill_type="solid")
        header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        accent_font = Font(name="Segoe UI", size=14, bold=True, color="EF4444")
        kpi_title_font = Font(name="Segoe UI", size=9, bold=False, color="71717A")
        kpi_val_font = Font(name="Segoe UI", size=18, bold=True, color="18181B")
        
        border_thin = Border(
            left=Side(style='thin', color='E4E4E7'),
            right=Side(style='thin', color='E4E4E7'),
            top=Side(style='thin', color='E4E4E7'),
            bottom=Side(style='thin', color='E4E4E7')
        )

        # Sheet 1: Executive Summary
        ws_summary = wb.active
        ws_summary.title = "Executive Summary"
        ws_summary.views.sheetView[0].showGridLines = True

        ws_summary["A1"] = "DataPilot AI — Executive Analytics Report"
        ws_summary["A1"].font = accent_font
        ws_summary["A2"] = f"Report: {report_title} | Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}"
        ws_summary["A2"].font = Font(name="Segoe UI", size=10, italic=True, color="52525B")

        # Write KPI Blocks if provided
        start_row = 4
        if kpis:
            ws_summary.cell(row=start_row, column=1, value="Key Performance Indicators").font = Font(name="Segoe UI", size=12, bold=True)
            start_row += 1
            col_idx = 1
            for kpi in kpis[:6]:
                # Card box
                c_lbl = ws_summary.cell(row=start_row, column=col_idx, value=kpi.get("label", "Metric"))
                c_lbl.font = kpi_title_font
                c_lbl.fill = PatternFill(start_color="F4F4F5", end_color="F4F4F5", fill_type="solid")
                c_lbl.alignment = Alignment(horizontal="center")
                
                c_val = ws_summary.cell(row=start_row + 1, column=col_idx, value=kpi.get("formatted_value", str(kpi.get("value", 0))))
                c_val.font = kpi_val_font
                c_val.fill = PatternFill(start_color="F4F4F5", end_color="F4F4F5", fill_type="solid")
                c_val.alignment = Alignment(horizontal="center")

                ws_summary.column_dimensions[get_column_letter(col_idx)].width = 22
                col_idx += 1

            start_row += 4

        # Sheet 2: Data Records
        ws_data = wb.create_sheet(title="Data Records")
        ws_data.views.sheetView[0].showGridLines = True

        # Write Column Headers
        for col_idx, col_name in enumerate(df.columns, 1):
            cell = ws_data.cell(row=1, column=col_idx, value=str(col_name))
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="left", vertical="center")

        # Write Rows (limit to first 10,000 for excel export safety)
        max_export_rows = min(len(df), 25000)
        for row_idx, row_data in enumerate(df.iloc[:max_export_rows].values, 2):
            for col_idx, val in enumerate(row_data, 1):
                c = ws_data.cell(row=row_idx, column=col_idx, value=val if not pd.isna(val) else "")
                c.border = border_thin
                c.font = Font(name="Segoe UI", size=10)

        # Freeze Header Row
        ws_data.freeze_panes = "A2"

        # Auto-fit Column Widths
        for col in ws_data.columns:
            max_len = max(len(str(cell.value or '')) for cell in col[:100])
            col_letter = get_column_letter(col[0].column)
            ws_data.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 40)

        # Sheet 3: Methodology & Metadata
        ws_meta = wb.create_sheet(title="Audit & Metadata")
        ws_meta["A1"] = "Analysis Methodology & Verification Trace"
        ws_meta["A1"].font = Font(name="Segoe UI", size=12, bold=True)
        ws_meta["A3"] = "Total Rows in Dataset:"
        ws_meta["B3"] = len(df)
        ws_meta["A4"] = "Total Columns:"
        ws_meta["B4"] = len(df.columns)
        ws_meta["A5"] = "Computation Engine:"
        ws_meta["B5"] = "DuckDB Columnar OLAP Engine (v1.0)"
        ws_meta["A6"] = "Export Timestamp:"
        ws_meta["B6"] = pd.Timestamp.now().isoformat()

        wb.save(export_path)
        return export_path
