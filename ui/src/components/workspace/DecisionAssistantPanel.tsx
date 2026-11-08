import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  BarChart2,
  ArrowRight,
  Mic,
  Paperclip,
  X,
  Zap,
} from 'lucide-react';
import {
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';
import type { AssistantMessage, IntelFeedItem, SimulationScenario } from '../../types';

// ─── Severity styling ─────────────────────────────────────────────────────────

const SEVERITY_COLORS: Record<IntelFeedItem['severity'], string> = {
  high: 'border-red-400 bg-red-50',
  medium: 'border-amber-400 bg-amber-50',
  low: 'border-blue-400 bg-blue-50',
};

const SEVERITY_BADGES: Record<IntelFeedItem['severity'], string> = {
  high: 'bg-red-100 text-red-700',
  medium: 'bg-amber-100 text-amber-700',
  low: 'bg-blue-100 text-blue-700',
};

// ─── Mini inline chart ────────────────────────────────────────────────────────

interface InlineChartProps {
  chartData: AssistantMessage['chart'];
}

const InlineChart: React.FC<InlineChartProps> = ({ chartData }) => {
  if (!chartData) return null;
  return (
    <div className="mt-2 border border-gray-200 rounded p-2 bg-white">
      <p className="text-xs font-medium text-gray-600 mb-1">{chartData.title}</p>
      <p className="text-xs text-gray-400 mb-2">Source: {chartData.source}</p>
      <ResponsiveContainer width="100%" height={80}>
        <AreaChart data={chartData.data} margin={{ top: 2, right: 4, left: -20, bottom: 2 }}>
          <defs>
            <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="year" tick={{ fontSize: 9, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
          <YAxis hide />
          <Tooltip
            contentStyle={{ fontSize: 11 }}
            formatter={(v: number) => [v.toFixed(1) + '%', '']}
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke="#3b82f6"
            fill="url(#chartGrad)"
            strokeWidth={1.5}
            dot={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

// ─── Chat message bubble ──────────────────────────────────────────────────────

const MessageBubble: React.FC<{ msg: AssistantMessage }> = ({ msg }) => {
  const isUser = msg.role === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] text-sm px-3 py-2 ${
          isUser
            ? 'bg-blue-600 text-white rounded-tl-2xl rounded-tr-sm rounded-bl-2xl'
            : 'bg-gray-100 text-gray-800 rounded-tl-sm rounded-tr-2xl rounded-bl-2xl'
        }`}
      >
        <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
        {msg.chart && <InlineChart chartData={msg.chart} />}
        <p className={`text-xs mt-1 ${isUser ? 'text-blue-200' : 'text-gray-400'}`}>
          {new Date(msg.ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>
    </div>
  );
};

// ─── Intel feed card ──────────────────────────────────────────────────────────

interface FeedCardProps {
  item: IntelFeedItem;
  onDismiss: (id: string) => void;
  onInvestigate: (item: IntelFeedItem) => void;
}

const FeedCard: React.FC<FeedCardProps> = ({ item, onDismiss, onInvestigate }) => (
  <div
    className={`border-l-4 rounded p-2.5 mb-2 ${SEVERITY_COLORS[item.severity]}`}
  >
    <div className="flex items-start justify-between gap-1 mb-1">
      <div className="flex items-center gap-1.5 flex-wrap">
        <span className={`text-xs font-semibold uppercase px-1.5 py-0.5 rounded ${SEVERITY_BADGES[item.severity]}`}>
          {item.severity}
        </span>
        <span className="text-xs font-semibold text-gray-800">{item.title}</span>
      </div>
      <button
        onClick={() => onDismiss(item.id)}
        className="text-gray-400 hover:text-gray-600 shrink-0"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
    <p className="text-xs text-gray-600 mb-1.5 leading-relaxed">{item.description}</p>
    <div className="flex items-center justify-between">
      <span className="text-xs text-gray-400 italic">{item.origin}</span>
      <button
        onClick={() => onInvestigate(item)}
        className="text-xs border border-blue-300 text-blue-600 hover:bg-blue-50 px-2 py-0.5 rounded"
      >
        Investigate
      </button>
    </div>
  </div>
);

// ─── Typing dots ──────────────────────────────────────────────────────────────

const TypingDots: React.FC = () => (
  <div className="flex justify-start">
    <div className="bg-gray-100 rounded-tl-sm rounded-tr-2xl rounded-bl-2xl px-3 py-2">
      <div className="flex gap-1 items-center h-4">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-bounce"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
    </div>
  </div>
);

// ─── Main Panel ───────────────────────────────────────────────────────────────

interface DecisionAssistantPanelProps {
  messages: AssistantMessage[];
  feedItems: IntelFeedItem[];
  onSendMessage: (content: string) => Promise<void>;
  onDismissFeedItem: (id: string) => void;
  onCheckItOut: () => void;
  isLoading: boolean;
  scenarios: SimulationScenario[] | null;
}

export const DecisionAssistantPanel: React.FC<DecisionAssistantPanelProps> = ({
  messages,
  feedItems,
  onSendMessage,
  onDismissFeedItem,
  onCheckItOut,
  isLoading,
}) => {
  const [activeTab, setActiveTab] = useState<'chat' | 'intel'>('chat');
  const [input, setInput] = useState('');
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || isLoading) return;
    setInput('');
    await onSendMessage(text);
  }, [input, isLoading, onSendMessage]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  const quickActions = ['Summarize results', 'Explain cost drivers', 'Compare scenarios', 'Investigate risks'];

  const activeFeedItems = feedItems.filter((f) => !f.dismissed);

  return (
    <div className="flex flex-col h-full border-l border-gray-200 bg-white overflow-hidden" style={{ width: '20%', minWidth: '260px' }}>
      {/* Header */}
      <div className="px-3 py-2 border-b border-gray-200 shrink-0">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1.5">
            <BarChart2 className="w-4 h-4 text-gray-500" />
            <span className="text-sm font-semibold text-gray-800">Financial Story</span>
          </div>
          <button
            onClick={onCheckItOut}
            className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded font-medium"
          >
            Check it Out
          </button>
        </div>
        {/* Tabs */}
        <div className="flex gap-1 bg-gray-100 rounded p-0.5">
          <button
            onClick={() => setActiveTab('chat')}
            className={`flex-1 text-xs py-1 rounded font-medium transition ${
              activeTab === 'chat' ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Chat
          </button>
          <button
            onClick={() => setActiveTab('intel')}
            className={`flex-1 text-xs py-1 rounded font-medium transition relative ${
              activeTab === 'intel' ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Intel Feed
            {activeFeedItems.length > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 text-xs bg-red-500 text-white rounded-full flex items-center justify-center">
                {activeFeedItems.length}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Chat Tab */}
      {activeTab === 'chat' && (
        <>
          <div className="flex-1 overflow-y-auto px-3 py-2 space-y-2">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} msg={msg} />
            ))}
            {isLoading && <TypingDots />}
            <div ref={chatEndRef} />
          </div>

          {/* Quick actions */}
          {!isLoading && (
            <div className="px-3 pb-2 flex flex-wrap gap-1 shrink-0">
              {quickActions.map((action) => (
                <button
                  key={action}
                  onClick={() => onSendMessage(action)}
                  className="text-xs border border-gray-300 text-gray-600 hover:bg-gray-50 px-2 py-0.5 rounded"
                >
                  {action}
                </button>
              ))}
            </div>
          )}

          {/* Composer */}
          <div className="border-t border-gray-200 p-2 shrink-0">
            <textarea
              rows={2}
              placeholder="Ask about this simulation…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              className="w-full text-sm border border-gray-300 rounded px-2 py-1 resize-none outline-none focus:ring-1 focus:ring-blue-500 text-gray-700 placeholder-gray-400 disabled:opacity-50"
            />
            <div className="flex items-center justify-between mt-1">
              <div className="flex gap-1">
                <button className="p-1 text-gray-400 hover:text-gray-600 rounded hover:bg-gray-100">
                  <Paperclip className="w-3.5 h-3.5" />
                </button>
                <button className="p-1 text-gray-400 hover:text-gray-600 rounded hover:bg-gray-100">
                  <Mic className="w-3.5 h-3.5" />
                </button>
              </div>
              <button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                className={`flex items-center gap-1 text-xs px-2.5 py-1 rounded font-medium transition ${
                  input.trim() && !isLoading
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                }`}
              >
                Send
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          </div>
        </>
      )}

      {/* Intel Feed Tab */}
      {activeTab === 'intel' && (
        <div className="flex-1 overflow-y-auto px-3 py-2">
          {activeFeedItems.length === 0 ? (
            <div className="text-center py-8 text-sm text-gray-400">
              <Zap className="w-6 h-6 mx-auto mb-2 text-gray-300" />
              No active intelligence items.
            </div>
          ) : (
            activeFeedItems.map((item) => (
              <FeedCard
                key={item.id}
                item={item}
                onDismiss={onDismissFeedItem}
                onInvestigate={(feedItem) => {
                  setActiveTab('chat');
                  onSendMessage(`Investigate: ${feedItem.title} — ${feedItem.description}`);
                }}
              />
            ))
          )}
        </div>
      )}
    </div>
  );
};



