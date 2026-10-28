# DataPilot AI — Autonomous Data Analyst Platform

> **Production-grade, AI-powered Autonomous Data Analytics Platform that automates the complete workflow of a professional Data Analyst.**

DataPilot AI bridges the power of **DuckDB columnar OLAP**, **Polars/Pandas transformations**, an **Excel Intelligence calculation engine (60+ compatible functions)**, **statistical & machine learning models**, and a **bilingual Natural Language Analyst (English & Tanglish)** into a unified, high-performance web workspace.

---

## Architecture Overview

```
DataPilot AI
├── Frontend (React 19, Vite, TypeScript, Tailwind CSS, Recharts, Lucide)
│   ├── Executive Dashboard Overview (Dynamic KPIs, Area/Bar/Donut charts, filters)
│   ├── AI Data Analyst Chat (English & Tanglish natural-language analysis)
│   ├── Dataset Explorer (TanStack virtualized table, server-side pagination & sorting)
│   ├── Data Cleaning Studio (Imputation, duplicate removal preview, outlier capping, undo/redo)
│   ├── Automatic Column Intelligence (type-aware analysis, interactive charts, exportable results)
│   ├── SQL Analytics Workspace (DuckDB query editor, EXPLAIN plan, schema browser)
│   ├── Statistical BI Studio (Parametric descriptive statistics, Pearson correlation, Pareto 80/20)
│   ├── Forecasting & ML (Time-series with 95% confidence intervals, K-Means segmentation)
│   ├── Export Centre (Multi-tab styled Excel, PDF summaries, CSV downloads)
│   └── Database Connectors (PostgreSQL, MySQL, SQLite read-only introspectors)
│
└── Backend (FastAPI, Python 3.12, DuckDB, Polars, PyArrow, Scikit-learn, OpenPyXL, ReportLab)
    ├── /api/datasets    - File ingestion (CSV, XLSX multi-sheet, Parquet, JSON), schema profiler
    ├── /api/chat        - Multi-turn NLP analyst with deterministic fallback
    ├── /api/dashboard   - Dynamic schema-driven dashboard generator
    ├── /api/cleaning    - Reversible transformation pipeline & preview diffs
    ├── /api/formulas    - Excel formula AST evaluator & registry
    ├── /api/sql         - Safe read-only DuckDB analytical engine
    ├── /api/analytics   - Descriptive stats, correlation heatmap, Pareto 80/20
    ├── /api/ml          - Time-series linear/polynomial forecasting & K-Means clustering
    ├── /api/reports     - Presentation-grade Excel (.xlsx), PDF executive reports, CSV
    └── /api/connectors  - External relational database connectors
```

---

## Core Capabilities

### 1. High-Performance Columnar Engine (100,000+ Rows)
- Powered by an in-memory **DuckDB OLAP engine** with vectorized execution.
- Instant sub-second aggregations, group-bys, and window calculations across 100,000+ rows without freezing the UI.
- Never calculates totals or averages from a display sample: all calculations run against the full dataset.

### 2. Conversational AI Analyst (English & Tanglish)
- Resolves natural language business queries into safe, structured DuckDB execution plans.
- Full bilingual conversational support for English and Tamil-English (Tanglish):
  - *"Total sales evlo?"* &rarr; Computes grand total sum of Sales.
  - *"Month-wise sales trend kaatu."* &rarr; Generates time-series monthly trend area chart.
  - *"Top 10 products eduthu kudu."* &rarr; Ranks top 10 categories/products by volume.
  - *"Profit yen decrease aachu?"* &rarr; Root-cause variance analysis on loss-making segments.
  - *"Duplicate rows remove pannu."* &rarr; Launches duplicate detection with confirmation preview.
  - *"Excel formula illama profit calculate pannu."* &rarr; Derives profit margin percentage automatically.
- **Conversational Memory**: Supports continuous follow-up filters (e.g., *"Now show only Chennai"* layers onto preceding queries).
- **Natural Language Analyst**: Answers dataset-grounded questions with concise insights and charts without exposing calculation internals in the user interface.
- **100% Deterministic Local Fallback**: Never requires an external AI API key for calculations, filtering, or aggregations. Supports optional Gemini / OpenAI / Claude integration via backend environment variables.

### 3. Automatic Column Intelligence
- Select one or two columns for automatic type detection and suitable summaries, distributions, group comparisons, numeric relationships, and monthly trends.
- Results include KPI cards, ranked tables, interactive charts, concise insights, and CSV downloads. Unsupported combinations explain the limitation rather than presenting misleading output.
- Objective selection, optional date filtering, and automatic analysis are available without exposing calculation syntax.

### 4. Automatic Data Cleaning Studio
- Quality checks cover missing values, duplicates, whitespace, invalid numeric/date values, unusual distributions, cardinality, and potentially sensitive fields.
- The uploaded source is retained separately from the working dataset; cleaning can be undone or reset to the original.
- **Duplicate Management**: Identifies redundant records, displays before/after previews, and requires user confirmation prior to execution.
- **Missing Value Imputation**: Configurable strategies: Mean, Median, Mode, Forward-fill, or Drop.
- **Outlier Detection**: Interquartile Range (IQR) and 3-Sigma Z-Score with Winsorizing (capping), dropping, or flag columns.
- **Standardization**: Text trimming, title casing, and ISO 8601 (`YYYY-MM-DD`) date normalization.
- **Reversible Pipeline**: Full Undo / Redo stack with an audit log of all transformations.

### 5. Statistical BI & Machine Learning
- **Parametric Descriptive Statistics**: Mean, Standard Deviation, Skewness, Median, Quartiles (Q1, Q3).
- **Correlation Heatmap**: Pearson correlation matrix across numerical variables.
- **Pareto 80/20 Analysis**: Identifies vital-few categories driving 80% of volume.
- **Predictive Time-Series Forecasting**: Linear trend and polynomial projection with 95% confidence interval bounds, holdout validation (RMSE, MAE, R²), and explicit model assumptions.
- **Customer Segmentation**: Unsupervised K-Means clustering with feature profiling.

### 6. Export & Report Centre
- **Multi-Tab Excel Reports**: Presentation-grade `.xlsx` with an Executive KPI Summary tab, formatted data grid with frozen header panes, and an audit metadata worksheet.
- **Executive PDF Summaries**: Generated via ReportLab with KPI tables, business narratives, and verification traces.
- **Cleaned CSV**: Instant streaming export.

---

## 14 Acceptance Criteria Test Results

The platform has been validated against all 14 acceptance test scenarios via `pytest`:

| # | Test Scenario | Expected Outcome | Status |
|---|---|---|---|
| **Test 1** | 100,000 Rows CSV Upload | Accurately loads 100,000+ rows into DuckDB and executes aggregations | **PASSED** |
| **Test 2** | Multi-Sheet Excel Workbook | Detects multiple sheets (`Revenue_Streams`, `Operating_Expenses`) | **PASSED** |
| **Test 3** | "Calculate total sales and average profit" | Returns verified KPI cards for Sales and Profit | **PASSED** |
| **Test 4** | "Create a monthly sales dashboard" | Dynamically generates KPI cards, area trend chart, and filters | **PASSED** |
| **Test 5** | "Find top 10 products by profit" | Ranks categories descending by profit | **PASSED** |
| **Test 6** | "Calculate profit margin without Excel formulas" | Automatically derives `(Profit / Sales) * 100` | **PASSED** |
| **Test 7** | "Find and remove duplicate records" | Previews redundant rows and applies deduplication upon confirmation | **PASSED** |
| **Test 8** | Conversational Follow-Up Query | Layers context (e.g., *"Now show only Chennai"*) onto previous results | **PASSED** |
| **Test 9** | Independent SQL Verification | Validates DuckDB SQL result against independently calculated Pandas sum | **PASSED** |
| **Test 10** | Time-Series Forecasting | Computes 6-month forecast with RMSE, MAE, and 95% confidence intervals | **PASSED** |
| **Test 11** | Cleaned Dataset Export | Exports valid multi-sheet Excel file with accurate dimensions | **PASSED** |
| **Test 12** | Formula Engine Function Parity | Tests SUM, AVERAGE, XLOOKUP, blanks, and error handling | **PASSED** |
| **Test 13** | Edge Case & Ambiguous Query Handling | Gracefully reports `#REF!` without hallucinating fake results | **PASSED** |
| **Test 14** | Complete UI & API Endpoint Health | All API routers, health checks, and registries operational | **PASSED** |

---

## Quick Start Guide (Windows)

### Prerequisites
- **Python 3.10+** (Tested on Python 3.12.1)
- **Node.js 18+** (Tested on Node.js v24.18.0)

### 1. One-Click Launch
Double-click `start.bat` in the project root:
```powershell
.\start.bat
```
This script automatically activates the virtual environment, installs requirements if needed, builds the frontend, and launches the server at `http://127.0.0.1:8000`.

### 2. Manual Step-by-Step Installation

#### Step A: Backend Setup
```powershell
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r backend\requirements.txt

# Run backend test suite
cd backend
pytest -v tests\test_acceptance.py
cd ..
```

#### Step B: Frontend Setup
```powershell
cd frontend
npm install
npm run build
cd ..
```

#### Step C: Launch Server
```powershell
cd backend
..\venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser.

---

## Environment Variables Configuration

Copy `.env.example` to `.env` in the root folder:
```env
HOST=127.0.0.1
PORT=8000
DEBUG=True

# Storage directories
UPLOAD_DIR=./data/uploads
EXPORT_DIR=./data/exports
SAMPLES_DIR=./data/samples

# Optional LLM Configuration (Deterministic NLP runs 100% locally if set to 'none')
LLM_PROVIDER=none # 'none', 'gemini', 'openai', 'anthropic', 'ollama'
GEMINI_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
OLLAMA_BASE_URL=http://localhost:11434

# Security & Limits
MAX_UPLOAD_SIZE_MB=250
QUERY_TIMEOUT_SECONDS=60
MAX_PREVIEW_ROWS=1000
```

---

## Security and Data Governance
- **Zero API Key Leakage**: LLM API keys are strictly maintained on the backend and never exposed to client browsers.
- **Read-Only Database Enforcement**: Connected production SQL databases and user query inputs disallow destructive operations (`DROP`, `DELETE`, `UPDATE`, `ALTER`, `ATTACH`).
- **Data Privacy**: No dataset records are sent to external third parties when using the default deterministic NLP engine.
- **Reversible Transformations**: Original datasets are never overwritten; state changes are recorded in an in-memory rollback stack.

---

## License
MIT License. Built for enterprise autonomous data analytics.
