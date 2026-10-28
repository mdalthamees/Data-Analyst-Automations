import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Sparkles, 
  TrendingUp, 
  Bot, 
  User, 
  RefreshCw,
  Lightbulb,
  AlertCircle
} from 'lucide-react';
import { ChatMessage, DatasetMeta } from '../../types';
import { ChatService, CleaningService } from '../../services/api';
import { ChartRenderer } from '../dashboard/ChartRenderer';

interface ChatInterfaceProps {
  activeDataset?: DatasetMeta;
  initialPrompt?: string;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  activeDataset,
  initialPrompt
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Quick preset questions with English & Tanglish support
  const quickPrompts = [
    { label: "Total sales & profit", query: "Show total sales and total profit." },
    { label: "Tamil: Total sales evlo?", query: "Total sales evlo?", badge: "Tanglish" },
    { label: "Profit margin", query: "Calculate profit margin without using Excel formulas." },
    { label: "Tamil: Month trend kaatu", query: "Month-wise sales trend kaatu.", badge: "Tanglish" },
    { label: "Top 10 products", query: "Find the top 10 products by revenue." },
    { label: "Tamil: Why profit dropped?", query: "Profit yen decrease aachu?", badge: "Tanglish" },
    { label: "Remove duplicates", query: "Find and remove duplicate records." },
    { label: "6-Month forecast", query: "Forecast sales for the next six months." },
    { label: "Unusual transactions", query: "Find unusual transactions." },
  ];

  useEffect(() => {
    // Initial welcome message
    if (messages.length === 0) {
      setMessages([
        {
          id: 'welcome_1',
          sender: 'assistant',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          text: `Hello! I am **DataPilot AI**, your autonomous Data Analyst. I perform real computations on **${activeDataset?.filename || 'your dataset'}** over DuckDB and verify every metric without hallucination. You can ask business questions in natural English or Tanglish.`,
          suggested_followups: [
            "Total sales evlo?",
            "Calculate profit margin without using Excel formulas",
            "Month-wise sales trend kaatu.",
            "Top 10 products eduthu kudu."
          ]
        }
      ]);
    }
  }, [activeDataset?.id]);

  useEffect(() => {
    if (initialPrompt) {
      handleSendQuery(initialPrompt);
    }
  }, [initialPrompt]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSendQuery = async (queryToSend?: string) => {
    const q = (queryToSend || inputValue).trim();
    if (!q || loading) return;

    const userMsg: ChatMessage = {
      id: `user_${Date.now()}`,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      text: q
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputValue('');
    setLoading(true);

    try {
      const resp = await ChatService.ask(q, 'session_main', activeDataset?.id);

      const assistantMsg: ChatMessage = {
        id: `ast_${Date.now()}`,
        sender: 'assistant',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        text: resp.summary || resp.title || "Computation finished.",
        kpis: resp.kpis || resp.kpi_cards,
        chart: resp.type === 'chart' ? {
          type: resp.chart_type || 'bar',
          title: resp.title || '',
          data: resp.chart_data || []
        } : undefined,
        narrative: resp.narrative,
        verification: resp.verification_trace,
        suggested_followups: resp.suggested_followups,
        requires_action: resp.requires_action,
        action_type: resp.action_type,
        cleaning_preview: resp.preview
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          sender: 'assistant',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          text: `Analysis error: ${err?.response?.data?.detail || err.message || "Failed to process analytical request."}`
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyDeduplication = async (msgId: string) => {
    if (!activeDataset) return;
    try {
      const res = await CleaningService.applyDuplicates(activeDataset.id);
      setMessages((prev) => [
        ...prev,
        {
          id: `dedup_${Date.now()}`,
          sender: 'assistant',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          text: `Duplicates successfully removed! Dataset updated from ${res.summary.before_rows.toLocaleString()} to ${res.summary.after_rows.toLocaleString()} records.`
        }
      ]);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] bg-[#09090b] text-[#f4f4f5]">
      {/* Quick Prompts Bar */}
      <div className="bg-[#101014] border-b border-[#222228] px-6 py-2.5 overflow-x-auto flex items-center space-x-2 scrollbar-none">
        <span className="text-[11px] font-bold text-zinc-400 uppercase tracking-wider whitespace-nowrap flex items-center space-x-1">
          <Lightbulb size={13} className="text-amber-400" />
          <span>Quick Prompts:</span>
        </span>
        {quickPrompts.map((p, idx) => (
          <button
            key={idx}
            onClick={() => handleSendQuery(p.query)}
            className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs bg-[#18181f] text-zinc-300 border border-[#2b2b35] hover:bg-[#22222c] hover:border-red-500/40 hover:text-white transition-all whitespace-nowrap"
          >
            <span>{p.label}</span>
            {p.badge && (
              <span className="text-[9px] px-1 rounded bg-red-950/60 text-red-400 border border-red-900/50">
                {p.badge}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Messages Feed */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6 max-w-4xl w-full mx-auto">
        {messages.map((msg) => {
          const isUser = msg.sender === 'user';
          return (
            <div
              key={msg.id}
              className={`flex items-start space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}
            >
              {/* Avatar */}
              <div
                className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 shadow-md ${
                  isUser
                    ? 'bg-zinc-800 text-zinc-200 border border-zinc-700'
                    : 'bg-gradient-to-tr from-red-600 to-rose-500 text-white shadow-red-500/10'
                }`}
              >
                {isUser ? <User size={16} /> : <Bot size={16} />}
              </div>

              {/* Message Bubble */}
              <div
                className={`max-w-[85%] rounded-2xl p-4.5 border ${
                  isUser
                    ? 'bg-[#18181d] text-white border-[#2b2b34] rounded-tr-none'
                    : 'bg-[#121216] text-zinc-200 border-[#222228] rounded-tl-none shadow-sm'
                }`}
              >
                <div className="text-xs text-zinc-400 mb-1 flex items-center justify-between">
                  <span className="font-semibold text-zinc-300">
                    {isUser ? 'You' : 'DataPilot AI Analyst'}
                  </span>
                  <span className="text-[10px] text-zinc-500">{msg.timestamp}</span>
                </div>

                {/* Primary Text Content */}
                <div className="text-sm leading-relaxed text-zinc-200 whitespace-pre-wrap">
                  {msg.text}
                </div>

                {/* KPI Cards inside response */}
                {msg.kpis && msg.kpis.length > 0 && (
                  <div className="mt-3 grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                    {msg.kpis.map((k, i) => (
                      <div
                        key={i}
                        className={`p-2.5 rounded-lg border text-center ${
                          k.highlight
                            ? 'bg-red-950/20 border-red-500/30'
                            : 'bg-[#18181e] border-[#292933]'
                        }`}
                      >
                        <div className="text-[11px] text-zinc-400 truncate">{k.label}</div>
                        <div className="text-base font-bold text-white tracking-tight mt-0.5">
                          {k.formatted_value}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Dynamic Chart inside response */}
                {msg.chart && msg.chart.data && msg.chart.data.length > 0 && (
                  <div className="mt-4 p-3 bg-[#0c0c0f] rounded-xl border border-[#26262f]">
                    <div className="text-xs font-bold text-white mb-2">{msg.chart.title}</div>
                    <ChartRenderer
                      type={msg.chart.type}
                      data={msg.chart.data}
                      xKey={msg.chart.x_key || 'name'}
                      yKeys={msg.chart.y_key ? [msg.chart.y_key] : ['value']}
                      playKey={msg.chart.play_key}
                      height={220}
                    />
                  </div>
                )}

                {/* Action Confirmation Button (e.g. Deduplication preview) */}
                {msg.requires_action && msg.action_type === 'confirm_deduplication' && (
                  <div className="mt-3 p-3 bg-red-950/20 border border-red-500/30 rounded-xl">
                    <div className="text-xs text-red-300 mb-2 font-medium">
                      Confirm Deduplication: Remove redundant rows permanently from this session?
                    </div>
                    <button
                      onClick={() => handleApplyDeduplication(msg.id)}
                      className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-red-600 hover:bg-red-500 text-white shadow-sm"
                    >
                      Confirm and Remove Duplicates
                    </button>
                  </div>
                )}

                {/* Executive Findings Accordion */}
                {msg.narrative && msg.narrative.what_happened && (
                  <div className="mt-3.5 pt-3 border-t border-[#23232b] text-xs space-y-1.5">
                    <div className="text-zinc-400">
                      <strong className="text-zinc-200">What Happened:</strong> {msg.narrative.what_happened}
                    </div>
                    {msg.narrative.risks_and_anomalies && (
                      <div className="text-zinc-400">
                        <strong className="text-zinc-200">Risks & Anomalies:</strong> {msg.narrative.risks_and_anomalies}
                      </div>
                    )}
                    {msg.narrative.recommended_actions && (
                      <div className="text-zinc-400">
                        <strong className="text-red-400">Next Action:</strong> {msg.narrative.recommended_actions}
                      </div>
                    )}
                  </div>
                )}

                {/* Suggested Follow-up Question Pills */}
                {msg.suggested_followups && msg.suggested_followups.length > 0 && (
                  <div className="mt-3 pt-2.5 border-t border-[#23232a] flex flex-wrap gap-1.5">
                    {msg.suggested_followups.map((fPrompt, i) => (
                      <button
                        key={i}
                        onClick={() => handleSendQuery(fPrompt)}
                        className="text-[11px] px-2 py-0.5 rounded-full bg-[#1c1c24] text-zinc-300 border border-[#2c2c38] hover:bg-[#252530] hover:text-white transition-all text-left"
                      >
                        + {fPrompt}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {loading && (
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-red-600/20 text-red-400 border border-red-500/30 flex items-center justify-center animate-pulse">
              <Bot size={16} />
            </div>
            <div className="bg-[#121216] border border-[#222228] rounded-2xl rounded-tl-none p-3.5 flex items-center space-x-2 text-xs text-zinc-400">
              <RefreshCw size={14} className="animate-spin text-red-500" />
              <span>Reviewing the selected dataset and preparing an answer...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div className="border-t border-[#222228] bg-[#0d0d10] p-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendQuery();
          }}
          className="max-w-4xl mx-auto flex items-center space-x-2 bg-[#141419] border border-[#272730] focus-within:border-red-500/50 rounded-xl px-3 py-1.5 shadow-lg transition-all"
        >
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask a question in English or Tanglish (e.g. 'Total sales evlo?', 'Top 10 products', 'Calculate profit margin')..."
            className="flex-1 bg-transparent text-sm text-white placeholder-zinc-500 focus:outline-none px-2 py-1.5"
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || loading}
            className="p-2 rounded-lg bg-red-600 hover:bg-red-500 disabled:opacity-40 disabled:hover:bg-red-600 text-white transition-all shadow-md shadow-red-500/20"
          >
            <Send size={15} />
          </button>
        </form>
      </div>
    </div>
  );
};
