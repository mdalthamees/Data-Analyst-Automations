import React, { useState, useEffect } from 'react';
import { 
  Search, 
  ChevronLeft, 
  ChevronRight, 
  ArrowUpDown, 
  ArrowUp, 
  ArrowDown, 
  Download, 
  Filter, 
  Layers, 
  Hash, 
  Calendar, 
  Tag, 
  Key, 
  CheckCircle2,
  RefreshCw
} from 'lucide-react';
import { DatasetMeta } from '../../types';
import { DatasetService, ReportsService } from '../../services/api';

interface DataExplorerProps {
  activeDataset?: DatasetMeta;
  onSelectSheet?: (sheetName: string) => void;
}

export const DataExplorer: React.FC<DataExplorerProps> = ({
  activeDataset,
  onSelectSheet
}) => {
  const [data, setData] = useState<{ columns: string[]; rows: any[][]; total_rows: number; page: number; total_pages: number }>({
    columns: [],
    rows: [],
    total_rows: 0,
    page: 1,
    total_pages: 1
  });
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(50);
  const [search, setSearch] = useState<string>('');
  const [sortBy, setSortBy] = useState<string | undefined>(undefined);
  const [sortDesc, setSortDesc] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (activeDataset?.id) {
      fetchPageData(1);
    }
  }, [activeDataset?.id, sortBy, sortDesc]);

  const fetchPageData = async (targetPage = page) => {
    if (!activeDataset?.id) return;
    setLoading(true);
    try {
      const res = await DatasetService.getData(
        activeDataset.id,
        targetPage,
        pageSize,
        sortBy,
        sortDesc,
        search
      );
      setData(res);
      setPage(res.page);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchPageData(1);
  };

  const toggleSort = (col: string) => {
    if (sortBy === col) {
      if (!sortDesc) {
        setSortDesc(true);
      } else {
        setSortBy(undefined);
        setSortDesc(false);
      }
    } else {
      setSortBy(col);
      setSortDesc(false);
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'numeric':
      case 'currency':
        return <Hash size={12} className="text-red-400" />;
      case 'date':
      case 'datetime':
        return <Calendar size={12} className="text-blue-400" />;
      case 'identifier':
        return <Key size={12} className="text-amber-400" />;
      default:
        return <Tag size={12} className="text-zinc-400" />;
    }
  };

  if (!activeDataset) {
    return (
      <div className="p-8 text-center text-zinc-500">
        Please select or upload a dataset to explore records.
      </div>
    );
  }

  const columnsMeta = activeDataset.profile?.columns || [];

  return (
    <div className="p-6 space-y-4 max-w-[1600px] mx-auto">
      {/* Top Header & Search Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#121216] border border-[#23232a] p-4 rounded-xl">
        <div className="flex items-center space-x-3">
          <h2 className="text-base font-bold text-white tracking-tight">Data Table Explorer</h2>
          <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-zinc-800 text-zinc-300">
            {data.total_rows.toLocaleString()} total rows
          </span>

          {/* Multiple sheets switcher if applicable */}
          {activeDataset.available_sheets && activeDataset.available_sheets.length > 1 && (
            <div className="flex items-center space-x-1.5 pl-3 border-l border-zinc-800 text-xs">
              <span className="text-zinc-500">Sheet:</span>
              {activeDataset.available_sheets.map((s) => (
                <button
                  key={s}
                  onClick={() => onSelectSheet && onSelectSheet(s)}
                  className={`px-2 py-0.5 rounded text-[11px] transition-all ${
                    activeDataset.selected_sheet === s
                      ? 'bg-red-500/20 text-red-400 border border-red-500/40 font-semibold'
                      : 'bg-zinc-800 text-zinc-400 hover:text-white'
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Search Bar & Export */}
        <div className="flex items-center space-x-2">
          <form onSubmit={handleSearchSubmit} className="flex items-center bg-[#18181f] border border-[#292933] rounded-lg px-2.5 py-1 text-xs">
            <Search size={13} className="text-zinc-400 mr-2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search table rows..."
              className="bg-transparent text-white placeholder-zinc-500 focus:outline-none w-48 text-xs"
            />
          </form>

          <a
            href={ReportsService.getCsvUrl(activeDataset.id)}
            download
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-[#1c1c23] text-zinc-300 border border-[#2b2b36] hover:bg-[#25252f] transition-all"
          >
            <Download size={13} />
            <span>Export CSV</span>
          </a>
        </div>
      </div>

      {/* Virtualized Data Table */}
      <div className="bg-[#121216] border border-[#23232a] rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto max-h-[650px] scrollbar-thin">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-[#16161b] text-zinc-300 uppercase tracking-wider text-[10px] sticky top-0 z-10 border-b border-[#26262e]">
              <tr>
                <th className="py-2.5 px-3 w-12 text-zinc-500 text-center font-mono">#</th>
                {data.columns.map((colName) => {
                  const colProfile = columnsMeta.find((c) => c.name === colName);
                  const isSorted = sortBy === colName;
                  return (
                    <th
                      key={colName}
                      onClick={() => toggleSort(colName)}
                      className="py-2.5 px-3 font-semibold hover:bg-[#1e1e26] cursor-pointer transition-colors whitespace-nowrap"
                    >
                      <div className="flex items-center space-x-1.5">
                        {colProfile && getTypeIcon(colProfile.inferred_type)}
                        <span>{colName}</span>
                        {isSorted ? (
                          sortDesc ? <ArrowDown size={11} className="text-red-400" /> : <ArrowUp size={11} className="text-red-400" />
                        ) : (
                          <ArrowUpDown size={10} className="text-zinc-600 opacity-60" />
                        )}
                      </div>
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e1e25] font-normal text-zinc-200">
              {data.rows.map((row, rIdx) => (
                <tr key={rIdx} className="hover:bg-[#18181f] transition-colors">
                  <td className="py-2 px-3 text-zinc-500 text-center font-mono text-[10px]">
                    {(page - 1) * pageSize + rIdx + 1}
                  </td>
                  {row.map((cell, cIdx) => (
                    <td key={cIdx} className="py-2 px-3 whitespace-nowrap font-mono text-zinc-300">
                      {cell === null || cell === undefined ? (
                        <span className="text-zinc-600 italic">null</span>
                      ) : typeof cell === 'number' ? (
                        cell.toLocaleString()
                      ) : (
                        String(cell)
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="flex items-center justify-between px-4 py-3 bg-[#141419] border-t border-[#23232a] text-xs text-zinc-400">
          <div className="flex items-center space-x-2">
            <span>Rows per page:</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setPage(1);
              }}
              className="bg-[#1b1b22] text-zinc-300 border border-[#2c2c36] rounded px-2 py-1 text-xs"
            >
              <option value="25">25</option>
              <option value="50">50</option>
              <option value="100">100</option>
              <option value="200">200</option>
            </select>
          </div>

          <div className="flex items-center space-x-3">
            <span>
              Page <strong className="text-zinc-200">{page}</strong> of <strong className="text-zinc-200">{data.total_pages}</strong>
            </span>
            <div className="flex items-center space-x-1">
              <button
                onClick={() => fetchPageData(Math.max(1, page - 1))}
                disabled={page <= 1 || loading}
                className="p-1.5 rounded bg-[#1c1c22] border border-[#2b2b35] disabled:opacity-40 hover:bg-[#25252e] text-zinc-300"
              >
                <ChevronLeft size={14} />
              </button>
              <button
                onClick={() => fetchPageData(Math.min(data.total_pages, page + 1))}
                disabled={page >= data.total_pages || loading}
                className="p-1.5 rounded bg-[#1c1c22] border border-[#2b2b35] disabled:opacity-40 hover:bg-[#25252e] text-zinc-300"
              >
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
