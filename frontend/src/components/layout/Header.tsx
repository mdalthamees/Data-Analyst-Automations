import React from 'react';
import { 
  Database, 
  Sparkles, 
  Upload, 
  FileSpreadsheet, 
  Download, 
  Layers, 
  CheckCircle2,
  RefreshCw
} from 'lucide-react';
import { DatasetMeta } from '../../types';

interface HeaderProps {
  datasets: DatasetMeta[];
  activeDataset?: DatasetMeta;
  onSelectDataset: (id: string) => void;
  onOpenUploadModal: () => void;
  onQuickSample: (type: string) => void;
  onNewChat: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  datasets,
  activeDataset,
  onSelectDataset,
  onOpenUploadModal,
  onQuickSample,
  onNewChat
}) => {
  return (
    <header className="h-16 bg-[#0e0e11] border-b border-[#222227] px-6 flex items-center justify-between z-20">
      {/* Left: Active Dataset Selector & Metadata */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <Database size={16} className="text-zinc-400" />
          <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Dataset:</span>
          <select
            value={activeDataset?.id || ''}
            onChange={(e) => onSelectDataset(e.target.value)}
            className="bg-[#18181d] text-white text-xs font-medium rounded-md px-3 py-1.5 border border-[#2a2a33] focus:outline-none focus:border-red-500 max-w-xs truncate cursor-pointer"
          >
            {datasets.map((ds) => (
              <option key={ds.id} value={ds.id}>
                {ds.filename} ({ds.row_count.toLocaleString()} rows)
              </option>
            ))}
          </select>
        </div>

        {activeDataset && (
          <div className="hidden lg:flex items-center space-x-3 text-xs border-l border-[#26262e] pl-4">
            <span className="px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 font-mono text-[11px]">
              {activeDataset.format}
            </span>
            <span className="text-zinc-400">
              <strong className="text-zinc-200">{activeDataset.row_count.toLocaleString()}</strong> rows
            </span>
            <span className="text-zinc-400">
              <strong className="text-zinc-200">{activeDataset.column_count}</strong> cols
            </span>
            {activeDataset.selected_sheet && (
              <span className="px-2 py-0.5 rounded bg-red-950/40 text-red-400 border border-red-900/40 text-[11px]">
                Sheet: {activeDataset.selected_sheet}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Right: Quick Actions */}
      <div className="flex items-center space-x-2.5">
        <button
          onClick={onNewChat}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 transition-all"
        >
          <Sparkles size={14} />
          <span>Ask Analyst</span>
        </button>

        <button
          onClick={onOpenUploadModal}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-[#1c1c22] text-zinc-200 border border-[#2b2b35] hover:bg-[#25252e] transition-all"
        >
          <Upload size={14} />
          <span>Upload File</span>
        </button>

        <div className="relative group">
          <button className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-[#1c1c22] text-zinc-300 border border-[#2b2b35] hover:bg-[#25252e] transition-all">
            <Layers size={14} />
            <span>Load Sample</span>
          </button>
          <div className="absolute right-0 mt-1 w-56 bg-[#16161b] border border-[#2b2b36] rounded-lg shadow-xl py-1.5 hidden group-hover:block z-50">
            <button
              onClick={() => onQuickSample('retail_sales')}
              className="w-full text-left px-3 py-2 text-xs text-zinc-200 hover:bg-[#22222a] flex items-center justify-between"
            >
              <span>Retail Sales (5,000 rows)</span>
              <span className="text-[10px] text-zinc-500 font-mono">CSV</span>
            </button>
            <button
              onClick={() => onQuickSample('100k_benchmark')}
              className="w-full text-left px-3 py-2 text-xs text-zinc-200 hover:bg-[#22222a] flex items-center justify-between"
            >
              <span>100K Benchmark Dataset</span>
              <span className="text-[10px] text-red-400 font-mono font-bold">100K</span>
            </button>
            <button
              onClick={() => onQuickSample('financial_multisheet')}
              className="w-full text-left px-3 py-2 text-xs text-zinc-200 hover:bg-[#22222a] flex items-center justify-between"
            >
              <span>Multi-Sheet Financial Model</span>
              <span className="text-[10px] text-emerald-400 font-mono">XLSX</span>
            </button>
            <button
              onClick={() => onQuickSample('hr_attrition')}
              className="w-full text-left px-3 py-2 text-xs text-zinc-200 hover:bg-[#22222a] flex items-center justify-between"
            >
              <span>HR Workforce & Attrition</span>
              <span className="text-[10px] text-zinc-500 font-mono">CSV</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
