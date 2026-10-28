import React, { useState, useEffect } from 'react';
import { 
  Wand2, 
  Trash2, 
  RotateCcw, 
  RotateCw, 
  AlertTriangle, 
  CheckCircle2, 
  Sliders, 
  Calendar, 
  Type, 
  Layers, 
  ArrowRight,
  RefreshCw,
  FileSpreadsheet
} from 'lucide-react';
import { DatasetMeta } from '../../types';
import { CleaningService, DatasetService } from '../../services/api';

interface CleaningStudioProps {
  activeDataset?: DatasetMeta;
  onDatasetUpdated: (dataset: DatasetMeta) => void;
}

export const CleaningStudio: React.FC<CleaningStudioProps> = ({
  activeDataset,
  onDatasetUpdated
}) => {
  const [duplicatePreview, setDuplicatePreview] = useState<any>(null);
  const [imputeColumn, setImputeColumn] = useState<string>('');
  const [imputeStrategy, setImputeStrategy] = useState<string>('mean');
  const [imputePreview, setImputePreview] = useState<any>(null);
  
  const [outlierColumn, setOutlierColumn] = useState<string>('');
  const [outlierMethod, setOutlierMethod] = useState<string>('iqr');
  const [outlierThreshold, setOutlierThreshold] = useState<number>(1.5);
  const [outlierAction, setOutlierAction] = useState<string>('cap');
  const [outlierPreview, setOutlierPreview] = useState<any>(null);

  const [dateColumn, setDateColumn] = useState<string>('');
  const [textColumn, setTextColumn] = useState<string>('');
  const [textOperation, setTextOperation] = useState<string>('trim');

  const [auditLog, setAuditLog] = useState<any[]>([]);
  const [qualityReport, setQualityReport] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  useEffect(() => {
    if (activeDataset?.id) {
      loadHistory();
      loadQualityReport();
      // Auto-preview duplicates
      fetchDuplicatePreview();
    }
  }, [activeDataset?.id]);

  const loadHistory = async () => {
    if (!activeDataset?.id) return;
    try {
      const res = await CleaningService.getHistory(activeDataset.id);
      setAuditLog(res.history || []);
    } catch (e) {
      console.error(e);
    }
  };

  const loadQualityReport = async () => {
    if (!activeDataset?.id) return;
    try {
      setQualityReport(await CleaningService.quality(activeDataset.id));
    } catch (e) {
      console.error("Failed to load data quality report:", e);
    }
  };

  const fetchDuplicatePreview = async () => {
    if (!activeDataset?.id) return;
    try {
      const res = await CleaningService.previewDuplicates(activeDataset.id);
      setDuplicatePreview(res);
    } catch (e) {
      console.error(e);
    }
  };

  const handleApplyDuplicates = async () => {
    if (!activeDataset?.id) return;
    setLoading(true);
    try {
      const res = await CleaningService.applyDuplicates(activeDataset.id);
      onDatasetUpdated(res.dataset);
      setStatusMessage(`Removed ${res.summary.removed_rows} duplicate rows successfully.`);
      fetchDuplicatePreview();
      loadHistory();
      loadQualityReport();
    } catch (e: any) {
      setStatusMessage(`Failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handlePreviewImpute = async () => {
    if (!activeDataset?.id || !imputeColumn) return;
    try {
      const res = await CleaningService.previewImpute(imputeColumn, imputeStrategy, undefined, activeDataset.id);
      setImputePreview(res);
    } catch (e) {
      console.error(e);
    }
  };

  const handleApplyImpute = async () => {
    if (!activeDataset?.id || !imputeColumn) return;
    setLoading(true);
    try {
      const res = await CleaningService.applyImpute(imputeColumn, imputeStrategy, undefined, activeDataset.id);
      onDatasetUpdated(res.dataset);
      setStatusMessage(res.summary.action);
      setImputePreview(null);
      loadHistory();
      loadQualityReport();
    } catch (e: any) {
      setStatusMessage(`Failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handlePreviewOutliers = async () => {
    if (!activeDataset?.id || !outlierColumn) return;
    try {
      const res = await CleaningService.previewOutliers(outlierColumn, outlierMethod, outlierThreshold, activeDataset.id);
      setOutlierPreview(res);
    } catch (e) {
      console.error(e);
    }
  };

  const handleApplyOutliers = async () => {
    if (!activeDataset?.id || !outlierColumn) return;
    setLoading(true);
    try {
      const res = await CleaningService.applyOutliers(outlierColumn, outlierAction, outlierMethod, outlierThreshold, activeDataset.id);
      onDatasetUpdated(res.dataset);
      setStatusMessage(res.summary.action);
      setOutlierPreview(null);
      loadHistory();
      loadQualityReport();
    } catch (e: any) {
      setStatusMessage(`Failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleStandardizeDates = async () => {
    if (!activeDataset?.id || !dateColumn) return;
    setLoading(true);
    try {
      const res = await CleaningService.standardizeDates(dateColumn, activeDataset.id);
      onDatasetUpdated(res.dataset);
      setStatusMessage(res.summary.action);
      loadHistory();
      loadQualityReport();
    } catch (e: any) {
      setStatusMessage(`Failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleNormalizeText = async () => {
    if (!activeDataset?.id || !textColumn) return;
    setLoading(true);
    try {
      const res = await CleaningService.normalizeText(textColumn, textOperation, activeDataset.id);
      onDatasetUpdated(res.dataset);
      setStatusMessage(res.summary.action);
      loadHistory();
      loadQualityReport();
    } catch (e: any) {
      setStatusMessage(`Failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleUndo = async () => {
    if (!activeDataset?.id) return;
    try {
      const res = await CleaningService.undo(activeDataset.id);
      onDatasetUpdated(res.dataset);
      setStatusMessage("Undone previous action");
      loadHistory();
      loadQualityReport();
    } catch (e: any) {
      setStatusMessage(e?.response?.data?.detail || "Undo failed");
    }
  };

  const handleRedo = async () => {
    if (!activeDataset?.id) return;
    try {
      const res = await CleaningService.redo(activeDataset.id);
      onDatasetUpdated(res.dataset);
      setStatusMessage("Redone action");
      loadHistory();
      loadQualityReport();
    } catch (e: any) {
      setStatusMessage(e?.response?.data?.detail || "Redo failed");
    }
  };

  const handleResetToOriginal = async () => {
    if (!activeDataset?.id || !window.confirm('Reset this working dataset to its original uploaded version? This cannot be undone.')) return;
    setLoading(true);
    try {
      const res = await CleaningService.reset(activeDataset.id);
      onDatasetUpdated(res.dataset);
      setStatusMessage('Working dataset restored from the unchanged original.');
      await Promise.all([loadHistory(), loadQualityReport(), fetchDuplicatePreview()]);
    } catch (e: any) {
      setStatusMessage(`Failed to restore original: ${e?.response?.data?.detail || e.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (!activeDataset) {
    return <div className="p-8 text-center text-zinc-500">Please select a dataset to use Data Cleaning Studio.</div>;
  }

  const columns = activeDataset.profile?.columns || [];
  const numericCols = columns.filter((c) => c.role === 'measure' || c.inferred_type === 'numeric');
  const stringCols = columns.filter((c) => c.inferred_type === 'string' || c.inferred_type === 'categorical');
  const dateCols = columns.filter((c) => c.role === 'date' || c.inferred_type === 'date');

  return (
    <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
      {/* Top Header & Reversible Undo/Redo Toolbar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#121216] border border-[#23232a] p-4 rounded-xl">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-lg font-bold text-white tracking-tight">Data Cleaning Studio</h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/10 text-red-400 border border-red-500/20">
              Reversible Pipeline
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-1">
            Review quality issues and preview reversible cleaning actions. The original upload remains unchanged.
          </p>
        </div>

        {/* Undo / Redo Toolbar */}
        <div className="flex items-center space-x-2">
          <button
            onClick={handleResetToOriginal}
            disabled={loading || !qualityReport?.modified}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-[#1c1c23] text-zinc-300 border border-[#2b2b36] hover:bg-[#25252f] disabled:opacity-40"
            title="Restore the working version from the original upload"
          >
            <RefreshCw size={13} /><span>Reset to original</span>
          </button>
          <button
            onClick={handleUndo}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-[#1c1c23] text-zinc-300 border border-[#2b2b36] hover:bg-[#25252f] transition-all"
            title="Undo last transformation"
          >
            <RotateCcw size={13} />
            <span>Undo</span>
          </button>
          <button
            onClick={handleRedo}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-[#1c1c23] text-zinc-300 border border-[#2b2b36] hover:bg-[#25252f] transition-all"
            title="Redo transformation"
          >
            <RotateCw size={13} />
            <span>Redo</span>
          </button>
        </div>
      </div>

      {statusMessage && (
        <div className="p-3 bg-[#181822] border border-red-500/30 rounded-xl text-xs text-zinc-200 flex items-center justify-between">
          <span className="flex items-center space-x-2">
            <CheckCircle2 size={14} className="text-emerald-400" />
            <span>{statusMessage}</span>
          </span>
          <button onClick={() => setStatusMessage(null)} className="text-zinc-500 hover:text-white">✕</button>
        </div>
      )}

      {qualityReport && (
        <section className="rounded-xl border border-[#23232a] bg-[#121216] p-5 space-y-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h3 className="text-sm font-bold text-white">Data quality overview</h3>
              <p className="mt-1 text-[11px] text-zinc-500">
                Original: {qualityReport.original.rows.toLocaleString()} rows · Current working copy: {qualityReport.current.rows.toLocaleString()} rows
                {qualityReport.modified ? ' · Changes applied' : ' · No changes applied'}
              </p>
            </div>
            <div className="flex gap-2 text-[10px]">
              <span className="rounded bg-red-500/10 px-2 py-1 text-red-300">{qualityReport.duplicate_rows.toLocaleString()} duplicate rows</span>
              <span className="rounded bg-amber-500/10 px-2 py-1 text-amber-300">{qualityReport.empty_rows.toLocaleString()} empty rows</span>
              <span className="rounded bg-zinc-800 px-2 py-1 text-zinc-300">{qualityReport.empty_columns.length} empty columns</span>
            </div>
          </div>
          <div className="max-h-72 overflow-auto rounded-lg border border-[#24242b]">
            <table className="w-full text-left text-[11px]">
              <thead className="sticky top-0 bg-[#18181f] text-zinc-400"><tr>
                <th className="px-3 py-2">Column</th><th className="px-3 py-2">Missing</th><th className="px-3 py-2">Distinct</th><th className="px-3 py-2">Quality signals</th>
              </tr></thead>
              <tbody>{qualityReport.checks.map((check: any) => {
                const signals = [
                  check.whitespace_count ? `${check.whitespace_count} whitespace` : '',
                  check.numeric_parse_failures ? `${check.numeric_parse_failures} invalid numbers` : '',
                  check.formatted_numeric_values ? `${check.formatted_numeric_values} formatted numbers` : '',
                  check.invalid_dates ? `${check.invalid_dates} invalid dates` : '',
                  check.infinite_count ? `${check.infinite_count} infinite` : '',
                  check.negative_count ? `${check.negative_count} negative` : '',
                  check.outlier_count ? `${check.outlier_count} unusual` : '',
                  check.constant ? 'constant' : '',
                  check.high_cardinality ? 'high cardinality' : '',
                  check.potentially_sensitive ? 'potentially sensitive' : '',
                  check.category_variations.length ? 'label variations' : ''
                ].filter(Boolean);
                return <tr key={check.column} className="border-t border-[#24242b] text-zinc-300">
                  <td className="px-3 py-2 font-medium text-white">{check.column}</td>
                  <td className="px-3 py-2">{check.missing_count.toLocaleString()} <span className="text-zinc-500">({check.missing_percentage}%)</span></td>
                  <td className="px-3 py-2">{check.distinct_count.toLocaleString()}</td>
                  <td className="px-3 py-2">{signals.length ? <span className="text-amber-300">{signals.join(' · ')}</span> : <span className="text-emerald-400">No flagged checks</span>}</td>
                </tr>;
              })}</tbody>
            </table>
          </div>
          {qualityReport.business_key_duplicates.length > 0 && (
            <p className="text-[11px] text-amber-300">
              Candidate-key duplicates: {qualityReport.business_key_duplicates.map((item: any) => `${item.columns.join(', ')} (${item.duplicate_rows})`).join(' · ')}
            </p>
          )}
        </section>
      )}

      {/* Grid of Cleaning Workbenches */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* 1. Duplicate Records Card */}
        <div className="bg-[#121216] border border-[#23232a] rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-[#22222a] pb-3">
            <div className="flex items-center space-x-2">
              <Trash2 size={16} className="text-red-400" />
              <h3 className="text-sm font-bold text-white">Deduplication Studio</h3>
            </div>
            {duplicatePreview && (
              <span className={`text-[11px] font-bold px-2 py-0.5 rounded ${
                duplicatePreview.affected_rows > 0 ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'
              }`}>
                {duplicatePreview.affected_rows} duplicates detected
              </span>
            )}
          </div>

          <p className="text-xs text-zinc-400">
            Identifies exact duplicate records across all columns. Requires confirmation before permanently removing duplicate rows.
          </p>

          {duplicatePreview && (
            <div className="bg-[#18181f] p-3 rounded-lg border border-[#272733] text-xs space-y-1 font-mono">
              <div className="text-zinc-300">Total Rows: {duplicatePreview.before_rows?.toLocaleString()}</div>
              <div className="text-red-400">Redundant Rows: {duplicatePreview.affected_rows} ({duplicatePreview.percentage_affected}%)</div>
              <div className="text-emerald-400">Target Clean Rows: {duplicatePreview.after_rows?.toLocaleString()}</div>
            </div>
          )}

          <button
            onClick={handleApplyDuplicates}
            disabled={!duplicatePreview || duplicatePreview.affected_rows === 0 || loading}
            className="w-full py-2 px-3 rounded-lg text-xs font-semibold bg-red-600 hover:bg-red-500 disabled:opacity-40 disabled:hover:bg-red-600 text-white shadow-md shadow-red-500/20 transition-all flex items-center justify-center space-x-2"
          >
            <span>Confirm & Remove {duplicatePreview?.affected_rows || 0} Duplicates</span>
          </button>
        </div>

        {/* 2. Missing Value Imputation Card */}
        <div className="bg-[#121216] border border-[#23232a] rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-[#22222a] pb-3">
            <div className="flex items-center space-x-2">
              <Sliders size={16} className="text-amber-400" />
              <h3 className="text-sm font-bold text-white">Missing Value Imputation</h3>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[11px] font-semibold text-zinc-400 mb-1 block">Column:</label>
              <select
                value={imputeColumn}
                onChange={(e) => { setImputeColumn(e.target.value); setImputePreview(null); }}
                className="w-full bg-[#18181f] text-white border border-[#272733] rounded px-2.5 py-1.5 text-xs focus:outline-none focus:border-red-500"
              >
                <option value="">Select column...</option>
                {columns.map((c) => (
                  <option key={c.name} value={c.name}>
                    {c.name} ({c.missing_count} nulls)
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-[11px] font-semibold text-zinc-400 mb-1 block">Strategy:</label>
              <select
                value={imputeStrategy}
                onChange={(e) => setImputeStrategy(e.target.value)}
                className="w-full bg-[#18181f] text-white border border-[#272733] rounded px-2.5 py-1.5 text-xs focus:outline-none focus:border-red-500"
              >
                <option value="mean">Mean (Arithmetic Average)</option>
                <option value="median">Median (Outlier Robust)</option>
                <option value="mode">Mode (Most Frequent)</option>
                <option value="forward_fill">Forward Fill (Last Known)</option>
                <option value="drop">Drop Rows with Nulls</option>
              </select>
            </div>
          </div>

          {imputePreview && (
            <div className="bg-[#18181f] p-3 rounded-lg border border-[#272733] text-xs font-mono text-zinc-300">
              <div>Missing in {imputePreview.column}: {imputePreview.missing_rows} rows ({imputePreview.missing_percentage}%)</div>
              <div className="text-emerald-400">Fill Value: {String(imputePreview.replacement_value)}</div>
            </div>
          )}

          <div className="flex items-center space-x-2">
            <button
              onClick={handlePreviewImpute}
              disabled={!imputeColumn}
              className="flex-1 py-1.5 px-3 rounded-lg text-xs font-medium bg-[#1c1c24] text-zinc-300 border border-[#2b2b36] hover:bg-[#252530]"
            >
              Preview Impact
            </button>
            <button
              onClick={handleApplyImpute}
              disabled={!imputeColumn || loading}
              className="flex-1 py-1.5 px-3 rounded-lg text-xs font-semibold bg-red-600 hover:bg-red-500 text-white disabled:opacity-40"
            >
              Apply Imputation
            </button>
          </div>
        </div>

        {/* 3. Outlier Capping & Detection */}
        <div className="bg-[#121216] border border-[#23232a] rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-[#22222a] pb-3">
            <div className="flex items-center space-x-2">
              <AlertTriangle size={16} className="text-orange-400" />
              <h3 className="text-sm font-bold text-white">Outlier Detection & Capping</h3>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2.5">
            <div>
              <label className="text-[11px] font-semibold text-zinc-400 mb-1 block">Numeric Col:</label>
              <select
                value={outlierColumn}
                onChange={(e) => { setOutlierColumn(e.target.value); setOutlierPreview(null); }}
                className="w-full bg-[#18181f] text-white border border-[#272733] rounded px-2 py-1.5 text-xs focus:outline-none focus:border-red-500"
              >
                <option value="">Select column...</option>
                {numericCols.map((c) => (
                  <option key={c.name} value={c.name}>{c.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-[11px] font-semibold text-zinc-400 mb-1 block">Method:</label>
              <select
                value={outlierMethod}
                onChange={(e) => setOutlierMethod(e.target.value)}
                className="w-full bg-[#18181f] text-white border border-[#272733] rounded px-2 py-1.5 text-xs focus:outline-none focus:border-red-500"
              >
                <option value="iqr">IQR (1.5x Interquartile)</option>
                <option value="zscore">Z-Score (3 Sigma)</option>
              </select>
            </div>

            <div>
              <label className="text-[11px] font-semibold text-zinc-400 mb-1 block">Action:</label>
              <select
                value={outlierAction}
                onChange={(e) => setOutlierAction(e.target.value)}
                className="w-full bg-[#18181f] text-white border border-[#272733] rounded px-2 py-1.5 text-xs focus:outline-none focus:border-red-500"
              >
                <option value="cap">Cap / Winsorize</option>
                <option value="drop">Drop Outlier Rows</option>
                <option value="flag">Flag as New Column</option>
              </select>
            </div>
          </div>

          {outlierPreview && (
            <div className="bg-[#18181f] p-3 rounded-lg border border-[#272733] text-xs font-mono space-y-1">
              <div className="text-zinc-300">Outliers Found: {outlierPreview.outlier_count} ({outlierPreview.outlier_percentage}%)</div>
              <div className="text-zinc-400">Valid Bounds: [{outlierPreview.lower_bound}, {outlierPreview.upper_bound}]</div>
            </div>
          )}

          <div className="flex items-center space-x-2">
            <button
              onClick={handlePreviewOutliers}
              disabled={!outlierColumn}
              className="flex-1 py-1.5 px-3 rounded-lg text-xs font-medium bg-[#1c1c24] text-zinc-300 border border-[#2b2b36] hover:bg-[#252530]"
            >
              Scan Outliers
            </button>
            <button
              onClick={handleApplyOutliers}
              disabled={!outlierColumn || loading}
              className="flex-1 py-1.5 px-3 rounded-lg text-xs font-semibold bg-red-600 hover:bg-red-500 text-white disabled:opacity-40"
            >
              Apply Outlier Action
            </button>
          </div>
        </div>

        {/* 4. Text & Date Standardization */}
        <div className="bg-[#121216] border border-[#23232a] rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-[#22222a] pb-3">
            <div className="flex items-center space-x-2">
              <Calendar size={16} className="text-blue-400" />
              <h3 className="text-sm font-bold text-white">Date & Text Standardization</h3>
            </div>
          </div>

          {/* Date standardizer */}
          <div className="space-y-2">
            <label className="text-[11px] font-semibold text-zinc-400 block">Standardize Date Column to ISO (YYYY-MM-DD):</label>
            <div className="flex items-center space-x-2">
              <select
                value={dateColumn}
                onChange={(e) => setDateColumn(e.target.value)}
                className="flex-1 bg-[#18181f] text-white border border-[#272733] rounded px-2.5 py-1.5 text-xs focus:outline-none focus:border-red-500"
              >
                <option value="">Select date column...</option>
                {columns.map((c) => (
                  <option key={c.name} value={c.name}>{c.name} ({c.inferred_type})</option>
                ))}
              </select>
              <button
                onClick={handleStandardizeDates}
                disabled={!dateColumn || loading}
                className="py-1.5 px-3 rounded-lg text-xs font-semibold bg-[#22222c] hover:bg-[#2d2d3a] text-white border border-[#333342] disabled:opacity-40"
              >
                Standardize
              </button>
            </div>
          </div>

          {/* Text normalization */}
          <div className="space-y-2 border-t border-[#22222a] pt-3">
            <label className="text-[11px] font-semibold text-zinc-400 block">Text Cleaning & Whitespace Normalization:</label>
            <div className="grid grid-cols-2 gap-2">
              <select
                value={textColumn}
                onChange={(e) => setTextColumn(e.target.value)}
                className="bg-[#18181f] text-white border border-[#272733] rounded px-2.5 py-1.5 text-xs focus:outline-none focus:border-red-500"
              >
                <option value="">Select text column...</option>
                {stringCols.map((c) => (
                  <option key={c.name} value={c.name}>{c.name}</option>
                ))}
              </select>
              <select
                value={textOperation}
                onChange={(e) => setTextOperation(e.target.value)}
                className="bg-[#18181f] text-white border border-[#272733] rounded px-2.5 py-1.5 text-xs focus:outline-none focus:border-red-500"
              >
                <option value="trim">Trim Extra Whitespace</option>
                <option value="titlecase">Title Case (Word Capitalize)</option>
                <option value="uppercase">Uppercase</option>
                <option value="lowercase">Lowercase</option>
              </select>
            </div>
            <button
              onClick={handleNormalizeText}
              disabled={!textColumn || loading}
              className="w-full py-1.5 px-3 rounded-lg text-xs font-semibold bg-[#22222c] hover:bg-[#2d2d3a] text-white border border-[#333342] disabled:opacity-40"
            >
              Normalize Text Column
            </button>
          </div>
        </div>
      </div>

      {/* Reversible Transformation Audit Log */}
      <div className="bg-[#121216] border border-[#23232a] rounded-xl p-5">
        <h3 className="text-sm font-bold text-white mb-3">Reversible Transformation History & Audit Trail</h3>
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {auditLog.map((step) => (
            <div
              key={step.index}
              className={`p-2.5 rounded-lg border text-xs flex items-center justify-between font-mono ${
                step.is_current ? 'bg-red-950/20 border-red-500/40 text-white' : 'bg-[#16161b] border-[#25252e] text-zinc-400'
              }`}
            >
              <div className="flex items-center space-x-2">
                <span className="w-5 text-center font-bold">{step.index + 1}</span>
                <span>{step.action}</span>
                {step.is_current && (
                  <span className="px-1.5 py-0.5 rounded text-[9px] bg-red-600 text-white font-sans font-bold">CURRENT</span>
                )}
              </div>
              <div>{step.row_count?.toLocaleString()} rows • {step.column_count} cols</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
