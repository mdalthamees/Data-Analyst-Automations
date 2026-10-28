import React, { useEffect, useMemo, useState } from 'react';
import { Pause, Play } from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';

interface ChartRendererProps {
  type: string;
  data: any[];
  xKey?: string;
  yKeys?: string[];
  nameKey?: string;
  valueKey?: string;
  playKey?: string;
  color?: string;
  height?: number;
}

const PALETTE = ['#ef4444', '#f87171', '#fb923c', '#e11d48', '#be123c', '#991b1b', '#f43f5e'];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-[#141418] border border-[#2b2b34] rounded-lg p-2.5 shadow-xl text-xs">
        <p className="font-semibold text-zinc-300 mb-1">{label}</p>
        {payload.map((entry: any, index: number) => {
          const val = entry.value;
          const formatted = typeof val === 'number' ? val.toLocaleString(undefined, { maximumFractionDigits: 2 }) : val;
          return (
            <div key={`item-${index}`} className="flex items-center space-x-2 text-zinc-400">
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color || entry.fill }}></span>
              <span className="capitalize">{entry.name || 'Value'}:</span>
              <span className="font-mono font-semibold text-white">{formatted}</span>
            </div>
          );
        })}
      </div>
    );
  }
  return null;
};

export const ChartRenderer: React.FC<ChartRendererProps> = ({
  type,
  data,
  xKey = 'name',
  yKeys = ['value'],
  nameKey = 'name',
  valueKey = 'value',
  playKey,
  color = '#ef4444',
  height = 280
}) => {
  const [frameIndex, setFrameIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const frames = useMemo(
    () => playKey && Array.isArray(data)
      ? [...new Set(data.map((point) => point[playKey]).filter((frame) => frame != null).map(String))]
        .sort((left, right) => left.localeCompare(right, undefined, { numeric: true }))
      : [],
    [data, playKey]
  );
  const hasPlayback = frames.length > 1;

  useEffect(() => {
    setFrameIndex(0);
    setIsPlaying(false);
  }, [data, playKey]);

  useEffect(() => {
    if (!isPlaying) return;
    if (frameIndex >= frames.length - 1) {
      setIsPlaying(false);
      return;
    }

    const timer = window.setTimeout(() => setFrameIndex((current) => current + 1), 900);
    return () => window.clearTimeout(timer);
  }, [frameIndex, frames.length, isPlaying]);

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-xs text-zinc-500">
        No chart points available to render.
      </div>
    );
  }

  const primaryY = yKeys[0] || 'value';

  if (type === 'bar') {
    return (
      <div style={{ width: '100%', height }}>
        <ResponsiveContainer>
          <BarChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#222228" vertical={false} />
            <XAxis dataKey={xKey} stroke="#71717a" fontSize={11} tickLine={false} />
            <YAxis stroke="#71717a" fontSize={11} tickLine={false} tickFormatter={(v) => (v >= 1000 ? `${(v/1000).toFixed(0)}k` : v)} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey={primaryY} fill={color} radius={[4, 4, 0, 0]} isAnimationActive animationDuration={700} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (type === 'area' || type === 'trend') {
    return (
      <div style={{ width: '100%', height }}>
        <ResponsiveContainer>
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <defs>
              <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.4} />
                <stop offset="95%" stopColor={color} stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#222228" vertical={false} />
            <XAxis dataKey={xKey} stroke="#71717a" fontSize={11} tickLine={false} />
            <YAxis stroke="#71717a" fontSize={11} tickLine={false} tickFormatter={(v) => (v >= 1000 ? `${(v/1000).toFixed(0)}k` : v)} />
            <Tooltip content={<CustomTooltip />} />
            {yKeys.length > 1 && <Legend wrapperStyle={{ fontSize: '11px', color: '#a1a1aa' }} />}
            <Area type="monotone" dataKey={primaryY} stroke={color} strokeWidth={2} fillOpacity={1} fill="url(#areaGradient)" isAnimationActive animationDuration={900} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (type === 'line') {
    return (
      <div style={{ width: '100%', height }}>
        <ResponsiveContainer>
          <LineChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#222228" vertical={false} />
            <XAxis dataKey={xKey} stroke="#71717a" fontSize={11} tickLine={false} />
            <YAxis stroke="#71717a" fontSize={11} tickLine={false} tickFormatter={(v) => (v >= 1000 ? `${(v/1000).toFixed(0)}k` : v)} />
            <Tooltip content={<CustomTooltip />} />
            {yKeys.length > 1 && <Legend wrapperStyle={{ fontSize: '11px', color: '#a1a1aa' }} />}
            {yKeys.map((y, idx) => (
              <Line
                key={y}
                type="monotone"
                dataKey={y}
                stroke={PALETTE[idx % PALETTE.length]}
                strokeWidth={2}
                dot={{ r: 3 }}
                isAnimationActive
                animationDuration={900}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (type === 'donut' || type === 'pie') {
    return (
      <div style={{ width: '100%', height }}>
        <ResponsiveContainer>
          <PieChart>
            <Tooltip content={<CustomTooltip />} />
            <Pie
              data={data}
              dataKey={valueKey}
              nameKey={nameKey}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={85}
              paddingAngle={3}
              isAnimationActive
              animationDuration={900}
            >
              {data.map((_, index) => (
                <Cell key={`cell-${index}`} fill={PALETTE[index % PALETTE.length]} stroke="#121215" strokeWidth={2} />
              ))}
            </Pie>
            <Legend verticalAlign="bottom" height={36} wrapperStyle={{ fontSize: '11px', color: '#a1a1aa' }} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (type === 'scatter') {
    const scatterData = hasPlayback
      ? data.filter((point) => frames.indexOf(String(point[playKey!])) <= frameIndex)
      : data;
    const chartHeight = hasPlayback ? Math.max(height - 46, 160) : height;

    return (
      <div style={{ width: '100%', height }}>
        <div style={{ width: '100%', height: chartHeight }}>
          <ResponsiveContainer>
            <ScatterChart margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#222228" />
              <XAxis dataKey={xKey} stroke="#71717a" fontSize={11} tickLine={false} />
              <YAxis dataKey={primaryY} stroke="#71717a" fontSize={11} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Scatter name="Distribution" data={scatterData} fill={color} isAnimationActive animationDuration={700} />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
        {hasPlayback && (
          <div className="flex h-[46px] items-center gap-3 px-2 text-[11px] text-zinc-400">
            <button
              type="button"
              onClick={() => {
                if (!isPlaying && frameIndex >= frames.length - 1) setFrameIndex(0);
                setIsPlaying((playing) => !playing);
              }}
              aria-label={isPlaying ? 'Pause scatter chart playback' : 'Play scatter chart playback'}
              className="rounded-md border border-[#30303a] p-1.5 text-zinc-200 hover:bg-[#202027]"
            >
              {isPlaying ? <Pause size={13} /> : <Play size={13} />}
            </button>
            <input
              aria-label="Scatter chart play axis"
              type="range"
              min={0}
              max={frames.length - 1}
              value={frameIndex}
              onChange={(event) => {
                setFrameIndex(Number(event.target.value));
                setIsPlaying(false);
              }}
              className="min-w-0 flex-1 accent-red-500"
            />
            <span className="min-w-20 text-right font-mono text-zinc-300">{frames[frameIndex]}</span>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center h-48 text-xs text-zinc-500">
      Unknown chart type: {type}
    </div>
  );
};
