import React, { useState } from 'react';
import { 
  Server, 
  Database, 
  CheckCircle2, 
  AlertCircle, 
  Play, 
  ArrowRight,
  ShieldCheck,
  RefreshCw
} from 'lucide-react';
import { DatasetMeta } from '../../types';
import { ConnectorsService } from '../../services/api';

interface DatabaseConnectorsProps {
  onDatasetImported: (dataset: DatasetMeta) => void;
}

export const DatabaseConnectors: React.FC<DatabaseConnectorsProps> = ({
  onDatasetImported
}) => {
  const [dbType, setDbType] = useState<string>('sqlite');
  const [database, setDatabase] = useState<string>('test.db');
  const [host, setHost] = useState<string>('localhost');
  const [port, setPort] = useState<string>('');
  const [user, setUser] = useState<string>('');
  const [password, setPassword] = useState<string>('');

  const [testResult, setTestResult] = useState<any>(null);
  const [selectedTable, setSelectedTable] = useState<string>('');
  const [testing, setTesting] = useState<boolean>(false);
  const [importing, setImporting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleTestConnection = async () => {
    setTesting(true);
    setError(null);
    setTestResult(null);
    try {
      const res = await ConnectorsService.test(
        dbType,
        database,
        host,
        port ? Number(port) : undefined,
        user,
        password
      );
      setTestResult(res);
      if (res.tables && res.tables.length > 0) {
        setSelectedTable(res.tables[0]);
      }
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message || "Connection failed");
    } finally {
      setTesting(false);
    }
  };

  const handleImportTable = async () => {
    if (!selectedTable) return;
    setImporting(true);
    setError(null);
    try {
      const res = await ConnectorsService.import(
        dbType,
        database,
        selectedTable,
        host,
        port ? Number(port) : undefined,
        user,
        password
      );
      onDatasetImported(res);
      setTestResult(null);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message || "Import failed");
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-[1200px] mx-auto">
      {/* Top Banner */}
      <div className="bg-[#121216] border border-[#23232a] p-4 rounded-xl flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2">
            <Server size={18} className="text-red-400" />
            <h2 className="text-lg font-bold text-white tracking-tight">Database & Enterprise Connectors</h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/10 text-red-400 border border-red-500/20">
              SQLAlchemy Read-Only
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-1">
            Connect to external production or staging databases. Ingest tables into local DuckDB without requiring third-party cloud tools.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-950/20 border border-red-500/30 rounded-xl text-xs text-red-300 flex items-center space-x-2">
          <AlertCircle size={14} />
          <span>{error}</span>
        </div>
      )}

      {/* Connection Form */}
      <div className="bg-[#121216] border border-[#23232a] rounded-xl p-5 space-y-4">
        <h3 className="text-sm font-bold text-white flex items-center space-x-2">
          <Database size={15} className="text-red-400" />
          <span>Connection Configuration</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="text-[11px] font-semibold text-zinc-400 mb-1 block">Database Engine:</label>
            <select
              value={dbType}
              onChange={(e) => setDbType(e.target.value)}
              className="w-full bg-[#18181f] text-white border border-[#272733] rounded px-2.5 py-1.5 text-xs focus:outline-none focus:border-red-500"
            >
              <option value="sqlite">SQLite (File-based)</option>
              <option value="postgresql">PostgreSQL</option>
              <option value="mysql">MySQL</option>
            </select>
          </div>

          <div>
            <label className="text-[11px] font-semibold text-zinc-400 mb-1 block">Database Name / Path:</label>
            <input
              type="text"
              value={database}
              onChange={(e) => setDatabase(e.target.value)}
              placeholder="e.g. analytics_db or path/to/file.db"
              className="w-full bg-[#18181f] text-white border border-[#272733] rounded px-2.5 py-1.5 text-xs focus:outline-none focus:border-red-500"
            />
          </div>

          <div>
            <label className="text-[11px] font-semibold text-zinc-400 mb-1 block">Host (Optional for SQLite):</label>
            <input
              type="text"
              value={host}
              onChange={(e) => setHost(e.target.value)}
              placeholder="localhost"
              disabled={dbType === 'sqlite'}
              className="w-full bg-[#18181f] text-white border border-[#272733] rounded px-2.5 py-1.5 text-xs focus:outline-none focus:border-red-500 disabled:opacity-40"
            />
          </div>

          <div>
            <label className="text-[11px] font-semibold text-zinc-400 mb-1 block">Port:</label>
            <input
              type="number"
              value={port}
              onChange={(e) => setPort(e.target.value)}
              placeholder={dbType === 'postgresql' ? '5432' : '3306'}
              disabled={dbType === 'sqlite'}
              className="w-full bg-[#18181f] text-white border border-[#272733] rounded px-2.5 py-1.5 text-xs focus:outline-none focus:border-red-500 disabled:opacity-40"
            />
          </div>

          <div>
            <label className="text-[11px] font-semibold text-zinc-400 mb-1 block">Username:</label>
            <input
              type="text"
              value={user}
              onChange={(e) => setUser(e.target.value)}
              placeholder="postgres"
              disabled={dbType === 'sqlite'}
              className="w-full bg-[#18181f] text-white border border-[#272733] rounded px-2.5 py-1.5 text-xs focus:outline-none focus:border-red-500 disabled:opacity-40"
            />
          </div>

          <div>
            <label className="text-[11px] font-semibold text-zinc-400 mb-1 block">Password:</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              disabled={dbType === 'sqlite'}
              className="w-full bg-[#18181f] text-white border border-[#272733] rounded px-2.5 py-1.5 text-xs focus:outline-none focus:border-red-500 disabled:opacity-40"
            />
          </div>
        </div>

        <button
          onClick={handleTestConnection}
          disabled={testing}
          className="px-4 py-2 bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-md shadow-red-500/20"
        >
          {testing ? "Testing Connection..." : "Test Connection"}
        </button>
      </div>

      {/* Introspected Tables & Import Wizard */}
      {testResult && (
        <div className="bg-[#121216] border border-[#23232a] rounded-xl p-5 space-y-4">
          <div className="flex items-center space-x-2 text-emerald-400 text-xs font-bold">
            <CheckCircle2 size={16} />
            <span>{testResult.message} ({testResult.latency_ms} ms)</span>
          </div>

          {testResult.tables && testResult.tables.length > 0 ? (
            <div className="space-y-3">
              <label className="text-xs font-semibold text-zinc-300 block">Select Table to Import into DuckDB:</label>
              <div className="flex items-center space-x-3">
                <select
                  value={selectedTable}
                  onChange={(e) => setSelectedTable(e.target.value)}
                  className="flex-1 bg-[#18181f] text-white border border-[#272733] rounded px-3 py-2 text-xs"
                >
                  {testResult.tables.map((t: string) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
                <button
                  onClick={handleImportTable}
                  disabled={importing}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold flex items-center space-x-1.5 shadow-md disabled:opacity-50"
                >
                  <span>{importing ? "Importing..." : "Import Table"}</span>
                  <ArrowRight size={13} />
                </button>
              </div>
            </div>
          ) : (
            <div className="text-xs text-zinc-400">Connected successfully, but no user tables found in database.</div>
          )}
        </div>
      )}
    </div>
  );
};
