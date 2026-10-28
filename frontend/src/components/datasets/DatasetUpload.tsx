import React, { useState } from 'react';
import { 
  Upload, 
  FileSpreadsheet, 
  Database, 
  CheckCircle2, 
  X, 
  AlertCircle, 
  Layers, 
  Zap,
  ArrowRight
} from 'lucide-react';
import { DatasetMeta } from '../../types';
import { DatasetService } from '../../services/api';

interface DatasetUploadProps {
  isOpen: boolean;
  onClose: () => void;
  onDatasetUploaded: (dataset: DatasetMeta) => void;
}

export const DatasetUpload: React.FC<DatasetUploadProps> = ({
  isOpen,
  onClose,
  onDatasetUploaded
}) => {
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];
    setUploading(true);
    setError(null);

    try {
      const res = await DatasetService.upload(file);
      onDatasetUploaded(res);
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleQuickSample = async (type: string, count: number) => {
    setUploading(true);
    setError(null);
    try {
      const res = await DatasetService.generateSample(type, count);
      onDatasetUploaded(res);
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || "Failed to generate sample");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
      <div className="bg-[#121216] border border-[#26262f] rounded-2xl max-w-xl w-full p-6 shadow-2xl space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#23232a] pb-4">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-red-600/20 text-red-400 border border-red-500/30 flex items-center justify-center">
              <Upload size={17} />
            </div>
            <div>
              <h3 className="text-base font-bold text-white tracking-tight">Upload Dataset</h3>
              <p className="text-xs text-zinc-400">CSV, Excel (XLSX, XLS), Parquet, JSON</p>
            </div>
          </div>
          <button onClick={onClose} className="text-zinc-500 hover:text-white">
            <X size={18} />
          </button>
        </div>

        {error && (
          <div className="p-3 bg-red-950/30 border border-red-500/40 rounded-xl text-xs text-red-300 flex items-center space-x-2">
            <AlertCircle size={15} />
            <span>{error}</span>
          </div>
        )}

        {/* Drag and Drop Box */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
          onDragLeave={() => setDragActive(false)}
          onDrop={(e) => { e.preventDefault(); setDragActive(false); handleFiles(e.dataTransfer.files); }}
          className={`border-2 border-dashed rounded-xl p-8 text-center transition-all ${
            dragActive
              ? 'border-red-500 bg-red-500/5'
              : 'border-[#2c2c36] hover:border-zinc-500 bg-[#0e0e11]'
          }`}
        >
          <div className="w-12 h-12 mx-auto rounded-full bg-zinc-800 text-zinc-400 flex items-center justify-center mb-3">
            <Upload size={22} className={uploading ? "animate-bounce text-red-400" : ""} />
          </div>
          <p className="text-sm font-semibold text-zinc-200 mb-1">
            {uploading ? "Profiling schema & loading into DuckDB..." : "Drag and drop your dataset here"}
          </p>
          <p className="text-xs text-zinc-500 mb-4">
            Supports multi-sheet Excel, 100,000+ rows CSV, Parquet columnar files
          </p>

          <label className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-semibold bg-red-600 hover:bg-red-500 text-white cursor-pointer shadow-md shadow-red-500/20 transition-all">
            <span>Browse Files</span>
            <input
              type="file"
              accept=".csv,.xlsx,.xls,.parquet,.json"
              className="hidden"
              onChange={(e) => handleFiles(e.target.files)}
              disabled={uploading}
            />
          </label>
        </div>

        {/* Or Quick Sample Datasets */}
        <div className="border-t border-[#23232a] pt-4">
          <div className="text-xs font-semibold text-zinc-400 mb-2.5 flex items-center space-x-1.5">
            <Layers size={13} className="text-red-400" />
            <span>Or Instant Demo Datasets:</span>
          </div>

          <div className="grid grid-cols-2 gap-2.5">
            <button
              onClick={() => handleQuickSample('retail_sales', 5000)}
              disabled={uploading}
              className="p-3 text-left rounded-xl bg-[#18181f] border border-[#2a2a34] hover:border-red-500/40 hover:bg-[#202029] transition-all"
            >
              <div className="text-xs font-semibold text-white">Global Retail Sales</div>
              <div className="text-[11px] text-zinc-400 mt-0.5">5,000 rows • Sales, Profit, Regions</div>
            </button>

            <button
              onClick={() => handleQuickSample('100k_benchmark', 100000)}
              disabled={uploading}
              className="p-3 text-left rounded-xl bg-[#18181f] border border-[#2a2a34] hover:border-red-500/40 hover:bg-[#202029] transition-all"
            >
              <div className="text-xs font-semibold text-white flex items-center justify-between">
                <span>100K Benchmark</span>
                <span className="text-[9px] px-1 rounded bg-red-500/20 text-red-400 font-bold">100,000</span>
              </div>
              <div className="text-[11px] text-zinc-400 mt-0.5">High volume columnar testing</div>
            </button>

            <button
              onClick={() => handleQuickSample('financial_multisheet', 12)}
              disabled={uploading}
              className="p-3 text-left rounded-xl bg-[#18181f] border border-[#2a2a34] hover:border-red-500/40 hover:bg-[#202029] transition-all"
            >
              <div className="text-xs font-semibold text-white">Financial Multi-Sheet</div>
              <div className="text-[11px] text-zinc-400 mt-0.5">Revenue & Opex sheets in Excel</div>
            </button>

            <button
              onClick={() => handleQuickSample('hr_attrition', 1200)}
              disabled={uploading}
              className="p-3 text-left rounded-xl bg-[#18181f] border border-[#2a2a34] hover:border-red-500/40 hover:bg-[#202029] transition-all"
            >
              <div className="text-xs font-semibold text-white">HR Workforce & Attrition</div>
              <div className="text-[11px] text-zinc-400 mt-0.5">1,200 employees, salaries, ratings</div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
