import React from 'react';
import { 
  X, 
  Mic, 
  Square, 
  Sparkles, 
  AlertTriangle, 
  TrendingUp, 
  Calendar, 
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  RefreshCw
} from 'lucide-react';
import { LiveWaveformBars } from '../voice/LiveWaveformBars';
import { ChatMessage, VoiceState } from '../../types';

interface AssistantDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  voiceState: VoiceState;
  audioLevel?: number;
  onToggleVoice: () => void;
  onSendMessage: (query: string) => void;
  messages: ChatMessage[];
}

export const AssistantDrawer: React.FC<AssistantDrawerProps> = ({
  isOpen,
  onClose,
  voiceState,
  audioLevel = 0,
  onToggleVoice,
  onSendMessage,
  messages,
}) => {
  if (!isOpen) return null;

  const isListening = voiceState === 'listening';
  const isSpeaking = voiceState === 'speaking';
  const isProcessing = voiceState === 'processing';
  const isVoiceActive = isListening || isSpeaking || isProcessing;

  const quickPrompts = [
    'Why did I spend ₹8,000 more this month?',
    'What are my upcoming bills?',
    'Can I afford a ₹25,000 purchase right now?',
    'Show my UPI spending breakdown',
  ];

  const recentAssistantMessage = [...messages].reverse().find((m) => m.sender === 'assistant');

  return (
    <div 
      role="dialog"
      aria-modal="true"
      aria-label="FinSight Voice Intelligence"
      className="fixed inset-y-0 right-0 z-50 w-full sm:w-96 bg-[#0C0B12] border-l border-white/[0.08] shadow-2xl flex flex-col justify-between overflow-hidden animate-in slide-in-from-right duration-200"
    >
      {/* 1. Header */}
      <div className="h-14 px-5 border-b border-white/[0.06] flex items-center justify-between flex-shrink-0 bg-[#0C0B12]">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-violet-600/20 border border-violet-500/30 flex items-center justify-center text-violet-400">
            <Sparkles className="w-3.5 h-3.5" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-white tracking-tight leading-none">
              Voice Intelligence
            </h3>
            <span className="text-[10px] text-emerald-400 flex items-center gap-1 mt-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>Engine Active</span>
            </span>
          </div>
        </div>

        <button
          onClick={onClose}
          aria-label="Close Intelligence Panel"
          className="w-7 h-7 rounded-lg bg-[#111018] border border-white/[0.08] hover:bg-white/[0.06] text-[#8E8B9A] hover:text-white flex items-center justify-center transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* 2. Scrollable Body */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {/* Voice Interaction Hero Box */}
        <div className="rounded-xl bg-[#111018] border border-violet-500/25 p-4 text-center relative overflow-hidden shadow-sm">
          {/* Subtle Ambient Violet Glow */}
          <div className="absolute inset-0 bg-gradient-to-b from-violet-600/10 to-transparent pointer-events-none" />

          {/* Voice Orb Button with Dynamic State */}
          <div className="relative flex flex-col items-center justify-center py-2">
            <button
              onClick={onToggleVoice}
              aria-label={isListening ? 'Stop listening' : 'Start speaking'}
              className={`relative w-16 h-16 rounded-full flex items-center justify-center transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-400 ${
                isListening
                  ? 'bg-rose-500 text-white shadow-[0_0_24px_rgba(244,63,94,0.6)] animate-pulse'
                  : isSpeaking
                  ? 'bg-gradient-to-tr from-violet-600 to-indigo-500 text-white shadow-[0_0_24px_rgba(139,92,246,0.6)]'
                  : 'bg-[#181628] border border-violet-400/40 text-violet-300 hover:border-violet-300 hover:bg-violet-900/30'
              }`}
            >
              {isListening ? (
                <Square className="w-5 h-5 fill-current" />
              ) : isProcessing ? (
                <RefreshCw className="w-5 h-5 animate-spin text-violet-300" />
              ) : (
                <Mic className="w-6 h-6" />
              )}
            </button>

            <span className="text-xs font-semibold text-white mt-3 block">
              {isListening
                ? 'Listening to your query...'
                : isProcessing
                ? 'Analyzing financial ledger...'
                : isSpeaking
                ? 'Speaking response...'
                : 'Tap to speak with FinSight'}
            </span>
            <span className="text-[10px] text-[#8E8B9A] block mt-0.5">
              {isListening ? 'Speak naturally in English or Hinglish' : 'Voice-first multi-turn intelligence'}
            </span>

            {/* Neon Cyan Live Waveform (Pinterest Reference) */}
            <div className="w-full mt-3 flex justify-center py-1">
              <LiveWaveformBars
                isActive={isVoiceActive}
                audioLevel={audioLevel}
                barCount={19}
                height={28}
                colorTheme="cyan"
              />
            </div>
          </div>
        </div>

        {/* Real-time Financial Anomaly Stream */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-white tracking-tight">Active Anomalies & Alerts</span>
            <span className="text-[10px] text-[#8E8B9A] font-mono">Real-time</span>
          </div>

          {/* Anomaly 1: Food & Dining Z-Score Alert */}
          <div className="rounded-lg bg-[#181520] border border-amber-500/25 p-3 flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-white">Food & Dining Spike</span>
                <span className="text-[9px] font-mono font-bold text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded">
                  Z +2.84
                </span>
              </div>
              <p className="text-[11px] text-[#8E8B9A] mt-0.5 leading-snug">
                Spent ₹14,200 vs. ₹8,400 90-day average. 14 food delivery orders via Swiggy & Zomato.
              </p>
            </div>
          </div>

          {/* Alert 2: Autopay Scheduled */}
          <div className="rounded-lg bg-[#111018] border border-white/[0.07] p-3 flex items-start gap-2.5">
            <Calendar className="w-4 h-4 text-violet-400 flex-shrink-0 mt-0.5" />
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-white">Scheduled CC Settlement</span>
                <span className="text-[9px] font-mono text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded">
                  Aug 30
                </span>
              </div>
              <p className="text-[11px] text-[#8E8B9A] mt-0.5 leading-snug">
                HDFC Credit Card autopay of ₹18,200 will be debited from Everyday Account.
              </p>
            </div>
          </div>
        </div>

        {/* Latest Assistant Explanation */}
        {recentAssistantMessage && (
          <div className="rounded-xl bg-[#141220] border border-violet-500/20 p-3.5 space-y-1.5">
            <div className="flex items-center gap-1.5 text-[11px] text-violet-300 font-semibold">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Latest Intelligence Brief</span>
            </div>
            <p className="text-xs text-[#EDEDEF] leading-relaxed">
              {recentAssistantMessage.text}
            </p>
          </div>
        )}

        {/* Quick Voice Question Prompts */}
        <div className="space-y-1.5 pt-1">
          <span className="text-[11px] font-bold text-[#8E8B9A] uppercase tracking-wider block mb-1">
            Suggested Inquiries
          </span>
          <div className="space-y-1.5">
            {quickPrompts.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => onSendMessage(prompt)}
                className="w-full text-left px-3 py-2 rounded-lg bg-[#111018] hover:bg-[#181628] border border-white/[0.07] hover:border-violet-500/35 text-xs text-[#EDEDEF] flex items-center justify-between transition-colors group"
              >
                <span className="truncate pr-2">{prompt}</span>
                <ArrowRight className="w-3 h-3 text-[#5C596C] group-hover:text-violet-400 flex-shrink-0 transition-colors" />
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 3. Footer Security Stamp */}
      <div className="p-3 bg-[#0C0B12] border-t border-white/[0.06] flex items-center justify-between text-[10px] text-[#5C596C]">
        <div className="flex items-center gap-1.5">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>Local Device Encryption</span>
        </div>
        <span>Gnani Engine v2.4</span>
      </div>
    </div>
  );
};
