'use client';

import { useEffect, useState } from 'react';
import { Activity, Instagram, CheckCircle2, AlertCircle, Clock, Video } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

type BotState = {
    status: 'idle' | 'downloading' | 'uploading' | 'completed' | 'error';
    message: string;
    reelId?: string;
    sender?: string;
    updatedAt: string;
};

export default function Dashboard() {
    const [botState, setBotState] = useState<BotState | null>(null);
    const [loading, setLoading] = useState(true);

    const fetchStatus = async () => {
        try {
            const res = await fetch('/api/progress');
            if (res.ok) {
                const data = await res.json();
                setBotState(data);
            }
        } catch (err) {
            console.error('Failed to fetch bot status', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 3000); // Poll every 3 seconds
        return () => clearInterval(interval);
    }, []);

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'idle': return 'text-slate-400';
            case 'downloading': return 'text-blue-400';
            case 'uploading': return 'text-purple-400';
            case 'completed': return 'text-emerald-400';
            case 'error': return 'text-rose-400';
            default: return 'text-slate-400';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'idle': return <Clock className="w-6 h-6 text-slate-400" />;
            case 'downloading': return <Video className="w-6 h-6 text-blue-400 animate-pulse" />;
            case 'uploading': return <Activity className="w-6 h-6 text-purple-400 animate-bounce" />;
            case 'completed': return <CheckCircle2 className="w-6 h-6 text-emerald-400" />;
            case 'error': return <AlertCircle className="w-6 h-6 text-rose-400" />;
            default: return <Clock className="w-6 h-6 text-slate-400" />;
        }
    };

    return (
        <main className="max-w-4xl mx-auto p-6 md:p-12">
            <header className="flex items-center justify-between py-6 border-b border-white/10 mb-12">
                <div className="flex items-center gap-3">
                    <div className="p-3 bg-gradient-to-tr from-pink-500 to-orange-400 rounded-xl shadow-lg shadow-pink-500/20">
                        <Instagram className="w-6 h-6 text-white" />
                    </div>
                    <div>
                        <h1 className="text-2xl flex font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
                            Bot Dashboard
                        </h1>
                        <p className="text-sm text-slate-500">Live DM Repost Tracking</p>
                    </div>
                </div>

                <div className="flex items-center gap-2 px-4 py-2 bg-slate-900 border border-slate-800 rounded-full">
                    <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-sm font-medium text-slate-300">System Online</span>
                </div>
            </header>

            {loading ? (
                <div className="flex justify-center py-20">
                    <Activity className="w-8 h-8 text-slate-500 animate-spin" />
                </div>
            ) : (
                <AnimatePresence mode="popLayout">
                    <motion.div
                        key={botState?.updatedAt || 'empty'}
                        initial={{ opacity: 0, scale: 0.95, y: 10 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        className="w-full bg-slate-900/50 backdrop-blur-xl border border-white/5 rounded-3xl p-8 shadow-2xl overflow-hidden relative"
                    >
                        {/* Ambient Background Glow based on status */}
                        <div className={`absolute -top-32 -left-32 w-96 h-96 bg-opacity-20 blur-[100px] rounded-full pointer-events-none transition-colors duration-1000 ${botState?.status === 'uploading' ? 'bg-purple-500' :
                                botState?.status === 'downloading' ? 'bg-blue-500' :
                                    botState?.status === 'completed' ? 'bg-emerald-500' :
                                        botState?.status === 'error' ? 'bg-rose-500' : 'bg-slate-500'
                            }`} />

                        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center gap-8">
                            <div className="p-6 bg-slate-950 rounded-2xl border border-white/5 shadow-inner">
                                {getStatusIcon(botState?.status || 'idle')}
                            </div>

                            <div className="flex-1 min-w-0">
                                <h3 className="text-sm uppercase tracking-widest text-slate-500 font-semibold mb-2">Current Activity</h3>
                                <p className={`text-2xl md:text-3xl font-medium tracking-tight mb-2 truncate ${getStatusColor(botState?.status || 'idle')}`}>
                                    {botState?.message || 'Waiting for DMs...'}
                                </p>
                                <div className="flex items-center gap-4 text-sm text-slate-400">
                                    {botState?.sender && (
                                        <span className="flex items-center gap-1.5 bg-slate-800/50 px-3 py-1 rounded-md">
                                            Sender: <strong className="text-slate-200">@{botState.sender}</strong>
                                        </span>
                                    )}
                                    {botState?.reelId && (
                                        <span className="font-mono text-xs opacity-50">ID: {botState.reelId}</span>
                                    )}
                                </div>
                            </div>

                            <div className="text-right shrink-0">
                                <div className="text-xs font-mono text-slate-500 uppercase">Last Updated</div>
                                <div className="text-sm text-slate-300">
                                    {botState?.updatedAt ? new Date(botState.updatedAt).toLocaleTimeString() : '--:--:--'}
                                </div>
                            </div>
                        </div>

                        {botState?.status === 'uploading' && (
                            <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: '100%' }}
                                transition={{ duration: 15, ease: "linear" }}
                                className="absolute bottom-0 left-0 h-1 bg-gradient-to-r from-purple-500 to-pink-500"
                            />
                        )}

                        {botState?.status === 'downloading' && (
                            <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: '100%' }}
                                transition={{ duration: 5, ease: "easeOut" }}
                                className="absolute bottom-0 left-0 h-1 bg-gradient-to-r from-blue-500 to-cyan-400"
                            />
                        )}
                    </motion.div>
                </AnimatePresence>
            )}
        </main>
    );
}
