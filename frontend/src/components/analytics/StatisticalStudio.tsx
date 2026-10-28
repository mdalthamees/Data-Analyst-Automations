import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  Activity, 
  TrendingUp, 
  Grid, 
  PieChart, 
  AlertCircle,
  RefreshCw
} from 'lucide-react';
import { DatasetMeta } from '../../types';
import { AnalyticsService } from '../../services/api';

interface StatisticalStudioProps {
  activeDataset?: DatasetMeta;
}

export const StatisticalStudio: React.FC<StatisticalStudioProps> = ({
  activeDataset
}) => {
  const [descriptive, setDescriptive] = useState<any[]>([]);
  const [correlation, setCorrelation] = useState<{ columns: string[]; matrix: any[] }>({ columns: [], matrix: [] });
  
  const [paretoDim, setParetoDim] = useState<string>('');
  const [paretoMeas, setParetoMeas] = useState<string>('');
  const [paretoResult, setParetoResult] = useState<any>(null);

  const [anomalyMeas, setAnomalyMeas] = useState<string>('');
  const [anomalyResult, setAnomalyResult] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (activeDataset?.id) {
      loadStats();
    }
  }, [activeDataset?.id]);

  const loadStats = async () => {
    if (!activeDataset?.id) return;
    setLoading(true);
    try {
      const [descRes, corrRes] = await Promise.all([
        AnalyticsService.descriptive(activeDataset.id),
        AnalyticsService.correlation(activeDataset.id)
      ]);
      setDescriptive(descRes.statistics || []);
      setCorrelation(corrRes);

      const dims = activeDataset.profile?.candidate_dimensions || [];
      const meas = activeDataset.profile?.candidate_measures || [];
      if (dims.length > 0 && meas.length > 0) {
        setParetoDim(dims[0]);
        setParetoMeas(meas[0]);
        loadPareto(dims[0], meas[0]);
      }
      if (meas.length > 0) {
        setAnomalyMeas(meas[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const loadPareto = async (dim: string, meas: string) => {
    if (!activeDataset?.id || !dim || !meas) return;
    try {
      const res = await AnalyticsService.pareto(activeDataset.id, dim, meas);
      setParetoResult(res);
    } catch (e) {
      console.error(e);
    }
  };

  const loadAnomalies = async () => {
    if (!activeDataset?.id || !anomalyMeas) return;
    try {
      const res = await AnalyticsService.anomalies(activeDataset.id, anomalyMeas, 3.0);
      setAnomalyResult(res);
    } catch (e) {
      console.error(e);
    }
  };

  if (!activeDataset) {
    return <div className="p-8 text-center text-zinc-500">Please select a dataset for statistical analysis.</div>;
  }

  const dims = activeDataset.profile?.candidate_dimensions || [];
  const meas = activeDataset.profile?.candidate_measures || [];

  return (
    <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
      {/* Top Banner */}
      <div className="bg-[#121216] border border-[#23232a] p-4 rounded-xl flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2">
            <BarChart3 size={18} className="text-red-400" />
            <h2 className="text-lg font-bold text-white tracking-tight">Statistical BI & Distribution Studio</h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/10 text-red-400 border border-red-500/20">
              Descriptive & Exploratory
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-1">
            Examine parametric summaries, Pearson correlation dependencies, and Pareto 80/20 category concentrations.
          </p>
        </div>
      </div>

      {/* 1. Descriptive Statistics Summary */}
      <div className="bg-[#121216] border border-[#23232a] rounded-xl p-5 space-y-3">
        <h3 className="text-sm font-bold text-white flex items-center space-x-2">
          <Activity size={15} className="text-red-400" />
          <span>Parametric Descriptive Statistics</span>
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-[#18181f] text-zinc-400 uppercase text-[10px] font-semibold border-b border-[#25252e]">
              <tr>
                <th className="py-2.5 px-3">Column</th>
                <th className="py-2.5 px-3">Count</th>
                <th className="py-2.5 px-3">Mean</th>
                <th className="py-2.5 px-3">Std Dev</th>
                <th className="py-2.5 px-3">Min</th>
                <th className="py-2.5 px-3">25% (Q1)</th>
                <th className="py-2.5 px-3">Median</th>
                <th className="py-2.5 px-3">75% (Q3)</th>
                <th className="py-2.5 px-3">Max</th>
                <th className="py-2.5 px-3">Skewness</th>
                <th className="py-2.5 px-3">Distribution</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e1e25] font-mono text-zinc-300">
              {descriptive.map((row) => (
                <tr key={row.column} className="hover:bg-[#18181f]">
                  <td className="py-2 px-3 font-sans font-bold text-white">{row.column}</td>
                  <td className="py-2 px-3">{row.count?.toLocaleString()}</td>
                  <td className="py-2 px-3 font-semibold text-white">{row.mean?.toLocaleString()}</td>
                  <td className="py-2 px-3 text-zinc-400">{row.std?.toLocaleString()}</td>
                  <td className="py-2 px-3">{row.min?.toLocaleString()}</td>
                  <td className="py-2 px-3">{row.q25?.toLocaleString()}</td>
                  <td className="py-2 px-3 font-semibold text-emerald-400">{row.median?.toLocaleString()}</td>
                  <td className="py-2 px-3">{row.q75?.toLocaleString()}</td>
                  <td className="py-2 px-3">{row.max?.toLocaleString()}</td>
                  <td className="py-2 px-3">{row.skewness}</td>
                  <td className="py-2 px-3 font-sans">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                      row.distribution_shape === 'Normal' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'
                    }`}>
                      {row.distribution_shape}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* 2. Pearson Correlation Matrix Heatmap */}
        <div className="bg-[#121216] border border-[#23232a] rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-[#23232a] pb-3">
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <Grid size={15} className="text-red-400" />
              <span>Pearson Correlation Matrix</span>
            </h3>
            <span className="text-[11px] text-zinc-500">Values range: -1.0 to +1.0</span>
          </div>

          {correlation.columns.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-center text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[#26262e]">
                    <th className="py-2 px-2 text-left text-zinc-400">Var</th>
                    {correlation.columns.map((col) => (
                      <th key={col} className="py-2 px-2 font-mono text-[10px] text-zinc-300 truncate max-w-[80px]" title={col}>
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1e1e25] font-mono text-[11px]">
                  {correlation.matrix.map((row) => (
                    <tr key={row.variable}>
                      <td className="py-2 px-2 text-left font-sans font-semibold text-zinc-300 text-xs truncate max-w-[100px]" title={row.variable}>
                        {row.variable}
                      </td>
                      {correlation.columns.map((c) => {
                        const val = row[c];
                        const isPos = val > 0.4;
                        const isNeg = val < -0.3;
                        return (
                          <td
                            key={c}
                            className={`py-2 px-2 font-semibold ${
                              val === 1 ? 'text-zinc-500' : isPos ? 'text-red-400 font-bold bg-red-950/20' : isNeg ? 'text-blue-400 bg-blue-950/20' : 'text-zinc-400'
                            }`}
                          >
                            {val}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-xs text-zinc-500 p-4 text-center">Insufficient numeric features for correlation matrix.</div>
          )}
        </div>

        {/* 3. Pareto 80/20 Distribution Analysis */}
        <div className="bg-[#121216] border border-[#23232a] rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-[#23232a] pb-3">
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <PieChart size={15} className="text-amber-400" />
              <span>Pareto 80/20 Concentration</span>
            </h3>
            {paretoResult && (
              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-red-500/20 text-red-400">
                Top {paretoResult.vital_few_count} segments = 80%
              </span>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <select
              value={paretoDim}
              onChange={(e) => { setParetoDim(e.target.value); loadPareto(e.target.value, paretoMeas); }}
              className="bg-[#18181f] text-white border border-[#272733] rounded px-2.5 py-1 text-xs"
            >
              {dims.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
            <select
              value={paretoMeas}
              onChange={(e) => { setParetoMeas(e.target.value); loadPareto(paretoDim, e.target.value); }}
              className="bg-[#18181f] text-white border border-[#272733] rounded px-2.5 py-1 text-xs"
            >
              {meas.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>

          {paretoResult && (
            <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
              {paretoResult.items?.slice(0, 8).map((item: any) => (
                <div key={item.category} className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-white">{item.category}</span>
                    <span className="font-mono text-zinc-400">
                      ${item.value?.toLocaleString()} ({item.cumulative_pct}%)
                    </span>
                  </div>
                  <div className="w-full bg-[#1e1e27] h-1.5 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${item.cumulative_pct <= 80 ? 'bg-red-500' : 'bg-zinc-600'}`}
                      style={{ width: `${Math.min(100, item.cumulative_pct)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
