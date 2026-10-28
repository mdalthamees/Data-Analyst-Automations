import React, { useEffect, useMemo, useRef, useState } from 'react';
import { BarChart3, Download, ImageDown, RotateCcw, Sparkles } from 'lucide-react';
import { DatasetMeta } from '../../types';
import { AnalyticsService } from '../../services/api';
import { ChartRenderer } from '../dashboard/ChartRenderer';

interface ColumnIntelligenceProps {
  activeDataset?: DatasetMeta;
  datasets: DatasetMeta[];
  onSelectDataset: (id: string) => void;
}

type AnalysisResult = {
  supported: boolean;
  columns_used: string[];
  row_count: number;
  analysis_type: string;
  title?: string;
  summary: string;
  limitations?: string[];
  insights?: string[];
  kpis?: Array<{ label: string; value: string | number | null }>;
  chart?: {
    type: string;
    title: string;
    x_key: string;
    y_key: string;
    y_keys?: string[];
    play_key?: string;
    x_label: string;
    y_label: string;
    data: Array<Record<string, any>>;
  } | null;
  table?: { columns: string[]; rows: Array<Record<string, any>> };
};

const fieldClass = 'bg-[#18181f] border border-[#2b2b35] rounded-lg px-3 py-2 text-xs text-zinc-100 focus:outline-none focus:border-red-500';

export const ColumnIntelligence: React.FC<ColumnIntelligenceProps> = ({
  activeDataset,
  datasets,
  onSelectDataset
}) => {
  const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
  const [objective, setObjective] = useState('auto');
  const [dateColumn, setDateColumn] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [autoRun, setAutoRun] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [chartType, setChartType] = useState('');
  const chartContainer = useRef<HTMLDivElement>(null);

  const columns = activeDataset?.profile?.columns || [];
  const dateColumns = useMemo(
    () => columns.filter((column) => column.role === 'date' || column.inferred_type === 'date' || /date|time|month|year/i.test(column.name)),
    [columns]
  );

  useEffect(() => {
    if (!activeDataset?.id) {
      setSelectedColumns([]);
      setResult(null);
      return;
    }
    const measures = activeDataset.profile?.candidate_measures || [];
    const dimensions = activeDataset.profile?.candidate_dimensions || [];
    const dates = activeDataset.profile?.candidate_dates || [];
    const defaults = measures.length && (dimensions.length || dates.length)
      ? [measures[0], dimensions[0] || dates[0]]
      : measures.length ? [measures[0]] : columns.slice(0, 1).map((column) => column.name);
    setSelectedColumns(defaults.filter(Boolean).slice(0, 2));
    setResult(null);
    setError('');
    setDateColumn(dates[0] || '');
  }, [activeDataset?.id]);

  const runAnalysis = async (selection = selectedColumns) => {
    if (!activeDataset?.id || !selection.length) return;
    setLoading(true);
    setError('');
    try {
      const response = await AnalyticsService.automatic(activeDataset.id, selection, objective, dateColumn, dateFrom, dateTo);
      setResult(response);
      setChartType(response.chart?.type || '');
    } catch (requestError: any) {
      setResult(null);
      setError(requestError?.response?.data?.detail || 'Analysis could not be completed. Check the selected columns and try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!autoRun || !activeDataset?.id || !selectedColumns.length) return;
    const timer = window.setTimeout(() => { void runAnalysis(); }, 500);
    return () => window.clearTimeout(timer);
  }, [activeDataset?.id, selectedColumns.join('|'), objective, dateColumn, dateFrom, dateTo, autoRun]);

  const toggleColumn = (name: string) => {
    setSelectedColumns((current) => current.includes(name)
      ? current.filter((column) => column !== name)
      : [...current, name]);
  };

  const reset = () => {
    setSelectedColumns([]);
    setResult(null);
    setError('');
    setDateFrom('');
    setDateTo('');
    setObjective('auto');
  };

  const downloadChart = () => {
    const svg = chartContainer.current?.querySelector('svg');
    if (!svg || !result?.title) return;
    const copy = svg.cloneNode(true) as SVGSVGElement;
    copy.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    const blob = new Blob([new XMLSerializer().serializeToString(copy)], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `${result.title.replace(/[^\w-]+/g, '_')}.svg`;
    anchor.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
  };

  const downloadResults = () => {
    if (!result?.table?.rows?.length) return;
    const headers = result.table.columns;
    const escape = (value: any) => `"${String(value ?? '').replace(/"/g, '""')}"`;
    const csv = [headers.map(escape).join(','), ...result.table.rows.map((row) => headers.map((header) => escape(row[header])).join(','))].join('\r\n');
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `${(result.title || 'analysis').replace(/[^\w-]+/g, '_')}.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  if (!activeDataset) {
    return <div className="p-8 text-center text-zinc-500">Select or upload a dataset to begin automatic analysis.</div>;
  }

  const chart = result?.chart;
  const chartOptions = chart?.type === 'scatter' ? ['scatter'] : ['bar', 'line', 'area'];

  return (
    <div className="max-w-[1600px] mx-auto p-6 space-y-5">
      <section className="rounded-xl border border-[#23232a] bg-[#121216] p-5">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <BarChart3 size={18} className="text-red-400" />
              <h2 className="text-lg font-bold text-white">Automatic Column Intelligence</h2>
              <span className="rounded border border-emerald-500/20 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-400">No formulas needed</span>
            </div>
            <p className="mt-1 text-xs text-zinc-400">Select one or more compatible columns. DataPilot detects their types and selects a suitable analysis.</p>
          </div>
          <div className="flex items-center gap-2">
            <label htmlFor="analysis-dataset" className="text-[11px] text-zinc-400">Dataset</label>
            <select id="analysis-dataset" className={fieldClass} value={activeDataset.id} onChange={(event) => onSelectDataset(event.target.value)}>
              {datasets.map((dataset) => <option key={dataset.id} value={dataset.id}>{dataset.filename}</option>)}
            </select>
          </div>
        </div>

        <div className="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-[1fr_240px]">
          <div>
            <div className="mb-2 flex items-center justify-between">
              <label className="text-xs font-semibold text-zinc-200">Columns <span className="font-normal text-zinc-500">({selectedColumns.length} selected)</span></label>
              <span className="text-[10px] text-zinc-500">{activeDataset.row_count.toLocaleString()} rows · {columns.length} fields</span>
            </div>
            <div className="flex max-h-36 flex-wrap gap-2 overflow-auto rounded-lg border border-[#25252d] bg-[#0e0e12] p-3">
              {columns.map((column) => {
                const selected = selectedColumns.includes(column.name);
                return (
                  <button key={column.name} type="button" onClick={() => toggleColumn(column.name)}
                    aria-pressed={selected}
                    className={`rounded-lg border px-3 py-1.5 text-xs transition-colors ${selected ? 'border-red-500/50 bg-red-500/10 text-red-200' : 'border-[#2a2a33] bg-[#17171d] text-zinc-300 hover:border-zinc-500'}`}>
                    {column.name}<span className="ml-1.5 text-[10px] opacity-60">{column.inferred_type}</span>
                  </button>
                );
              })}
            </div>
          </div>
          <div className="space-y-3">
            <div>
              <label htmlFor="analysis-objective" className="mb-1.5 block text-xs font-semibold text-zinc-200">Analysis objective</label>
              <select id="analysis-objective" className={`${fieldClass} w-full`} value={objective} onChange={(event) => setObjective(event.target.value)}>
                <option value="auto">Auto detect</option>
                <option value="distribution">Distribution</option>
                <option value="compare">Compare columns</option>
                <option value="trend">Trend over time</option>
                <option value="segments">Compare groups</option>
              </select>
            </div>
            <label className="flex cursor-pointer items-center gap-2 text-xs text-zinc-300">
              <input type="checkbox" checked={autoRun} onChange={(event) => setAutoRun(event.target.checked)} className="accent-red-500" />
              Analyze automatically
            </label>
            <div className="flex gap-2">
              <button onClick={() => void runAnalysis()} disabled={loading || !selectedColumns.length}
                className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-red-600 px-3 py-2 text-xs font-semibold text-white hover:bg-red-500 disabled:opacity-50">
                <Sparkles size={14} />{loading ? 'Analyzing…' : 'Analyze'}
              </button>
              <button onClick={reset} className="rounded-lg border border-[#30303a] px-3 py-2 text-zinc-300 hover:bg-[#202027]" title="Reset analysis"><RotateCcw size={14} /></button>
            </div>
          </div>
        </div>

        {dateColumns.length > 0 && (
          <div className="mt-4 flex flex-wrap items-end gap-3 border-t border-[#24242b] pt-4">
            <div>
              <label htmlFor="analysis-date-column" className="mb-1 block text-[11px] text-zinc-400">Optional date filter</label>
              <select id="analysis-date-column" className={fieldClass} value={dateColumn} onChange={(event) => setDateColumn(event.target.value)}>
                <option value="">No date filter</option>
                {dateColumns.map((column) => <option key={column.name} value={column.name}>{column.name}</option>)}
              </select>
            </div>
            {dateColumn && <>
              <label className="text-[11px] text-zinc-400">From<input aria-label="Start date" type="date" className={`mt-1 block ${fieldClass}`} value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} /></label>
              <label className="text-[11px] text-zinc-400">To<input aria-label="End date" type="date" className={`mt-1 block ${fieldClass}`} value={dateTo} onChange={(event) => setDateTo(event.target.value)} /></label>
            </>}
          </div>
        )}
      </section>

      {error && <div role="alert" className="rounded-lg border border-red-500/30 bg-red-950/20 px-4 py-3 text-xs text-red-300">{error}</div>}
      {result && !result.supported && (
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 px-4 py-3 text-sm text-amber-200">{result.summary}</div>
      )}
      {result?.supported && (
        <>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-red-400">{result.analysis_type} · {result.row_count.toLocaleString()} rows analyzed</p>
              <h3 className="mt-1 text-xl font-bold text-white">{result.title}</h3>
              <p className="mt-1 text-xs text-zinc-400">{result.summary}</p>
            </div>
            <button onClick={downloadResults} className="flex items-center justify-center gap-2 rounded-lg border border-[#30303a] px-3 py-2 text-xs text-zinc-200 hover:bg-[#202027]">
              <Download size={14} /> Download results
            </button>
          </div>

          <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
            {(result.kpis || []).map((kpi) => (
              <div key={kpi.label} className="rounded-xl border border-[#25252d] bg-[#121216] p-4">
                <p className="text-[11px] text-zinc-500">{kpi.label}</p>
                <p className="mt-2 break-words text-lg font-bold text-white">{typeof kpi.value === 'number' ? kpi.value.toLocaleString(undefined, { maximumFractionDigits: 2 }) : kpi.value ?? '—'}</p>
              </div>
            ))}
          </div>

          {chart && (
            <section className="rounded-xl border border-[#23232a] bg-[#121216] p-5">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h4 className="text-sm font-bold text-white">{chart.title}</h4>
                  <p className="mt-1 text-[10px] text-zinc-500">{chart.x_label} · {chart.y_label}</p>
                </div>
                <div className="flex items-center gap-2">
                  {chartOptions.length > 1 && <select aria-label="Chart type" className={fieldClass} value={chartType} onChange={(event) => setChartType(event.target.value)}>
                    {chartOptions.map((option) => <option key={option} value={option}>{option[0].toUpperCase() + option.slice(1)} chart</option>)}
                  </select>}
                  <button onClick={downloadChart} className="flex items-center gap-1.5 rounded-lg border border-[#30303a] px-3 py-2 text-[11px] text-zinc-300 hover:bg-[#202027]">
                    <ImageDown size={13} /> Download chart
                  </button>
                </div>
              </div>
              <div ref={chartContainer}>
                <ChartRenderer type={chartType || chart.type} data={chart.data} xKey={chart.x_key} yKeys={chart.y_keys || [chart.y_key]} playKey={chart.play_key} height={310} />
              </div>
            </section>
          )}

          {(result.insights?.length || result.limitations?.length) ? (
            <section className="rounded-xl border border-[#23232a] bg-[#121216] p-4">
              <h4 className="mb-3 text-xs font-bold uppercase tracking-wider text-zinc-300">Automatic insights</h4>
              <ul className="space-y-2 text-xs text-zinc-300">
                {(result.insights || []).map((insight) => <li key={insight} className="flex gap-2"><span className="text-red-400">•</span>{insight}</li>)}
                {(result.limitations || []).map((limitation) => <li key={limitation} className="flex gap-2 text-amber-300"><span>!</span>{limitation}</li>)}
              </ul>
            </section>
          ) : null}

          {result.table?.rows?.length ? (
            <section className="overflow-hidden rounded-xl border border-[#23232a] bg-[#121216]">
              <div className="border-b border-[#24242b] px-4 py-3"><h4 className="text-xs font-bold text-white">Results table</h4></div>
              <div className="max-h-96 overflow-auto">
                <table className="w-full text-left text-xs">
                  <thead className="sticky top-0 bg-[#18181f] text-zinc-400"><tr>{result.table.columns.map((column) => <th key={column} className="whitespace-nowrap px-4 py-3 font-semibold">{column}</th>)}</tr></thead>
                  <tbody>{result.table.rows.map((row, index) => <tr key={index} className="border-t border-[#23232a] text-zinc-300">{result.table!.columns.map((column) => <td key={column} className="whitespace-nowrap px-4 py-2.5">{typeof row[column] === 'number' ? row[column].toLocaleString(undefined, { maximumFractionDigits: 2 }) : String(row[column] ?? '—')}</td>)}</tr>)}</tbody>
                </table>
              </div>
            </section>
          ) : null}
        </>
      )}
      {!result && !error && !loading && <div className="rounded-xl border border-dashed border-[#30303a] p-10 text-center text-xs text-zinc-500">Select one or more columns to view automatic analysis results.</div>}
    </div>
  );
};
