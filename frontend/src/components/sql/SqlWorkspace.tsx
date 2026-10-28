import React, { useState, useEffect } from 'react';
import { 
  Terminal, 
  Play, 
  FileText, 
  Clock, 
  Database, 
  ChevronRight, 
  Download, 
  CheckCircle2, 
  AlertCircle,
  Copy,
  Table
} from 'lucide-react';
import { DatasetMeta } from '../../types';
import { SQLService } from '../../services/api';

interface SqlWorkspaceProps {
  activeDataset?: DatasetMeta;
}

export const SqlWorkspace: React.FC<SqlWorkspaceProps> = ({
  activeDataset
}) => {
  const [query, setQuery] = useState<string>('');
  const [result, setResult] = useState<any>(null);
  const [plan, setPlan] = useState<string | null>(null);
  const [tables, setTables] = useState<string[]>([]);
  const [selectedTableSchema, setSelectedTableSchema] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    loadTables();
    if (activeDataset?.table_name) {
      setQuery(`SELECT Category, ROUND(SUM(Sales), 2) AS total_sales, ROUND(SUM(Profit), 2) AS total_profit\nFROM ${activeDataset.table_name}\nGROUP BY Category\nORDER BY total_sales DESC;`);
      loadSchema(activeDataset.table_name);
    }
  }, [activeDataset?.table_name]);

  const loadTables = async () => {
    try {
      const res = await SQLService.tables();
      setTables(res.tables || []);
    } catch (e) {
      console.error(e);
    }
  };

  const loadSchema = async (tbl: string) => {
    try {
      const res = await SQLService.schema(tbl);
      setSelectedTableSchema(res.schema || []);
    } catch (e) {
      console.error(e);
    }
  };

  const handleRunQuery = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setPlan(null);
    try {
      const res = await SQLService.execute(query);
      setResult(res);
    } catch (e: any) {
      setResult({ success: false, error: e.message });
    } finally {
      setLoading(false);
    }
  };

  const handleExplain = async () => {
    if (!query.trim()) return;
    try {
      const res = await SQLService.explain(query);
      setPlan(res.plan);
    } catch (e: any) {
      setPlan(`Error: ${e.message}`);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
      {/* Top Banner */}
      <div className="bg-[#121216] border border-[#23232a] p-4 rounded-xl flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2">
            <Terminal size={18} className="text-red-400" />
            <h2 className="text-lg font-bold text-white tracking-tight">SQL Analytics Workspace</h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/10 text-red-400 border border-red-500/20">
              DuckDB Columnar Engine
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-1">
            Execute analytical SQL queries with sub-second execution over in-memory columnar tables. Enforces read-only safeguards.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* Left: Schema & Table Browser */}
        <div className="bg-[#121216] border border-[#23232a] rounded-xl p-4 space-y-4">
          <div className="flex items-center space-x-2 text-xs font-bold text-white border-b border-[#23232a] pb-2.5">
            <Database size={14} className="text-red-400" />
            <span>DuckDB Tables</span>
          </div>

          <div className="space-y-1">
            {tables.map((t) => (
              <button
                key={t}
                onClick={() => {
                  loadSchema(t);
                  setQuery(`SELECT * FROM ${t} LIMIT 50;`);
                }}
                className={`w-full text-left px-2.5 py-1.5 rounded text-xs font-mono truncate transition-all ${
                  activeDataset?.table_name === t
                    ? 'bg-red-500/20 text-red-400 font-bold'
                    : 'text-zinc-400 hover:text-white hover:bg-[#1a1a22]'
                }`}
              >
                {t}
              </button>
            ))}
          </div>

          {selectedTableSchema.length > 0 && (
            <div className="border-t border-[#23232a] pt-3 space-y-2">
              <span className="text-[11px] font-semibold text-zinc-400 block uppercase tracking-wider">Columns Schema:</span>
              <div className="max-h-60 overflow-y-auto space-y-1 pr-1 font-mono text-[11px]">
                {selectedTableSchema.map((col, idx) => (
                  <div key={idx} className="flex items-center justify-between text-zinc-400 py-0.5 border-b border-[#1b1b22]">
                    <span className="text-zinc-200 truncate">{col.column_name}</span>
                    <span className="text-[10px] text-zinc-500">{col.column_type}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right: SQL Editor & Results */}
        <div className="lg:col-span-3 space-y-4">
          
          {/* SQL Editor Card */}
          <div className="bg-[#121216] border border-[#23232a] rounded-xl p-4 space-y-3">
            {/* Snippet shortcuts */}
            <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
              <span className="text-zinc-500">Snippets:</span>
              <button
                onClick={() => setQuery(`SELECT * FROM ${activeDataset?.table_name} LIMIT 25;`)}
                className="px-2 py-0.5 rounded bg-[#18181f] border border-[#282833] text-zinc-300 hover:text-white"
              >
                SELECT *
              </button>
              <button
                onClick={() => setQuery(`SELECT Region, ROUND(SUM(Sales), 2) AS total_sales, ROUND(AVG(Profit), 2) AS avg_profit\nFROM ${activeDataset?.table_name}\nGROUP BY Region\nORDER BY total_sales DESC;`)}
                className="px-2 py-0.5 rounded bg-[#18181f] border border-[#282833] text-zinc-300 hover:text-white"
              >
                GROUP BY
              </button>
              <button
                onClick={() => setQuery(`SELECT *, DENSE_RANK() OVER (ORDER BY Sales DESC) as rank_sales\nFROM ${activeDataset?.table_name}\nLIMIT 20;`)}
                className="px-2 py-0.5 rounded bg-[#18181f] border border-[#282833] text-zinc-300 hover:text-white"
              >
                WINDOW RANK()
              </button>
            </div>

            {/* Textarea Editor */}
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              rows={6}
              placeholder="Write analytical SQL here..."
              className="w-full bg-[#0a0a0d] text-zinc-200 font-mono text-xs border border-[#24242d] rounded-lg p-3 focus:outline-none focus:border-red-500 leading-relaxed resize-y"
            />

            {/* Actions Bar */}
            <div className="flex items-center justify-between">
              <button
                onClick={handleExplain}
                className="px-3 py-1.5 rounded-lg text-xs font-medium bg-[#1c1c24] text-zinc-300 border border-[#2c2c38] hover:bg-[#252530]"
              >
                Explain Plan
              </button>

              <button
                onClick={handleRunQuery}
                disabled={loading}
                className="flex items-center space-x-1.5 px-4 py-1.5 rounded-lg text-xs font-semibold bg-red-600 hover:bg-red-500 text-white shadow-md shadow-red-500/20 disabled:opacity-50"
              >
                <Play size={13} fill="currentColor" />
                <span>Run Query</span>
              </button>
            </div>
          </div>

          {/* EXPLAIN Execution Plan Drawer */}
          {plan && (
            <div className="p-3 bg-[#0a0a0d] border border-amber-500/30 rounded-xl font-mono text-xs text-amber-300 whitespace-pre-wrap">
              <div className="font-bold text-amber-400 mb-1">Execution Plan (DuckDB EXPLAIN):</div>
              {plan}
            </div>
          )}

          {/* Query Results Table */}
          {result && (
            <div className="bg-[#121216] border border-[#23232a] rounded-xl overflow-hidden shadow-sm">
              <div className="flex items-center justify-between px-4 py-2.5 bg-[#16161b] border-b border-[#23232a] text-xs">
                <div className="flex items-center space-x-3">
                  <span className="font-semibold text-white">Query Results</span>
                  {result.success && (
                    <span className="text-zinc-400 font-mono text-[11px]">
                      {result.row_count} rows in <strong className="text-emerald-400">{result.execution_time_ms} ms</strong>
                    </span>
                  )}
                </div>
              </div>

              {result.success ? (
                <div className="overflow-x-auto max-h-96 scrollbar-thin">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="bg-[#16161b] text-zinc-300 uppercase tracking-wider text-[10px] sticky top-0 border-b border-[#26262e]">
                      <tr>
                        {result.columns.map((c: string) => (
                          <th key={c} className="py-2.5 px-3 font-semibold whitespace-nowrap">{c}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#1e1e25] font-mono text-zinc-300">
                      {result.rows.map((row: any[], rIdx: number) => (
                        <tr key={rIdx} className="hover:bg-[#18181f]">
                          {row.map((val: any, cIdx: number) => (
                            <td key={cIdx} className="py-2 px-3 whitespace-nowrap">
                              {val === null ? <span className="text-zinc-600">null</span> : String(val)}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="p-4 bg-red-950/20 text-red-300 text-xs font-mono">
                  Error: {result.error}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
