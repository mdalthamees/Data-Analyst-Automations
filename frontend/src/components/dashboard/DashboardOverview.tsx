import React, { useState, useEffect } from 'react';
import { 
  Download, 
  Sparkles, 
  RefreshCw, 
  TrendingUp, 
  TrendingDown, 
  Filter, 
  Maximize2,
  Calendar,
  FileSpreadsheet,
  FileText
} from 'lucide-react';
import { DashboardConfig, DatasetMeta } from '../../types';
import { DashboardService, ReportsService } from '../../services/api';
import { ChartRenderer } from './ChartRenderer';

interface DashboardOverviewProps {
  activeDataset?: DatasetMeta;
  onNavigateToChat: (initialPrompt?: string) => void;
}

export const DashboardOverview: React.FC<DashboardOverviewProps> = ({
  activeDataset,
  onNavigateToChat
}) => {
  const [dashboard, setDashboard] = useState<DashboardConfig | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [activeFilter, setActiveFilter] = useState<{ [key: string]: string }>({});

  useEffect(() => {
    if (activeDataset?.id) {
      loadDashboard(activeDataset.id);
    }
  }, [activeDataset?.id]);

  const loadDashboard = async (datasetId: string) => {
    setLoading(true);
    try {
      const data = await DashboardService.generate(datasetId);
      setDashboard(data);
    } catch (err) {
      console.error("Dashboard loading error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleExportPdf = async () => {
    if (!activeDataset || !dashboard) return;
    try {
      const blob = await ReportsService.exportPdf(
        activeDataset.id,
        dashboard.title,
        {
          executive_summary: `Autonomous performance dashboard for ${activeDataset.filename}. All metrics derived from verified computations.`,
          what_happened: `Computed ${dashboard.kpis.length} executive KPIs across ${activeDataset.row_count.toLocaleString()} records.`
        },
        dashboard.kpis
      );
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `DataPilot_${dashboard.title.replace(/\s+/g, '_')}.pdf`;
      a.click();
    } catch (e) {
      console.error("PDF export error", e);
    }
  };

  if (!activeDataset) {
    return (
      <div className="flex flex-col items-center justify-center h-[70vh] text-center p-6">
        <div className="w-16 h-16 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center mb-4">
          <Sparkles className="text-red-400" size={32} />
        </div>
        <h3 className="text-lg font-bold text-white mb-2">No Dataset Active</h3>
        <p className="text-zinc-400 text-sm max-w-md mb-6">
          Upload a CSV or Excel file, or load one of our production sample datasets to generate your dynamic analytics dashboard.
        </p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
      {/* Top Bar: Title & Controls */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-[#121216] border border-[#23232a] p-4 rounded-xl">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-extrabold text-white tracking-tight">
              {dashboard?.title || 'Executive Analytics Dashboard'}
            </h1>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-red-500/10 text-red-400 border border-red-500/20">
              Live DuckDB OLAP
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-1">
            Autonomous dynamic dashboard derived from {activeDataset.filename} ({activeDataset.row_count.toLocaleString()} rows).
          </p>
        </div>

        <div className="flex items-center space-x-2.5">
          <button
            onClick={() => loadDashboard(activeDataset.id)}
            disabled={loading}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-[#1c1c23] text-zinc-300 border border-[#2c2c36] hover:bg-[#262630] transition-all"
          >
            <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
            <span>Regenerate</span>
          </button>

          <a
            href={ReportsService.getExcelUrl(activeDataset.id)}
            download
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-[#1c1c23] text-zinc-300 border border-[#2c2c36] hover:bg-[#262630] transition-all"
          >
            <FileSpreadsheet size={13} className="text-emerald-400" />
            <span>Excel</span>
          </a>

          <button
            onClick={handleExportPdf}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-red-600 hover:bg-red-500 text-white shadow-md shadow-red-500/20 transition-all"
          >
            <Download size={13} />
            <span>Export PDF</span>
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      {dashboard?.kpis && dashboard.kpis.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {dashboard.kpis.map((kpi, index) => {
            const isPositive = kpi.trend === 'up';
            const isHighlight = kpi.highlight;

            return (
              <div
                key={kpi.id || index}
                className={`p-4 rounded-xl border transition-all ${
                  isHighlight 
                    ? 'bg-gradient-to-b from-[#1c1618] to-[#141214] border-red-500/30 shadow-lg shadow-red-500/5' 
                    : 'bg-[#121216] border-[#23232a]'
                }`}
              >
                <div className="flex items-center justify-between text-xs text-zinc-400 mb-2">
                  <span>{kpi.label}</span>
                  {kpi.change_pct && (
                    <span className={`flex items-center space-x-0.5 text-[11px] font-semibold ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
                      {isPositive ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                      <span>{kpi.change_pct}</span>
                    </span>
                  )}
                </div>
                <div className="text-2xl font-extrabold text-white tracking-tight">
                  {kpi.formatted_value}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Filter Toolbar (if filters available) */}
      {dashboard?.filters && dashboard.filters.length > 0 && (
        <div className="flex flex-wrap items-center gap-3 bg-[#121216] border border-[#23232a] p-3 rounded-xl text-xs text-zinc-400">
          <span className="flex items-center space-x-1 font-semibold text-zinc-300">
            <Filter size={13} />
            <span>Interactive Filters:</span>
          </span>
          {dashboard.filters.map((f) => (
            <div key={f.column} className="flex items-center space-x-1.5">
              <span className="text-zinc-500">{f.label}:</span>
              <select
                value={activeFilter[f.column] || 'All'}
                onChange={(e) => setActiveFilter({ ...activeFilter, [f.column]: e.target.value })}
                className="bg-[#1a1a21] text-zinc-200 border border-[#2e2e38] rounded px-2 py-1 text-xs focus:outline-none focus:border-red-500"
              >
                <option value="All">All {f.label}s</option>
                {f.options.map((opt) => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
            </div>
          ))}
          <button
            onClick={() => setActiveFilter({})}
            className="text-[11px] text-red-400 hover:underline ml-auto"
          >
            Reset Filters
          </button>
        </div>
      )}

      {/* Dynamic Charts Grid */}
      {dashboard?.charts && dashboard.charts.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {dashboard.charts.map((chart) => (
            <div
              key={chart.id}
              className="bg-[#121216] border border-[#23232a] rounded-xl p-5 shadow-sm"
            >
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-sm font-bold text-white tracking-tight">
                    {chart.title}
                  </h3>
                  {chart.description && (
                    <p className="text-xs text-zinc-400 mt-0.5">{chart.description}</p>
                  )}
                </div>
                <button
                  onClick={() => onNavigateToChat(`Explain chart: ${chart.title}`)}
                  className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-[#1f1f27] transition-all"
                  title="Ask AI Data Analyst about this chart"
                >
                  <Sparkles size={14} className="text-red-400" />
                </button>
              </div>

              <ChartRenderer
                type={chart.type}
                data={chart.data}
                xKey={chart.x_key}
                yKeys={chart.y_keys}
                nameKey={chart.name_key}
                valueKey={chart.value_key}
                playKey={chart.play_key}
                color={chart.color || '#ef4444'}
                height={260}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
