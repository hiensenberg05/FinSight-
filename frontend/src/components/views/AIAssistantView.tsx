import React, { useState, useEffect, useRef } from 'react';
import { 
  BarChart2, 
  Target, 
  TrendingUp, 
  ArrowUp, 
  Activity, 
  Calendar,
  Sparkles,
  Square,
  AlertTriangle,
  ShieldCheck,
  ExternalLink,
  Send,
  Mic,
  Volume2,
  VolumeX,
  MessageSquare,
  Pause,
  Play
} from 'lucide-react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';
import { SoundOrbVisualizer } from '../voice/SoundOrbVisualizer';
import { LiveWaveformBars } from '../voice/LiveWaveformBars';
import { ActionConfirmationCard } from '../chat/ActionConfirmationCard';
import { InteractiveSimulationCard } from '../chat/InteractiveSimulationCard';
import { PortalEvidenceCard } from '../chat/PortalEvidenceCard';
import { SlackAlertCard } from '../chat/SlackAlertCard';
import { SpendingDonutChart } from '../chat/SpendingDonutChart';
import { useVoice } from '../../voice/VoiceContext';
import { api } from '../../services/api';
import { FinancialHealthMetrics, CategorySpending, Transaction, Bill } from '../../types';
import { formatINR, getTodayFormatted } from '../../utils/formatters';

interface AIAssistantViewProps {
  onSelectTab?: (tab: string) => void;
}

const FormattedMessage: React.FC<{ text: string; isStreaming?: boolean }> = ({ text, isStreaming }) => {
  if (!text) return null;

  // Split content into blocks: paragraph vs markdown table
  const lines = text.split('\n');
  const blocks: Array<{ type: 'text' | 'table'; content: string | string[] }> = [];
  let currentTable: string[] = [];
  let currentText: string[] = [];

  const flushText = () => {
    if (currentText.length > 0) {
      blocks.push({ type: 'text', content: currentText.join('\n') });
      currentText = [];
    }
  };
  const flushTable = () => {
    if (currentTable.length > 0) {
      blocks.push({ type: 'table', content: currentTable });
      currentTable = [];
    }
  };

  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
      flushText();
      currentTable.push(trimmed);
    } else {
      flushTable();
      currentText.push(line);
    }
  }
  flushText();
  flushTable();

  // Helper to parse bold text
  const renderInlineFormatted = (raw: string) => {
    const parts = raw.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="text-white font-bold">{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  // Helper to render status badges in tables
  const renderTableCell = (cell: string, isHeader: boolean) => {
    const clean = cell.trim();
    if (isHeader) return clean;

    const lower = clean.toLowerCase();
    if (lower.includes('over budget') || lower.includes('high surge') || lower.includes('anomaly') || lower.includes('outlier')) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30 whitespace-nowrap">
          {clean}
        </span>
      );
    }
    if (lower.includes('on track') || lower.includes('scheduled') || lower.includes('cash inflow') || lower.includes('surplus') || lower.includes('safe')) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 whitespace-nowrap">
          {clean}
        </span>
      );
    }
    if (lower.includes('cap recommended') || lower.includes('moderate pacing') || lower.includes('discretionary') || lower.includes('pending')) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 whitespace-nowrap">
          {clean}
        </span>
      );
    }
    const isCurrency = clean.includes('₹') || clean.includes('%') || /^[+-]?\d+(?:,\d+)*(?:\.\d+)?$/.test(clean);
    return (
      <span className={isCurrency ? 'font-mono font-semibold text-slate-100' : 'text-slate-300'}>
        {renderInlineFormatted(clean)}
      </span>
    );
  };

  return (
    <div className="space-y-2">
      {blocks.map((block, idx) => {
        if (block.type === 'text') {
          const rawText = block.content as string;
          const paragraphs = rawText.split(/\n\s*\n/).filter(p => p.trim().length > 0);
          return (
            <div key={idx} className="space-y-1.5">
              {paragraphs.map((p, pIdx) => (
                <p key={pIdx} className="text-[13px] text-[#E2E8F0] leading-relaxed whitespace-pre-line font-medium">
                  {renderInlineFormatted(p.trim())}
                  {isStreaming && idx === blocks.length - 1 && pIdx === paragraphs.length - 1 && (
                    <span className="inline-block w-1.5 h-3.5 bg-violet-400 ml-1 animate-pulse" />
                  )}
                </p>
              ))}
            </div>
          );
        }

        // Render Markdown Table
        const rows = block.content as string[];
        if (rows.length < 2) return null;

        const headerLine = rows[0];
        const dataLines = rows.slice(1).filter(r => !r.match(/^\|\s*[-:]+\s*\|/));
        const headers = headerLine.split('|').map(c => c.trim()).filter((_, i, arr) => i > 0 && i < arr.length);

        return (
          <div key={idx} className="w-full overflow-x-auto rounded-xl border border-white/[0.1] bg-black/40 backdrop-blur-md shadow-lg my-2 scrollbar-thin scrollbar-thumb-violet-600/40">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-white/[0.08] bg-white/[0.04]">
                  {headers.map((h, hIdx) => (
                    <th key={hIdx} className="py-2 px-3 text-[10.5px] font-bold uppercase tracking-wider text-violet-300">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.05]">
                {dataLines.map((row, rIdx) => {
                  const cells = row.split('|').map(c => c.trim()).filter((_, i, arr) => i > 0 && i < arr.length);
                  return (
                    <tr key={rIdx} className="hover:bg-white/[0.03] transition-colors">
                      {cells.map((cell, cIdx) => (
                        <td key={cIdx} className="py-2 px-3 text-[11.5px]">
                          {renderTableCell(cell, false)}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        );
      })}
    </div>
  );
};

export const AIAssistantView: React.FC<AIAssistantViewProps> = ({ onSelectTab }) => {
  const {
    voiceState,
    audioLevel,
    audioLevelSource,
    currentResponse,
    finalTranscript,
    interimTranscript,
    transcriptHistory,
    streamingText,
    isWsConnected,
    isContinuousMode,
    isMuted,
    isMicMuted,
    toggleMicMute,
    toggleMute,
    providerStatus,
    voiceError,
    currentEvidence,
    pendingAction,
    activeSimulation,
    activePortalEvidence,
    dismissPortalEvidence,
    openEvidenceDrawer,
    confirmActionProposal,
    cancelActionProposal,
    adjustSimulationSlider,
    toggleContinuousMode,
    isPlaybackPaused,
    togglePauseVoice,
    languageMode,
    setLanguageMode,
    voicePersona,
    setVoicePersona,
    detectedLanguage,
    processQuery,
    toggleListening,
    interruptSpeaking,
  } = useVoice();

  const [activeChip, setActiveChip] = useState<'spending' | 'budget' | 'investments' | null>(null);
  const [chatInput, setChatInput] = useState<string>('');
  const [inputMode, setInputMode] = useState<'voice' | 'text'>('voice');
  const chatBottomRef = useRef<HTMLDivElement>(null);

  // Real Database State
  const [healthMetrics, setHealthMetrics] = useState<FinancialHealthMetrics | null>(null);
  const [categories, setCategories] = useState<CategorySpending[]>([]);
  const [recentTxns, setRecentTxns] = useState<Transaction[]>([]);
  const [bills, setBills] = useState<Bill[]>([]);

  const isProcessing = voiceState === 'thinking' || voiceState === 'tool_execution';
  const isSpeaking = voiceState === 'speaking';
  const isListening = voiceState === 'listening';

  const handleChipClick = (chip: 'spending' | 'budget' | 'investments', promptText: string) => {
    setActiveChip(chip);
    processQuery(promptText);
  };

  const handleSendChat = () => {
    if (!chatInput.trim()) return;
    const text = chatInput.trim();
    setChatInput('');
    processQuery(text);
  };

  const handleOrbToggle = () => {
    if (isContinuousMode) toggleListening();
    else toggleContinuousMode();
  };

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcriptHistory, streamingText, finalTranscript]);

  const totalSpent = categories.reduce((sum, c) => sum + Math.abs(c.amount), 0);
  const nextBill = bills[0] || null;

  return (
    <div className="w-full max-w-4xl mx-auto min-h-full flex flex-col justify-between space-y-3 pb-2">
      {/* 2-COLUMN MAIN GRID */}
      <div className="grid grid-cols-1 gap-3.5 items-start">
        {/* LEFT MAIN COLUMN (8 of 12 cols) */}
        <div className="flex flex-col space-y-3">
          {/* 1. Hero Voice Greeting Area with Centered Orb & Inline Chips */}
          <div className="relative rounded-2xl glass-card-3d px-5 py-3 shadow-lg overflow-hidden">
            <div className="mb-2 flex flex-wrap items-center justify-between gap-2 pr-1">
              <h2 className="text-[26px] font-extrabold text-metallic-silver tracking-tight leading-tight">FinSight Voice</h2>
              <div className="flex items-center gap-2 text-[11px] text-[#A29DBE]" aria-label="Voice connection status">
                <i className={`h-2 w-2 rounded-full ${isWsConnected ? 'bg-emerald-400' : 'bg-amber-400'}`} />
                <span>{isWsConnected ? 'Voice ready' : 'Voice gateway offline'}</span>
                {providerStatus.tts_status === 'connected' && <span className="text-emerald-300">· Gnani voice ready</span>}
              </div>
            </div>

            <div>
              <div className="flex flex-wrap items-center gap-2 mt-1">
                <div className="px-1.5 py-0.5 rounded-md bg-gradient-to-r from-violet-600 to-indigo-600 border border-violet-400/40 flex items-center gap-0.5 shadow-[0_0_10px_rgba(109,79,255,0.4)]">
                  <span className="w-[2px] h-2 bg-white rounded-full" />
                  <span className="w-[2px] h-3 bg-white rounded-full" />
                  <span className="w-[2px] h-2 bg-white rounded-full" />
                </div>
                <span className="text-[13px] font-extrabold text-metallic-violet tracking-tight">
                  Voice Engine
                </span>

                {/* Gender choice maps to a language-matched Gnani Timbre voice. */}
                <div className="flex items-center rounded-full bg-white/[0.06] border border-white/10 p-0.5 shadow-inner" title="Dynamic Indian Voice Persona">
                  <button
                    onClick={() => setVoicePersona('Nalini')}
                    className={`px-2 py-0.5 rounded-full text-[10.5px] font-bold transition-all ${
                      voicePersona === 'Nalini'
                        ? 'bg-violet-600 text-white shadow-[0_0_8px_rgba(124,58,237,0.5)]'
                        : 'text-[#8E8AA5] hover:text-white'
                    }`}
                  >
                    Female voice
                  </button>
                  <button
                    onClick={() => setVoicePersona('Deepak')}
                    className={`px-2 py-0.5 rounded-full text-[10.5px] font-bold transition-all ${
                      voicePersona === 'Deepak'
                        ? 'bg-violet-600 text-white shadow-[0_0_8px_rgba(124,58,237,0.5)]'
                        : 'text-[#8E8AA5] hover:text-white'
                    }`}
                  >
                    Male voice
                  </button>
                </div>

                {/* Language Mode Selector (Auto / EN / HI) */}
                <div className="flex items-center rounded-full bg-white/[0.06] border border-white/10 p-0.5 shadow-inner" title="Voice & Speech Language">
                  <button
                    onClick={() => setLanguageMode('auto')}
                    className={`px-2 py-0.5 rounded-full text-[10.5px] font-bold transition-all ${
                      languageMode === 'auto'
                        ? 'bg-cyan-600 text-white shadow-[0_0_8px_rgba(8,145,178,0.5)]'
                        : 'text-[#8E8AA5] hover:text-white'
                    }`}
                  >
                    Auto
                  </button>
                  <button
                    onClick={() => setLanguageMode('en')}
                    className={`px-2 py-0.5 rounded-full text-[10.5px] font-bold transition-all ${
                      languageMode === 'en'
                        ? 'bg-indigo-600 text-white shadow-[0_0_8px_rgba(79,70,229,0.5)]'
                        : 'text-[#8E8AA5] hover:text-white'
                    }`}
                  >
                    English
                  </button>
                  <button
                    onClick={() => setLanguageMode('hi')}
                    className={`px-2 py-0.5 rounded-full text-[10.5px] font-bold transition-all ${
                      languageMode === 'hi'
                        ? 'bg-emerald-600 text-white shadow-[0_0_8px_rgba(16,185,129,0.5)]'
                        : 'text-[#8E8AA5] hover:text-white'
                    }`}
                  >
                    हिंदी
                  </button>
                  <button onClick={() => setLanguageMode('hinglish')} aria-pressed={languageMode === 'hinglish'} className={`px-2 py-0.5 rounded-full text-[10.5px] font-bold ${languageMode === 'hinglish' ? 'bg-cyan-700 text-white' : 'text-[#8E8AA5] hover:text-white'}`}>Hinglish</button>
                </div>

                <button
                  onClick={toggleContinuousMode}
                  className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border text-[11px] font-bold transition-all active:scale-95 shadow-sm ${
                    isContinuousMode
                      ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300 shadow-[0_0_10px_rgba(16,185,129,0.25)]'
                      : 'bg-white/[0.05] border-white/20 text-[#8E8AA5] hover:text-white'
                  }`}
                  title="Open a live voice session. FinSight will listen again after each reply."
                  aria-pressed={isContinuousMode}
                >
                  <span className={`w-1.5 h-1.5 rounded-full ${isContinuousMode ? 'bg-emerald-400 animate-pulse' : 'bg-gray-400'}`} />
                  <span>{isContinuousMode ? 'End live voice' : 'Live voice'}</span>
                </button>
                {isSpeaking && (
                  <button
                    onClick={interruptSpeaking}
                    className="flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-rose-500/20 border border-rose-500/40 text-rose-300 text-[11px] font-bold hover:bg-rose-500/30 transition-all active:scale-95 shadow-[0_0_10px_rgba(244,63,94,0.3)] animate-pulse"
                  >
                    <Square className="w-2.5 h-2.5 fill-current" />
                    <span>Interrupt (Barge-In)</span>
                  </button>
                )}
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <span className="text-[11px] text-[#8E8AA5]">Input</span>
                <button type="button" onClick={() => setInputMode('voice')} aria-pressed={inputMode === 'voice'} className={`min-h-10 rounded-lg border px-3 text-xs ${inputMode === 'voice' ? 'border-violet-400/50 bg-violet-500/15 text-white' : 'border-white/10 text-[#A29DBE]'}`}>Voice</button>
                <button type="button" onClick={() => setInputMode('text')} aria-pressed={inputMode === 'text'} className={`min-h-10 rounded-lg border px-3 text-xs ${inputMode === 'text' ? 'border-violet-400/50 bg-violet-500/15 text-white' : 'border-white/10 text-[#A29DBE]'}`}>Text</button>
                {inputMode === 'voice' && <button type="button" onClick={toggleMicMute} aria-pressed={isMicMuted} className="min-h-10 rounded-lg border border-white/10 px-3 text-xs text-[#D2CFE8]">{isMicMuted ? 'Unmute microphone' : 'Mute microphone'}</button>}
                <button type="button" onClick={toggleMute} aria-pressed={isMuted} className="min-h-10 rounded-lg border border-white/10 px-3 text-xs text-[#D2CFE8]">{isMuted ? 'Unmute audio' : 'Mute audio'}</button>
                {isSpeaking && <button type="button" onClick={interruptSpeaking} className="min-h-10 rounded-lg border border-rose-400/40 px-3 text-xs text-rose-200">Stop speaking</button>}
              </div>
              {voiceError && <div role="alert" className="mt-2 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-200"><span>{voiceError}</span><button type="button" onClick={() => setInputMode('text')} className="min-h-9 underline underline-offset-2">Switch to typing</button></div>}
              {(interimTranscript || finalTranscript) && inputMode === 'voice' && <p aria-live="polite" className="mt-2 text-sm text-slate-200">{interimTranscript || finalTranscript}</p>}
              <p className="text-[12px] text-[#8E8AA5] mt-0.5">
                {isContinuousMode ? (
                  <span className="text-emerald-400/90 font-medium">
                    Live voice is on. Speak naturally; tap the orb to pause listening.
                  </span>
                ) : (
                  <span>Ask by voice or text. Your conversation remains available when you switch modes.</span>
                )}
              </p>
            </div>

            {/* Action Chips + Orb */}
            <div className="flex items-center justify-between gap-2 mt-1">
              <div className="flex items-center gap-2 z-10 flex-shrink-0">
                <button
                  onClick={() =>
                    handleChipClick(
                      'spending',
                      languageMode === 'hi'
                        ? 'Mera kharcha kahan hua?'
                        : 'Show me my spending breakdown for this month'
                    )
                  }
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-[11.5px] font-medium transition-all shadow-sm active:scale-95 whitespace-nowrap glass-card-3d glass-card-3d-interactive ${
                    activeChip === 'spending'
                      ? 'border-violet-500/70 text-white shadow-[0_0_14px_rgba(109,79,255,0.4)]'
                      : 'border-white/[0.12] hover:border-violet-500/40 text-[#D2CFE8]'
                  }`}
                >
                  <BarChart2 className="w-3.5 h-3.5 text-violet-400" />
                  <span>{languageMode === 'hi' ? 'खर्चा Breakdown' : 'Spending Breakdown'}</span>
                </button>

                <button
                  onClick={() =>
                    handleChipClick(
                      'budget',
                      languageMode === 'hi'
                        ? 'Mera kharch kyu badha?'
                        : 'Why did my spending change?'
                    )
                  }
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-[11.5px] font-medium transition-all shadow-sm active:scale-95 whitespace-nowrap glass-card-3d glass-card-3d-interactive ${
                    activeChip === 'budget'
                      ? 'border-violet-500/70 text-white shadow-[0_0_14px_rgba(109,79,255,0.4)]'
                      : 'border-white/[0.12] hover:border-violet-500/40 text-[#D2CFE8]'
                  }`}
                >
                  <Target className="w-3.5 h-3.5 text-cyan-400" />
                  <span>{languageMode === 'hi' ? 'खर्च क्यों बढ़ा?' : 'Why Did Spend Increase?'}</span>
                </button>
              </div>

              {/* Centered Sound Orb */}
              <div className="flex flex-col items-center justify-center flex-shrink-0">
                <SoundOrbVisualizer
                  voiceState={voiceState}
                  audioLevel={audioLevel}
                  onToggle={handleOrbToggle}
                  idleLabel={isContinuousMode ? 'Tap to resume' : 'Start live voice'}
                />
                <LiveWaveformBars isActive={audioLevelSource === 'microphone' || audioLevelSource === 'playback'} audioLevel={audioLevel} height={18} barCount={21} className="h-5" />
                    <span className="text-[10px] text-[#77728F]">{audioLevelSource === 'microphone' ? 'Microphone level' : audioLevelSource === 'playback' ? 'Gnani playback level' : audioLevelSource === 'unavailable' ? 'Audio level unavailable' : isContinuousMode ? 'Live conversation' : 'Tap for live conversation'}</span>
              </div>

              <div className="flex items-center z-10 flex-shrink-0">
                <button
                  onClick={() =>
                    handleChipClick(
                      'investments',
                      languageMode === 'hi'
                        ? 'Koi unusual transactions hai kya?'
                        : 'Are there any anomalies or irregular charges?'
                    )
                  }
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-[11.5px] font-medium transition-all shadow-sm active:scale-95 whitespace-nowrap glass-card-3d glass-card-3d-interactive ${
                    activeChip === 'investments'
                      ? 'border-violet-500/70 text-white shadow-[0_0_14px_rgba(109,79,255,0.4)]'
                      : 'border-white/[0.12] hover:border-violet-500/40 text-[#D2CFE8]'
                  }`}
                >
                  <TrendingUp className="w-3.5 h-3.5 text-pink-400" />
                  <span>{languageMode === 'hi' ? 'Anomalies Check' : 'Check Anomalies'}</span>
                </button>
              </div>
            </div>
          </div>

          {/* 2. Full Conversation Lookup / Chat History Thread */}
          <div className="rounded-2xl glass-card-3d border border-violet-500/25 p-4 shadow-xl backdrop-blur-2xl flex flex-col space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-white/[0.08]">
              <div className="flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-violet-400" />
                <h3 className="text-sm font-bold text-white tracking-tight">Conversation</h3>
              </div>
              <div className="flex items-center gap-2">
                {(isSpeaking || isPlaybackPaused) && (
                  <button
                    onClick={togglePauseVoice}
                    className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition-all ${
                      isPlaybackPaused
                        ? 'bg-amber-500/20 border-amber-500/40 text-amber-300 hover:bg-amber-500/30'
                        : 'bg-violet-600/30 border-violet-400/40 text-violet-200 hover:bg-violet-600/40'
                    }`}
                    title={isPlaybackPaused ? 'Resume assistant speech' : 'Pause assistant speech'}
                  >
                    {isPlaybackPaused ? <Play className="w-3.5 h-3.5" /> : <Pause className="w-3.5 h-3.5" />}
                    <span>{isPlaybackPaused ? 'Resume' : 'Pause'}</span>
                  </button>
                )}
                <button
                  onClick={toggleMute}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition-all ${
                    isMuted
                      ? 'bg-rose-500/20 border-rose-500/40 text-rose-300'
                      : 'bg-white/[0.04] border-white/[0.1] text-violet-300 hover:text-white'
                  }`}
                  title="Toggle assistant voice audio output"
                >
                  {isMuted ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
                  <span>{isMuted ? 'Muted' : 'Voice ON'}</span>
                </button>
              </div>
            </div>

            {/* Scrollable messages container */}
            <div className="max-h-[380px] overflow-y-auto space-y-3 pr-1.5 scrollbar-thin scrollbar-thumb-violet-600/40">
              {/* Past completed turns */}
              {[...transcriptHistory].reverse().map((turn) => (
                <div key={turn.id} className="space-y-2">
                  {/* User Prompt */}
                  <div className="flex justify-end">
                    <div className="max-w-[85%] rounded-2xl rounded-tr-sm glass-card-3d border-violet-500/40 px-4 py-2 shadow-lg text-right">
                      <div className="flex items-center justify-end gap-1.5 text-[9.5px] uppercase font-bold tracking-wider text-violet-300 mb-0.5">
                        <span>You</span>
                        <span>·</span>
                        <span>{turn.timestamp}</span>
                      </div>
                      <p className="text-[13px] font-semibold text-metallic-silver leading-snug">
                        "{turn.userQuery}"
                      </p>
                    </div>
                  </div>

                  {/* Assistant Response */}
                  <div className="rounded-2xl glass-card-3d border border-white/[0.08] p-3 shadow-md space-y-2">
                    <div className="flex items-start gap-2.5">
                      <div className="w-7 h-7 rounded-xl bg-violet-600/30 border border-violet-400/40 text-violet-200 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-md">
                        <Sparkles className="w-3.5 h-3.5" />
                      </div>
                      <div className="min-w-0 flex-1 space-y-2">
                        <FormattedMessage text={turn.assistantResponse} />

                        {/* Relative Generative Visual Chart / Plot */}
                        {turn.chartData && turn.chartData.length > 0 && (
                          <div className="w-full mt-2.5">
                            <SpendingDonutChart
                              data={turn.chartData}
                              title={turn.chartTitle}
                            />
                          </div>
                        )}

                        {turn.followUpQuestions && turn.followUpQuestions.length > 0 && (
                          <div className="flex flex-wrap items-center gap-2 pt-1" aria-label="Suggested follow-up questions">
                            {turn.followUpQuestions.map((question) => (
                              <button key={question} type="button" onClick={() => processQuery(question)} className="min-h-10 rounded-lg border border-violet-400/25 px-3 text-[11px] text-violet-200 hover:bg-violet-500/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-violet-400">{question}</button>
                            ))}
                          </div>
                        )}

                        {/* Provenance Badge */}
                        {turn.evidence && turn.evidence.length > 0 && (
                          <div className="pt-1.5 flex items-center justify-between">
                            <button
                              onClick={() => openEvidenceDrawer(turn.evidence)}
                              className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-emerald-300 bg-emerald-500/15 hover:bg-emerald-500/25 border border-emerald-500/30 px-3 py-1 rounded-full transition-all cursor-pointer shadow-sm"
                            >
                              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                              <span>Verified from {turn.evidence.length} ledger transactions</span>
                              <ExternalLink className="w-2.5 h-2.5 opacity-60 ml-0.5" />
                            </button>
                            <span className="text-[10px] text-slate-400 font-mono">Relational SQL Grounding</span>
                          </div>
                        )}

                        {/* Action Proposal Card */}
                        {turn.actionProposal && (
                          <ActionConfirmationCard
                            proposal={turn.actionProposal}
                            onConfirm={confirmActionProposal}
                            onCancel={cancelActionProposal}
                          />
                        )}

                        {/* Simulation Card */}
                        {turn.simulationData && (
                          <InteractiveSimulationCard
                            initialData={turn.simulationData}
                            onSliderChange={adjustSimulationSlider}
                          />
                        )}

                        {/* Autonomous Portal Evidence Card */}
                        {turn.portalEvidence && (
                          <PortalEvidenceCard
                            evidence={turn.portalEvidence}
                          />
                        )}

                        {/* Autonomous Slack Alert Card */}
                        {(turn.slackAlert || turn.toolUsed === 'dispatch_slack_alert') && (
                          <SlackAlertCard
                            data={turn.slackAlert || {
                              channel: '#engineering-inventory-tracker',
                              workspace: 'accounting',
                              alert_type: 'test',
                              slack_url: 'https://app.slack.com/client/T09MCF0UERJ/C09M5ETUMPF',
                              dm_url: 'https://app.slack.com/client/T09MCF0UERJ/D0CFWN1310F',
                              status: 'delivered',
                            }}
                          />
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}

              {/* Current in-flight turn if processing or streaming */}
              {(isProcessing || (streamingText && !transcriptHistory.some(h => h.assistantResponse === streamingText))) && (
                <div className="space-y-2">
                  {finalTranscript && (
                    <div className="flex justify-end">
                      <div className="max-w-[85%] rounded-2xl rounded-tr-sm glass-card-3d border-violet-500/40 px-4 py-2 shadow-lg text-right">
                        <span className="text-[10px] uppercase font-bold tracking-wider text-violet-300 block">You</span>
                        <p className="text-[13px] font-semibold text-metallic-silver leading-snug mt-0.5">"{finalTranscript}"</p>
                      </div>
                    </div>
                  )}

                  {/* Assistant Streaming Bubble */}
                  <div className="rounded-2xl glass-card-3d border border-violet-500/35 p-3.5 shadow-xl relative backdrop-blur-2xl">
                    <div className="flex items-start gap-2.5">
                      <div className="w-7 h-7 rounded-xl bg-violet-600/30 border border-violet-400/40 text-violet-200 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-md">
                        <Sparkles className="w-3.5 h-3.5" />
                      </div>
                      <div className="min-w-0 flex-1">
                        {isProcessing && !streamingText ? (
                          <div className="flex items-center gap-2 text-[12.5px] text-violet-300">
                            <span className="w-2 h-2 rounded-full bg-violet-400 animate-ping" />
                            <span>{voiceState === 'tool_execution' ? 'Retrieving the requested financial data…' : 'Preparing your answer…'}</span>
                          </div>
                        ) : (
                          <div>
                            <FormattedMessage text={streamingText} isStreaming={isSpeaking} />
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Live Operational Action Proposal Card */}
              {pendingAction && (
                <ActionConfirmationCard
                  proposal={pendingAction}
                  onConfirm={confirmActionProposal}
                  onCancel={cancelActionProposal}
                />
              )}

              {/* Live Predictive Advisory What-If Simulation Card */}
              {activeSimulation && (
                <InteractiveSimulationCard
                  initialData={activeSimulation}
                  onSliderChange={adjustSimulationSlider}
                />
              )}

              {/* Live Autonomous Portal Forensic Evidence Card */}
              {activePortalEvidence && (
                <PortalEvidenceCard
                  evidence={activePortalEvidence}
                  onDismiss={dismissPortalEvidence}
                />
              )}

              <div ref={chatBottomRef} />
            </div>

            {/* Text entry remains in the same conversation when the user changes modes. */}
            {inputMode === 'text' ? (
              <form onSubmit={(event) => { event.preventDefault(); handleSendChat(); }} className="pt-2 border-t border-white/[0.08] flex items-center gap-2">
                <label htmlFor="assistant-question" className="sr-only">Ask FinSight a question</label>
                <input
                  id="assistant-question"
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder={languageMode === 'hi' ? 'अपना सवाल लिखें' : 'Write a question about your finances'}
                  className="min-h-11 w-full min-w-0 rounded-xl bg-white/[0.04] border border-white/[0.12] focus:border-violet-500/60 focus:bg-white/[0.07] px-3.5 py-2.5 text-sm text-white placeholder-[#8E8AA5] transition-all focus:outline-none shadow-inner"
                />
                <button type="submit" disabled={!chatInput.trim()} className="flex min-h-11 min-w-11 items-center justify-center rounded-xl bg-violet-600 hover:bg-violet-500 disabled:opacity-30 text-white transition-all" aria-label="Send question">
                  <Send className="w-4 h-4" />
                </button>
              </form>
            ) : (
              <div className="pt-2 border-t border-white/[0.08] flex items-center justify-between gap-3">
                <span className="text-xs text-[#8E8AA5]">{isListening ? 'Speak now; your transcript appears above.' : isProcessing ? 'The assistant is working on this turn.' : isSpeaking ? 'The answer is playing.' : 'Voice input is ready when you are.'}</span>
                <button type="button" onClick={toggleListening} disabled={isMicMuted || isProcessing} className="min-h-11 min-w-11 rounded-full bg-violet-600 px-4 text-sm font-semibold text-white disabled:opacity-40" aria-label={isListening ? 'Stop listening' : 'Start speaking'}>{isListening ? 'Finish' : 'Speak'}</button>
              </div>
            )}
          </div>

            {/* Split Two Cards Row: Real Spending Breakdown + Real Database Transactions */}
            <div className="hidden grid-cols-1 md:grid-cols-2 gap-3.5 items-start">
              {/* Card 1: Real Database Category Breakdown Donut */}
              <div className="rounded-2xl glass-card-3d glass-card-3d-interactive p-4 shadow-sm flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-[14px] font-extrabold text-metallic-silver tracking-tight">
                      Spending Breakdown
                    </h3>
                    <span className="text-[11px] font-medium text-[#8E8AA5]">
                      {healthMetrics?.period || 'Period unavailable'}
                    </span>
                  </div>

                  <div className="flex items-center justify-between gap-3 py-1">
                    <div className="relative w-28 h-28 flex items-center justify-center flex-shrink-0">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={categories}
                            dataKey="amount"
                            nameKey="name"
                            cx="50%"
                            cy="50%"
                            innerRadius={34}
                            outerRadius={48}
                            paddingAngle={3}
                            cornerRadius={4}
                            stroke="rgba(0,0,0,0.3)"
                            strokeWidth={1}
                            isAnimationActive={false}
                          >
                            {categories.map((entry, index) => (
                              <Cell key={`donut-${index}`} fill={entry.color || '#8B5CF6'} />
                            ))}
                          </Pie>
                          <Tooltip
                            content={({ active, payload }) => {
                              if (active && payload && payload.length) {
                                const data = payload[0].payload as CategorySpending;
                                return (
                                  <div className="glass-card-3d border border-white/[0.15] p-2 rounded-lg text-xs text-white shadow-xl">
                                    <p className="font-semibold text-white">{data.name}</p>
                                    <p className="text-metallic-violet font-extrabold tabular-nums">{formatINR(data.amount)} ({data.percentage}%)</p>
                                  </div>
                                );
                              }
                              return null;
                            }}
                          />
                        </PieChart>
                      </ResponsiveContainer>

                      <div className="absolute inset-4 rounded-full glass-inset-tray flex flex-col items-center justify-center pointer-events-none border border-white/[0.08]">
                        <span className="text-[12px] font-extrabold text-metallic-silver tabular-nums leading-none">
                          {categories.length ? formatINR(totalSpent) : '—'}
                        </span>
                        <span className="text-[8.5px] font-medium text-[#8E8AA5] mt-0.5 uppercase tracking-wider">
                          Total
                        </span>
                      </div>
                    </div>

                    {/* Category List from Database */}
                    <div className="space-y-1.5 flex-1 text-[11px]">
                      {categories.slice(0, 5).map((cat) => (
                        <div key={cat.name} className="flex items-center justify-between glass-card-3d px-2 py-1 rounded-lg">
                          <div className="flex items-center gap-1.5 truncate">
                            <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ backgroundColor: cat.color || '#8B5CF6' }} />
                            <span className="text-[#C8C5DC] truncate font-medium">{cat.name}</span>
                          </div>
                          <span className="text-[#8E8AA5] font-semibold tabular-nums ml-2">
                            {cat.percentage}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="pt-2 border-t border-white/[0.06] flex items-center justify-between text-[11px] text-emerald-400 font-semibold">
                  <span>Category totals from the returned data</span>
                </div>
              </div>

              {/* Card 2: Real Database Recent Transactions */}
              <div className="rounded-2xl glass-card-3d glass-card-3d-interactive p-4 shadow-sm flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-[14px] font-extrabold text-metallic-silver tracking-tight">
                      Recent Transactions
                    </h3>
                    <button
                      onClick={() => onSelectTab?.('transactions')}
                      className="text-[11px] text-violet-400 hover:text-violet-300 font-medium transition-colors"
                    >
                      View transactions
                    </button>
                  </div>

                  <div className="space-y-1.5">
                    {recentTxns.map((tx) => (
                      <div 
                        key={tx.id}
                        className="flex items-center justify-between py-1.5 border-b border-white/[0.04] last:border-0"
                      >
                        <div className="flex items-center gap-2.5">
                          <div className="w-7 h-7 rounded-xl bg-violet-600/30 text-violet-200 font-bold text-[11px] flex items-center justify-center shadow-md flex-shrink-0 border-t border-white/[0.2] border-b border-black/40">
                            {tx.merchant ? tx.merchant[0] : 'T'}
                          </div>
                          <div>
                            <div className="flex items-center gap-1.5">
                              <span className="text-[12.5px] font-semibold text-white block leading-tight">
                                {tx.merchant}
                              </span>
                              {tx.isAnomaly && (
                                <span className="flex items-center gap-0.5 text-[9.5px] font-bold text-amber-300 bg-amber-500/20 border border-amber-500/40 px-1 py-0.2 rounded">
                                  <AlertTriangle className="w-2.5 h-2.5" />
                                  <span>AI Flag</span>
                                </span>
                              )}
                            </div>
                            <span className="text-[10.5px] text-[#8E8AA5] block mt-0.5">
                              {tx.category} · {tx.dateStr || tx.date}
                            </span>
                          </div>
                        </div>
                        <span className={`text-[12.5px] font-bold tabular-nums text-right ${tx.amount > 0 ? 'text-emerald-400' : 'text-metallic-silver'}`}>
                          {tx.amount > 0 ? `+${formatINR(tx.amount)}` : formatINR(tx.amount)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

        {/* RIGHT RAIL (4 of 12 cols) */}
        <div className="hidden flex-col space-y-3 items-stretch">
          {/* Card 1: Next Upcoming Bill from Database */}
          {nextBill && <div className="rounded-2xl glass-card-3d glass-card-3d-interactive p-3.5 flex items-center gap-3 shadow-sm">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-b from-violet-600/30 to-violet-950/50 border-t border-violet-400/40 border-b border-black/40 flex items-center justify-center text-violet-300 flex-shrink-0 shadow-md">
              <Calendar className="w-4 h-4" />
            </div>
            <div className="min-w-0 flex-1">
              <h4 className="text-[13.5px] font-extrabold text-metallic-silver tracking-tight leading-tight">
                {getTodayFormatted()}
              </h4>
              <p className="text-[11.5px] text-metallic-violet mt-0.5 font-bold truncate leading-tight">
                Next bill: {nextBill.name} · {formatINR(nextBill.amount)} (Due in {nextBill.daysLeft}d)
              </p>
            </div>
          </div>}

          {/* Card 2: Financial Health Score from Database Analytics */}
          <div className="rounded-2xl glass-card-3d glass-card-3d-interactive p-4 flex flex-col justify-between shadow-sm">
            <div>
              <div className="flex items-center justify-between mb-1">
                <h3 className="text-[14px] font-extrabold text-metallic-silver tracking-tight">
                  Financial Health Score
                </h3>
              </div>

              {/* Semicircle Gauge Meter */}
              <div className="relative flex flex-col items-center justify-center pt-1 pb-1">
                <div className="relative w-40 h-22 flex items-center justify-center overflow-hidden">
                  <svg viewBox="0 0 100 60" className="w-40 h-24">
                    <defs>
                      <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#38BDF8" />
                        <stop offset="50%" stopColor="#818CF8" />
                        <stop offset="100%" stopColor="#C084FC" />
                      </linearGradient>
                      <filter id="healthGlow" x="-20%" y="-20%" width="140%" height="140%">
                        <feDropShadow dx="0" dy="0" stdDeviation="2" floodColor="#818CF8" floodOpacity="0.6" />
                      </filter>
                    </defs>
                    <path
                      d="M 15 52 A 35 35 0 0 1 85 52"
                      fill="none"
                      stroke="#131024"
                      strokeWidth="8"
                      strokeLinecap="round"
                    />
                    <path
                      d="M 15 52 A 35 35 0 0 1 85 52"
                      fill="none"
                      stroke="url(#gaugeGradient)"
                      strokeWidth="8"
                      strokeLinecap="round"
                      strokeDasharray="110"
                      strokeDashoffset={110 * (1 - (healthMetrics?.score ?? 0) / 100)}
                      filter="url(#healthGlow)"
                    />
                  </svg>

                  <div className="absolute bottom-1 inset-x-0 flex flex-col items-center justify-center">
                    <span className="text-[30px] font-extrabold text-metallic-silver tabular-nums leading-none">
                      {healthMetrics?.score ?? '—'}
                    </span>
                    <span className="text-[11px] font-bold text-emerald-400 mt-0.5 uppercase tracking-wider">
                      {healthMetrics?.rating || 'No data'}
                    </span>
                  </div>
                </div>

                <div className="w-32 flex items-center justify-between text-[10px] text-[#5A5675] font-semibold -mt-1 px-1">
                  <span>0</span>
                  <span>100</span>
                </div>
              </div>
            </div>

            <p className="text-[11.5px] text-[#8E8AA5] text-center pt-1.5 border-t border-white/[0.06]">
              {healthMetrics?.summary || 'No current financial health summary is available.'}
            </p>
          </div>

          {/* Card 3: Quick Insights from Real Database Computations */}
          <div className="rounded-2xl glass-card-3d glass-card-3d-interactive p-4 flex flex-col justify-between shadow-sm">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Activity className="w-4 h-4 text-violet-400" />
                <h3 className="text-[14px] font-extrabold text-metallic-silver tracking-tight">
                  Quick Insights
                </h3>
              </div>

              <div className="space-y-1.5">
                {/* Available Balance */}
                <div className="flex items-center justify-between py-1 border-b border-white/[0.04]">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-lg bg-emerald-500/15 border border-emerald-500/25 flex items-center justify-center text-emerald-400 flex-shrink-0">
                      <ArrowUp className="w-3 h-3" />
                    </div>
                    <div>
                      <span className="text-[13px] font-extrabold text-metallic-silver tabular-nums block leading-tight">
                        {healthMetrics?.availableBalance != null ? formatINR(healthMetrics.availableBalance) : '—'}
                      </span>
                      <span className="text-[10.5px] text-[#7C7896] block mt-0.5">
                        Available Balance
                      </span>
                    </div>
                  </div>
                  <span className="text-[10.5px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full">
                    Active
                  </span>
                </div>

                {/* Monthly Savings */}
                <div className="flex items-center justify-between py-1 border-b border-white/[0.04]">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-lg bg-violet-500/15 border border-violet-500/25 flex items-center justify-center text-violet-300 flex-shrink-0">
                      <Target className="w-3 h-3" />
                    </div>
                    <div>
                    <span className={`text-[13px] font-extrabold tabular-nums block leading-tight ${
                        (healthMetrics?.monthlySavings ?? 0) < 0 ? 'text-rose-300' : 'text-metallic-silver'
                      }`}>
                        {healthMetrics?.monthlySavings != null ? formatINR(healthMetrics.monthlySavings) : '—'}
                      </span>
                      <span className="text-[10.5px] text-[#7C7896] block mt-0.5">
                        Monthly Savings
                      </span>
                    </div>
                  </div>
                  {healthMetrics?.monthlySavings != null ? (healthMetrics.monthlySavings < 0 ? (
                    <span className="text-[10.5px] font-semibold text-rose-400 bg-rose-500/15 border border-rose-500/30 px-2 py-0.5 rounded-full">
                      Deficit
                    </span>
                  ) : (
                    <span className="text-[10.5px] font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/25 px-2 py-0.5 rounded-full">
                      On track
                    </span>
                  )) : <span className="text-[10.5px] text-[#77728F]">No data</span>}
                </div>

                {/* Pending Bills */}
                <div className="flex items-center justify-between py-1">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-lg bg-pink-500/15 border border-pink-500/25 flex items-center justify-center text-pink-400 flex-shrink-0">
                      <Calendar className="w-3 h-3" />
                    </div>
                    <div>
                      <span className="text-[13px] font-extrabold text-metallic-silver tabular-nums block leading-tight">
                        {bills.length ? formatINR(bills.reduce((s, b) => s + b.amount, 0)) : '—'}
                      </span>
                      <span className="text-[10.5px] text-[#7C7896] block mt-0.5">
                        Upcoming Bills
                      </span>
                    </div>
                  </div>
                  <span className="text-[10.5px] font-semibold text-amber-300 bg-amber-500/10 px-2 py-0.5 rounded-full">
                    {bills.length} due
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Card 4: Recent Voice Inquiries with Latency History */}
          <div className="rounded-2xl glass-card-3d glass-card-3d-interactive p-4 flex flex-col justify-between shadow-sm">
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-[14px] font-extrabold text-metallic-silver tracking-tight">
                  Voice Inquiries & Latency
                </h3>
                <span className="text-[10px] text-metallic-violet font-mono font-bold">
                  Last {transcriptHistory.length}
                </span>
              </div>

              <div className="space-y-2">
                {transcriptHistory.slice(0, 3).map((item) => (
                  <div key={item.id} className="p-2 rounded-xl glass-card-3d border border-white/[0.04]">
                    <div className="flex items-center justify-between">
                      <span className="text-[11.5px] font-semibold text-white truncate max-w-[190px]">
                        "{item.userQuery}"
                      </span>
                      <span className="text-[9.5px] text-[#7C7896]">{item.timestamp}</span>
                    </div>
                    <p className="text-[10.5px] text-[#A29DBE] line-clamp-1 mt-0.5">
                      {item.assistantResponse}
                    </p>
                    {item.latencies && (
                      <div className="flex items-center gap-1.5 mt-1 text-[9px] text-emerald-400 font-mono">
                        <span>⚡ {item.latencies.total_turn_ms ?? '—'}ms</span>
                        <span>·</span>
                        <span>tool: {item.latencies.tool_ms ?? '—'}ms</span>
                        <span>·</span>
                        <span>LLM first text: {item.latencies.generation_ttft_ms ?? '—'}ms</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
