import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  Brain, 
  Layers, 
  AlertCircle, 
  CheckCircle2, 
  Sliders, 
  Calendar,
  RefreshCw
} from 'lucide-react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Area, ComposedChart } from 'recharts';
import { DatasetMeta } from '../../types';
import { MLService } from '../../services/api';

interface MLForecastingStudioProps {
  activeDataset?: DatasetMeta;
}

export const MLForecastingStudio: React.FC<MLForecastingStudioProps> = ({
  activeDataset
}) => {
  const [targetMeasure, setTargetMeasure] = useState<string>('');
  const [dateColumn, setDateColumn] = useState<string>('');
  const [periodsAhead, setPeriodsAhead] = useState<number>(6);
  const [forecastData, setForecastData] = useState<any>(null);
  
  const [clusterFeatures, setClusterFeatures] = useState<string[]>([]);
  const [nClusters, setNClusters] = useState<number>(3);
  const [segmentResult, setSegmentResult] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (activeDataset?.id) {
      const dates = activeDataset.profile?.candidate_dates || [];
      const measures = activeDataset.profile?.candidate_measures || [];
      if (measures.length > 0) setTargetMeasure(measures[0]);
      if (dates.length > 0) setDateColumn(dates[0]);
      setClusterFeatures(measures.slice(0, 3));
      
      if (dates.length > 0 && measures.length > 0) {
        handleRunForecast(measures[0], dates[0]);
      }
    }
  }, [activeDataset?.id]);

  const handleRunForecast = async (meas = targetMeasure, dt = dateColumn) => {
    if (!activeDataset?.id || !meas || !dt) return;
    setLoading(true);
    setError(null);
    try {
      const res = await MLService.forecast(activeDataset.id, meas, dt, periodsAhead);
      setForecastData(res);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message || "Forecasting error");
    } finally {
      setLoading(false);
    }
  };

  const handleRunSegmentation = async () => {
    if (!activeDataset?.id || clusterFeatures.length < 2) return;
    setLoading(true);
    setError(null);
    try {
      const res = await MLService.segmentation(activeDataset.id, clusterFeatures, nClusters);
      setSegmentResult(res);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message || "Clustering error");
    } finally {
      setLoading(false);
    }
  };

  if (!activeDataset) {
    return <div className="p-8 text-center text-zinc-500">Please select a dataset to use Forecasting & ML.</div>;
  }

  const measures = activeDataset.profile?.candidate_measures || [];
  const dates = activeDataset.profile?.candidate_dates || [];

  // Combine historical and forecast points for chart
  const combinedChartPoints = forecastData ? [
    ...(forecastData.historical_data || []).map((h: any) => ({
      period: h.period,
      actual: h.actual,
      forecast: null,
      lower_bound: null,
      upper_bound: null
    })),
    ...(forecastData.forecast_data || []).filter((f: any) => f.is_forecast).map((f: any) => ({
      period: f.period,
      actual: null,
      forecast: f.forecast,
      lower_bound: f.lower_bound,
      upper_bound: f.upper_bound
    }))
  ] : [];

  return (
    <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
      {/* Top Banner */}
      <div className="bg-[#121216] border border-[#23232a] p-4 rounded-xl flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2">
            <Brain size={18} className="text-red-400" />
            <h2 className="text-lg font-bold text-white tracking-tight">Predictive Forecasting & Machine Learning</h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/10 text-red-400 border border-red-500/20">
              Scikit-Learn & Statsmodels
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-1">
            Time-series trend forecasting with 95% statistical confidence intervals and K-Means customer segmentation clustering.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-950/20 border border-red-500/30 rounded-xl text-xs text-red-300 flex items-center space-x-2">
          <AlertCircle size={14} />
          <span>{error}</span>
        </div>
      )}

      {/* 1. Time Series Forecasting Studio */}
      <div className="bg-[#121216] border border-[#23232a] rounded-xl p-5 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-[#23232a] pb-3">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <TrendingUp size={16} className="text-red-400" />
              <span>Time-Series Forecast (95% Confidence Interval)</span>
            </h3>
            <p className="text-xs text-zinc-400">Projects future values with train/test validation.</p>
          </div>

          <div className="flex items-center space-x-2">
            <select
              value={targetMeasure}
              onChange={(e) => setTargetMeasure(e.target.value)}
              className="bg-[#18181f] text-white border border-[#272733] rounded px-2.5 py-1 text-xs"
            >
              {measures.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
            <select
              value={dateColumn}
              onChange={(e) => setDateColumn(e.target.value)}
              className="bg-[#18181f] text-white border border-[#272733] rounded px-2.5 py-1 text-xs"
            >
              {dates.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
            <select
              value={periodsAhead}
              onChange={(e) => setPeriodsAhead(Number(e.target.value))}
              className="bg-[#18181f] text-white border border-[#272733] rounded px-2.5 py-1 text-xs"
            >
              <option value="3">3 Months Ahead</option>
              <option value="6">6 Months Ahead</option>
              <option value="12">12 Months Ahead</option>
            </select>
            <button
              onClick={() => handleRunForecast()}
              disabled={loading}
              className="px-3 py-1 bg-red-600 hover:bg-red-500 text-white rounded text-xs font-semibold shadow-sm"
            >
              Generate Forecast
            </button>
          </div>
        </div>

        {/* Validation Metrics Strip */}
        {forecastData?.validation_metrics && (
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-[#18181f] border border-[#282833] p-2.5 rounded-lg text-center">
              <div className="text-[10px] text-zinc-400 uppercase tracking-wider">RMSE (Holdout Error)</div>
              <div className="text-base font-extrabold text-white font-mono mt-0.5">
                ${forecastData.validation_metrics.rmse.toLocaleString()}
              </div>
            </div>
            <div className="bg-[#18181f] border border-[#282833] p-2.5 rounded-lg text-center">
              <div className="text-[10px] text-zinc-400 uppercase tracking-wider">MAE (Absolute Error)</div>
              <div className="text-base font-extrabold text-white font-mono mt-0.5">
                ${forecastData.validation_metrics.mae.toLocaleString()}
              </div>
            </div>
            <div className="bg-[#18181f] border border-[#282833] p-2.5 rounded-lg text-center">
              <div className="text-[10px] text-zinc-400 uppercase tracking-wider">R² Fit Score</div>
              <div className="text-base font-extrabold text-emerald-400 font-mono mt-0.5">
                {forecastData.validation_metrics.r2_score}
              </div>
            </div>
          </div>
        )}

        {/* Forecast Projection Chart */}
        {combinedChartPoints.length > 0 && (
          <div style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
              <ComposedChart data={combinedChartPoints} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#222228" vertical={false} />
                <XAxis dataKey="period" stroke="#71717a" fontSize={11} />
                <YAxis stroke="#71717a" fontSize={11} tickFormatter={(v) => (v >= 1000 ? `${(v/1000).toFixed(0)}k` : v)} />
                <Tooltip
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="bg-[#141418] border border-[#2b2b34] rounded-lg p-2.5 shadow-xl text-xs space-y-1">
                          <p className="font-semibold text-zinc-300">{label}</p>
                          {payload.map((e: any, idx: number) => (
                            <div key={idx} className="text-zinc-400 flex items-center space-x-1.5 font-mono">
                              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: e.color }}></span>
                              <span>{e.name}:</span>
                              <span className="text-white font-bold">
                                {typeof e.value === 'number' ? `$${e.value.toLocaleString()}` : e.value}
                              </span>
                            </div>
                          ))}
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                {/* Confidence Interval Band */}
                <Area type="monotone" dataKey="upper_bound" stroke="none" fill="#ef4444" fillOpacity={0.12} name="Upper 95% Bound" />
                {/* Historical Actuals */}
                <Line type="monotone" dataKey="actual" stroke="#f4f4f5" strokeWidth={2.5} dot={{ r: 3 }} name="Historical Actual" />
                {/* Projected Forecast */}
                <Line type="monotone" dataKey="forecast" stroke="#ef4444" strokeWidth={2.5} strokeDasharray="5 5" dot={{ r: 4 }} name="Forecast Projection" />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Model Assumptions & Limitations */}
        {forecastData?.model_assumptions && (
          <div className="p-3 bg-[#15151c] border border-[#262631] rounded-lg text-xs space-y-1 text-zinc-400">
            <span className="font-bold text-zinc-300 block">Model Assumptions & Limitations:</span>
            {forecastData.model_assumptions.map((asm: string, i: number) => (
              <div key={i} className="flex items-center space-x-2">
                <span className="w-1.5 h-1.5 rounded-full bg-red-400"></span>
                <span>{asm}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 2. Customer Segmentation Clustering (K-Means) */}
      <div className="bg-[#121216] border border-[#23232a] rounded-xl p-5 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-[#23232a] pb-3">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <Layers size={16} className="text-red-400" />
              <span>Customer Segmentation (K-Means Clustering)</span>
            </h3>
            <p className="text-xs text-zinc-400">Groups records into behavioral segments based on multidimensional feature distances.</p>
          </div>

          <div className="flex items-center space-x-2">
            <select
              value={nClusters}
              onChange={(e) => setNClusters(Number(e.target.value))}
              className="bg-[#18181f] text-white border border-[#272733] rounded px-2.5 py-1 text-xs"
            >
              <option value="2">2 Clusters</option>
              <option value="3">3 Clusters</option>
              <option value="4">4 Clusters</option>
              <option value="5">5 Clusters</option>
            </select>
            <button
              onClick={handleRunSegmentation}
              disabled={loading}
              className="px-3 py-1 bg-red-600 hover:bg-red-500 text-white rounded text-xs font-semibold shadow-sm"
            >
              Run Clustering
            </button>
          </div>
        </div>

        {/* Cluster Profiles Cards */}
        {segmentResult?.cluster_profiles && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {segmentResult.cluster_profiles.map((c: any) => (
              <div key={c.cluster_name} className="p-4 bg-[#18181f] border border-[#282833] rounded-xl space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-sm">{c.cluster_name}</span>
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-red-500/20 text-red-400">
                    {c.size} records ({c.percentage}%)
                  </span>
                </div>
                <div className="space-y-1 text-xs text-zinc-400 pt-1 border-t border-[#252530]">
                  {Object.entries(c.means).map(([feat, val]: any) => (
                    <div key={feat} className="flex items-center justify-between">
                      <span className="truncate max-w-[120px]">{feat}:</span>
                      <span className="font-mono text-zinc-200 font-semibold">{val.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
