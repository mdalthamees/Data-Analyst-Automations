import React from 'react';
import { 
  LayoutDashboard, 
  Sparkles, 
  Database, 
  Wand2, 
  Terminal, 
  BarChart3, 
  TrendingUp, 
  FileText, 
  Server, 
  ChevronLeft, 
  ChevronRight,
  ShieldCheck,
  Zap
} from 'lucide-react';
import { TabType, DatasetMeta } from '../../types';

interface SidebarProps {
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;
  collapsed: boolean;
  setCollapsed: (collapsed: boolean) => void;
  activeDataset?: DatasetMeta;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  collapsed,
  setCollapsed,
  activeDataset
}) => {
  const navItems: Array<{ id: TabType; label: string; icon: React.ReactNode; badge?: string }> = [
    { id: 'overview', label: 'Executive Dashboard', icon: <LayoutDashboard size={19} /> },
    { id: 'chat', label: 'AI Data Analyst', icon: <Sparkles size={19} className="text-red-400" />, badge: 'Tanglish' },
    { id: 'explorer', label: 'Dataset & Explorer', icon: <Database size={19} /> },
    { id: 'cleaning', label: 'Cleaning Studio', icon: <Wand2 size={19} /> },
    { id: 'formulas', label: 'Column Intelligence', icon: <BarChart3 size={19} />, badge: 'Auto' },
    { id: 'sql', label: 'SQL Analytics', icon: <Terminal size={19} /> },
    { id: 'analytics', label: 'Statistical BI', icon: <BarChart3 size={19} /> },
    { id: 'ml', label: 'Forecasting & ML', icon: <TrendingUp size={19} /> },
    { id: 'reports', label: 'Export Centre', icon: <FileText size={19} /> },
    { id: 'connectors', label: 'Data Connectors', icon: <Server size={19} /> },
  ];

  return (
    <aside
      className={`h-screen flex flex-col bg-[#0e0e11] border-r border-[#222227] transition-all duration-300 z-30 select-none ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="flex items-center justify-between px-4 h-16 border-b border-[#222227]">
        {!collapsed && (
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-red-600 to-rose-500 flex items-center justify-center shadow-lg shadow-red-500/20">
              <Zap size={18} className="text-white fill-current" />
            </div>
            <div>
              <span className="font-extrabold tracking-tight text-white text-base">DataPilot</span>
              <span className="ml-1 px-1.5 py-0.5 text-[10px] font-bold rounded bg-red-500/10 text-red-400 border border-red-500/20">AI</span>
            </div>
          </div>
        )}
        {collapsed && (
          <div className="w-8 h-8 mx-auto rounded-lg bg-gradient-to-tr from-red-600 to-rose-500 flex items-center justify-center shadow-lg shadow-red-500/20">
            <Zap size={18} className="text-white fill-current" />
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-[#1c1c22] transition-colors"
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {navItems.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-all group relative ${
                isActive
                  ? 'bg-red-500/10 text-white border border-red-500/30 shadow-sm shadow-red-500/10'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-[#18181d]'
              }`}
            >
              <div className={`${isActive ? 'text-red-400' : 'text-zinc-400 group-hover:text-zinc-200'}`}>
                {item.icon}
              </div>
              {!collapsed && (
                <div className="ml-3 flex-1 flex items-center justify-between text-left">
                  <span>{item.label}</span>
                  {item.badge && (
                    <span className="px-1.5 py-0.5 text-[10px] rounded font-semibold bg-zinc-800 text-zinc-300 border border-zinc-700/60">
                      {item.badge}
                    </span>
                  )}
                </div>
              )}
              {collapsed && (
                <div className="absolute left-full ml-2 px-2 py-1 bg-zinc-900 text-zinc-200 text-xs rounded border border-zinc-700 shadow-md whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50">
                  {item.label}
                </div>
              )}
            </button>
          );
        })}
      </nav>

      {/* Active Dataset Footer */}
      <div className="p-3 border-t border-[#222227] bg-[#0a0a0d]">
        {!collapsed ? (
          <div className="bg-[#141419] rounded-lg p-2.5 border border-[#26262e]">
            <div className="flex items-center justify-between text-[11px] text-zinc-400 mb-1">
              <span className="flex items-center space-x-1">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>Active OLAP Table</span>
              </span>
              <span className="font-mono text-zinc-300">{activeDataset?.row_count?.toLocaleString() || 0} rows</span>
            </div>
            <div className="text-xs font-semibold text-white truncate" title={activeDataset?.filename || 'No dataset loaded'}>
              {activeDataset?.filename || 'No dataset active'}
            </div>
            {activeDataset?.profile?.quality_summary && (
              <div className="mt-1.5 flex items-center justify-between text-[10px] text-zinc-400">
                <span>Quality Score</span>
                <span className="text-red-400 font-bold">{activeDataset.profile.quality_summary.overall_score}%</span>
              </div>
            )}
          </div>
        ) : (
          <div className="w-8 h-8 mx-auto rounded-lg bg-[#141419] flex items-center justify-center border border-[#26262e]" title={activeDataset?.filename || 'Dataset'}>
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
          </div>
        )}
      </div>
    </aside>
  );
};
