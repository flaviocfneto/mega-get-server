import React, { useState, useEffect, useRef } from 'react';
import { 
  CloudDownload, 
  Plus, 
  Pause, 
  Play, 
  X, 
  History, 
  Terminal, 
  ChevronDown, 
  ChevronUp,
  Trash2,
  AlertCircle,
  CheckCircle2,
  Clock,
  RefreshCw,
  RotateCcw
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { Transfer, AppConfig } from './types';

export default function App() {
  const [url, setUrl] = useState('');
  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [history, setHistory] = useState<string[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [isLogExpanded, setIsLogExpanded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchConfig();
    fetchHistory();
    fetchLogs();
    
    const interval = setInterval(() => {
      fetchTransfers();
      fetchLogs();
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (isLogExpanded) {
      scrollToBottom();
    }
  }, [logs, isLogExpanded]);

  const scrollToBottom = () => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchConfig = async () => {
    try {
      const res = await fetch('/api/config');
      const data = await res.json();
      setConfig(data);
    } catch (err) {
      console.error('Failed to fetch config', err);
    }
  };

  const fetchTransfers = async () => {
    try {
      const res = await fetch('/api/transfers');
      const data = await res.json();
      setTransfers(data);
    } catch (err) {
      console.error('Failed to fetch transfers', err);
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await fetch('/api/history');
      const data = await res.json();
      setHistory(data);
    } catch (err) {
      console.error('Failed to fetch history', err);
    }
  };

  const fetchLogs = async () => {
    try {
      const res = await fetch('/api/logs');
      const data = await res.json();
      setLogs(data);
    } catch (err) {
      console.error('Failed to fetch logs', err);
    }
  };

  const handleDownload = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!url.trim()) return;

    setIsLoading(true);
    try {
      const res = await fetch('/api/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });
      if (res.ok) {
        setUrl('');
        fetchTransfers();
        fetchHistory();
      }
    } catch (err) {
      console.error('Download failed', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAction = async (tag: string, action: 'pause' | 'resume' | 'cancel' | 'retry') => {
    try {
      await fetch(`/api/transfers/${tag}/${action}`, { method: 'POST' });
      fetchTransfers();
    } catch (err) {
      console.error(`Failed to ${action} transfer ${tag}`, err);
    }
  };

  const handleCancelAll = async () => {
    try {
      await fetch('/api/transfers/cancel-all', { method: 'POST' });
      fetchTransfers();
    } catch (err) {
      console.error('Failed to cancel all transfers', err);
    }
  };

  const clearHistory = async () => {
    try {
      await fetch('/api/history', { method: 'DELETE' });
      setHistory([]);
    } catch (err) {
      console.error('Failed to clear history', err);
    }
  };

  const getStateColor = (state: string) => {
    switch (state) {
      case 'ACTIVE': return 'text-blue-400 bg-blue-400/10 border-blue-400/20';
      case 'QUEUED': return 'text-amber-400 bg-amber-400/10 border-amber-400/20';
      case 'PAUSED': return 'text-gray-400 bg-gray-400/10 border-gray-400/20';
      case 'RETRYING': return 'text-orange-400 bg-orange-400/10 border-orange-400/20';
      case 'COMPLETED': return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20';
      case 'FAILED': return 'text-rose-400 bg-rose-400/10 border-rose-400/20';
      default: return 'text-gray-400 bg-gray-400/10 border-gray-400/20';
    }
  };

  const getStateIcon = (state: string) => {
    switch (state) {
      case 'ACTIVE': return <RefreshCw className="w-3 h-3 animate-spin" />;
      case 'QUEUED': return <Clock className="w-3 h-3" />;
      case 'PAUSED': return <Pause className="w-3 h-3" />;
      case 'RETRYING': return <RefreshCw className="w-3 h-3" />;
      case 'COMPLETED': return <CheckCircle2 className="w-3 h-3" />;
      case 'FAILED': return <AlertCircle className="w-3 h-3" />;
      default: return null;
    }
  };

  const formatBytes = (bytes: number, decimals = 2) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-gray-100 font-sans selection:bg-blue-500/30">
      {/* Header */}
      <header className="border-b border-white/5 bg-black/20 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-blue-400 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
              <CloudDownload className="text-white w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white">MEGA Get</h1>
              <p className="text-[10px] uppercase tracking-widest text-gray-500 font-semibold">Cloud Download Manager</p>
            </div>
          </div>
          {config && (
            <div className="hidden md:flex items-center gap-6 text-xs text-gray-400">
              <div className="flex flex-col items-end">
                <span className="text-[10px] uppercase text-gray-600 font-bold">Download Path</span>
                <span className="font-mono">{config.download_dir}</span>
              </div>
            </div>
          )}
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Add Download Section */}
        <section className="mb-12">
          <div className="bg-gradient-to-b from-white/[0.05] to-transparent p-[1px] rounded-2xl">
            <div className="bg-[#121212] rounded-2xl p-6 shadow-2xl">
              <form onSubmit={handleDownload} className="flex flex-col md:flex-row gap-4">
                <div className="relative flex-1">
                  <input
                    type="text"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="Paste MEGA.nz export link here..."
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all placeholder:text-gray-600"
                  />
                </div>
                <button
                  type="submit"
                  disabled={isLoading || !url.trim()}
                  className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:hover:bg-blue-600 text-white font-semibold px-8 py-3.5 rounded-xl flex items-center justify-center gap-2 transition-all shadow-lg shadow-blue-600/20 active:scale-95"
                >
                  {isLoading ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Plus className="w-5 h-5" />}
                  Download
                </button>
              </form>
            </div>
          </div>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Active Transfers */}
          <div className="lg:col-span-2 space-y-6">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                Active Transfers
                <span className="bg-white/5 text-gray-400 text-[10px] px-2 py-0.5 rounded-full border border-white/10">
                  {transfers.length}
                </span>
              </h2>
              {transfers.some(t => ['ACTIVE', 'QUEUED', 'RETRYING'].includes(t.state)) && (
                <button 
                  onClick={handleCancelAll}
                  className="text-[10px] uppercase font-bold text-gray-500 hover:text-rose-400 flex items-center gap-1.5 transition-colors"
                >
                  <X className="w-3 h-3" />
                  Cancel All
                </button>
              )}
            </div>

            <div className="space-y-4">
              <AnimatePresence mode="popLayout">
                {transfers.length === 0 ? (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="bg-white/[0.02] border border-dashed border-white/10 rounded-2xl py-20 flex flex-col items-center justify-center text-gray-500"
                  >
                    <CloudDownload className="w-12 h-12 mb-4 opacity-20" />
                    <p className="text-sm">No active transfers</p>
                    <p className="text-xs opacity-60">Paste a URL above to start downloading</p>
                  </motion.div>
                ) : (
                  transfers.map((t) => (
                    <motion.div
                      key={t.tag}
                      layout
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.95 }}
                      className="bg-[#121212] border border-white/5 rounded-2xl p-5 hover:border-white/10 transition-colors group"
                    >
                      <div className="flex items-start justify-between gap-4 mb-4">
                        <div className="flex-1 min-w-0">
                          <h3 className="font-medium text-sm text-white truncate mb-1" title={t.filename}>
                            {t.filename}
                          </h3>
                          <div className="flex items-center gap-3 text-[11px] text-gray-500">
                            <span className="font-mono bg-white/5 px-1.5 py-0.5 rounded border border-white/5">#{t.tag}</span>
                            <span className="truncate max-w-[200px]">{t.path}</span>
                          </div>
                        </div>
                        <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[10px] font-bold uppercase tracking-wider ${getStateColor(t.state)}`}>
                          {getStateIcon(t.state)}
                          {t.state}
                        </div>
                      </div>

                      <div className="space-y-3">
                        <div className="flex items-center justify-between text-xs mb-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            {t.size_bytes === 0 ? (
                              <>
                                <span className="font-semibold text-white">{t.progress_pct}%</span>
                                <span className="text-gray-500">Unknown size</span>
                              </>
                            ) : (
                              <>
                                <span className="font-semibold text-white">
                                  {formatBytes(t.downloaded_bytes)}
                                </span>
                                <span className="text-gray-500">of {formatBytes(t.size_bytes)}</span>
                                <span className="text-blue-400 font-bold ml-1">({t.progress_pct}%)</span>
                              </>
                            )}
                          </div>
                          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            {(t.state === 'FAILED' || t.state === 'RETRYING') && (
                              <button 
                                onClick={() => handleAction(t.tag, 'retry')}
                                className="p-1.5 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white transition-colors"
                                title="Retry"
                              >
                                <RotateCcw className="w-4 h-4" />
                              </button>
                            )}
                            {t.state === 'PAUSED' ? (
                              <button 
                                onClick={() => handleAction(t.tag, 'resume')}
                                className="p-1.5 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white transition-colors"
                                title="Resume"
                              >
                                <Play className="w-4 h-4 fill-current" />
                              </button>
                            ) : t.state !== 'FAILED' && t.state !== 'RETRYING' && (
                              <button 
                                onClick={() => handleAction(t.tag, 'pause')}
                                className="p-1.5 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white transition-colors"
                                title="Pause"
                              >
                                <Pause className="w-4 h-4 fill-current" />
                              </button>
                            )}
                            <button 
                              onClick={() => handleAction(t.tag, 'cancel')}
                              className="p-1.5 hover:bg-rose-500/10 rounded-lg text-gray-400 hover:text-rose-400 transition-colors"
                              title="Cancel"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                        <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                          <motion.div 
                            className={`h-full rounded-full ${t.state === 'FAILED' ? 'bg-rose-500' : 'bg-blue-500'}`}
                            initial={{ width: 0 }}
                            animate={{ width: `${t.progress_pct}%` }}
                            transition={{ duration: 1, ease: "linear" }}
                          />
                        </div>
                      </div>
                      
                      {t.state === 'RETRYING' && t.progress_pct === 0 && (
                        <div className="mt-4 p-3 bg-orange-500/10 border border-orange-500/20 rounded-xl flex items-start gap-3">
                          <AlertCircle className="w-4 h-4 text-orange-400 shrink-0 mt-0.5" />
                          <p className="text-[11px] text-orange-200/70 leading-relaxed">
                            Stuck at 0%? Try <button onClick={() => handleAction(t.tag, 'resume')} className="text-orange-400 font-bold hover:underline">Resuming</button> or <button onClick={() => handleAction(t.tag, 'cancel')} className="text-orange-400 font-bold hover:underline">Restarting</button> the download.
                          </p>
                        </div>
                      )}
                    </motion.div>
                  ))
                )}
              </AnimatePresence>
            </div>
          </div>

          {/* Recent URLs */}
          <div className="space-y-6">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                Recent URLs
                <History className="w-4 h-4 text-gray-500" />
              </h2>
              {history.length > 0 && (
                <button 
                  onClick={clearHistory}
                  className="text-[10px] uppercase font-bold text-gray-500 hover:text-rose-400 flex items-center gap-1 transition-colors"
                >
                  <Trash2 className="w-3 h-3" />
                  Clear
                </button>
              )}
            </div>

            <div className="bg-[#121212] border border-white/5 rounded-2xl overflow-hidden">
              {history.length === 0 ? (
                <div className="p-8 text-center text-gray-600 text-sm italic">
                  No history yet
                </div>
              ) : (
                <div className="divide-y divide-white/5">
                  {history.map((h, i) => (
                    <button
                      key={i}
                      onClick={() => setUrl(h)}
                      className="w-full text-left p-4 hover:bg-white/[0.03] transition-colors group flex items-center justify-between gap-3"
                    >
                      <span className="text-xs text-gray-400 truncate group-hover:text-blue-400 transition-colors">
                        {h}
                      </span>
                      <Plus className="w-3 h-3 text-gray-600 group-hover:text-blue-400 shrink-0" />
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Collapsible Log */}
      <div className={`fixed bottom-0 left-0 right-0 z-40 transition-all duration-300 ease-in-out ${isLogExpanded ? 'h-64' : 'h-12'}`}>
        <div className="max-w-7xl mx-auto px-4 h-full">
          <div className="bg-[#1a1a1a] border-x border-t border-white/10 rounded-t-2xl h-full flex flex-col shadow-2xl">
            <button 
              onClick={() => setIsLogExpanded(!isLogExpanded)}
              className="flex items-center justify-between px-6 py-3 hover:bg-white/5 transition-colors shrink-0"
            >
              <div className="flex items-center gap-3">
                <Terminal className="w-4 h-4 text-blue-400" />
                <span className="text-xs font-bold uppercase tracking-widest text-gray-400">System Log</span>
              </div>
              {isLogExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
            </button>
            
            <div className={`flex-1 overflow-y-auto p-4 font-mono text-[11px] leading-relaxed text-gray-400 custom-scrollbar ${!isLogExpanded && 'hidden'}`}>
              {logs.map((log, i) => (
                <div key={i} className="mb-1 flex gap-3">
                  <span className="text-gray-600 shrink-0">[{new Date().toLocaleTimeString()}]</span>
                  <span className={log.toLowerCase().includes('error') ? 'text-rose-400' : ''}>{log}</span>
                </div>
              ))}
              <div ref={logEndRef} />
            </div>
          </div>
        </div>
      </div>

      <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.2);
        }
      `}</style>
    </div>
  );
}
