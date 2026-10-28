import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.config import settings

class PDFExporter:
    """
    Executive PDF Report Generator:
    Generates presentation-ready summaries, KPIs, and audit details.
    """

    @classmethod
    def export_summary_pdf(
        cls,
        title: str,
        kpis: List[Dict[str, Any]],
        narrative: Dict[str, Any],
        row_count: int,
        table_name: str
    ) -> Path:
        timestamp = int(time.time())
        filename = f"DataPilot_Summary_{timestamp}.pdf"
        export_path = settings.EXPORT_DIR / filename

        doc = SimpleDocTemplate(str(export_path), pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#EF4444')
        )
        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#71717A')
        )
        heading_style = ParagraphStyle(
            'SectionHead',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=16,
            textColor=colors.HexColor('#18181B')
        )
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#27272A')
        )

        elements = []

        # Title
        elements.append(Paragraph("DataPilot AI — Executive Analysis Report", title_style))
        elements.append(Paragraph(f"{title} | Analyzed Source: {table_name} ({row_count:,} rows)", subtitle_style))
        elements.append(Spacer(1, 15))

        # KPI Table
        if kpis:
            elements.append(Paragraph("Executive Metrics", heading_style))
            elements.append(Spacer(1, 8))
            
            kpi_data = [["Metric", "Value", "Trend"]]
            for k in kpis[:8]:
                kpi_data.append([
                    k.get("label", ""),
                    k.get("formatted_value", str(k.get("value", ""))),
                    k.get("change_pct", "Stable")
                ])
            
            kpi_table = Table(kpi_data, colWidths=[200, 180, 140])
            kpi_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#18181B')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E4E4E7')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F4F4F5')])
            ]))
            elements.append(kpi_table)
            elements.append(Spacer(1, 15))

        # Narrative Findings
        elements.append(Paragraph("Executive Business Findings", heading_style))
        elements.append(Spacer(1, 6))
        
        exec_sum = narrative.get("executive_summary", "Analysis completed successfully across full dataset.")
        elements.append(Paragraph(f"<b>Summary:</b> {exec_sum}", body_style))
        elements.append(Spacer(1, 6))

        what_happened = narrative.get("what_happened", "")
        if what_happened:
            elements.append(Paragraph(f"<b>What Happened:</b> {what_happened}", body_style))
            elements.append(Spacer(1, 6))

        magnitude = narrative.get("magnitude_of_change", "")
        if magnitude:
            elements.append(Paragraph(f"<b>Magnitude of Change:</b> {magnitude}", body_style))
            elements.append(Spacer(1, 6))

        risks = narrative.get("risks_and_anomalies", "")
        if risks:
            elements.append(Paragraph(f"<b>Risks & Anomalies:</b> {risks}", body_style))
            elements.append(Spacer(1, 6))

        actions = narrative.get("recommended_actions", "")
        if actions:
            elements.append(Paragraph(f"<b>Recommended Action:</b> {actions}", body_style))
            elements.append(Spacer(1, 15))

        # Audit footer
        elements.append(Paragraph(f"Verified Computation Engine: DuckDB Columnar OLAP | Trace ID: {timestamp}", subtitle_style))

        doc.build(elements)
        return export_path
