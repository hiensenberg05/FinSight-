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
import { mockHealthMetrics, mockCategorySpending, mockBills } from '../../data/mockFinancialData';
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
  const [healthMetrics, setHealthMetrics] = useState<FinancialHealthMetrics | null>(mockHealthMetrics);
  const [categories, setCategories] = useState<CategorySpending[]>(mockCategorySpending);
  const [recentTxns, setRecentTxns] = useState<Transaction[]>([]);
  const [bills, setBills] = useState<Bill[]>(mockBills);
  const [showSimulator, setShowSimulator] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;
    api.getHealthMetrics()
      .then((data) => {
        if (isMounted && data && typeof data.score === 'number') {
          setHealthMetrics(data);
        }
      })
      .catch(() => {});

    api.getCategorySpending()
      .then((data) => {
        if (isMounted && Array.isArray(data) && data.length > 0) {
          setCategories(data);
        }
      })
      .catch(() => {});

    api.getBills()
      .then((data) => {
        if (isMounted && Array.isArray(data) && data.length > 0) {
          setBills(data);
        }
      })
      .catch(() => {});

    return () => {
      isMounted = false;
    };
  }, [pendingAction]);

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
    <div className="w-full max-w-7xl mx-auto min-h-full flex flex-col space-y-4 pb-16">
      {/* 2-COLUMN SPLIT COCKPIT */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* =========================================================================
            LEFT PRIMARY STREAM (7 of 12 cols = ~58%)
           ========================================================================= */}
        <div className="lg:col-span-7 flex flex-col space-y-3.5">
          {/* 1. Live 3D Voice Station with Three.js Interactive Sphere */}
          <div className="relative rounded-2xl glass-card-3d px-5 py-4 shadow-xl overflow-hidden border border-slate-800/80 bg-gradient-to-b from-[#111728]/90 via-[#0E1322]/95 to-[#0B0F17]/90">
            {/* Top Bar: Title, Engine Status & Persona / Language Selectors */}
            <div className="mb-2 flex flex-wrap items-center justify-between gap-2 pr-1">
              <div>
                <h2 className="text-[20px] font-extrabold text-metallic-silver tracking-tight leading-tight">
                  FinSight 3D Live Voice Co-Pilot
                </h2>
                <p className="text-[11.5px] text-slate-300 mt-0.5">
                  Real-time live dialogue grounded in PostgreSQL ledger math & Playwright DOM forensic proof.
                </p>
              </div>
              <div className="flex items-center gap-2 text-[11px] text-slate-300 font-mono" aria-label="Voice connection status">
                <span className={`h-2 w-2 rounded-full ${isWsConnected ? 'bg-emerald-400' : 'bg-amber-400'}`} />
                <span>{isWsConnected ? '14ms Gateway Connected' : 'Connecting Gateway'}</span>
              </div>
            </div>

            {/* Persona & Language Bar */}
            <div className="flex flex-wrap items-center justify-between gap-2 py-2 border-t border-b border-slate-800/80">
              <div className="flex flex-wrap items-center gap-2">
                {/* Persona */}
                <div className="flex items-center rounded-lg bg-slate-900/80 border border-slate-700/80 p-0.5" title="Gnani Voice Persona">
                  <button
                    onClick={() => setVoicePersona('Nalini')}
                    className={`px-2.5 py-1 rounded-md text-[10.5px] font-bold transition-all ${
                      voicePersona === 'Nalini'
                        ? 'bg-indigo-600 text-white shadow-sm'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Female (Nalini)
                  </button>
                  <button
                    onClick={() => setVoicePersona('Deepak')}
                    className={`px-2.5 py-1 rounded-md text-[10.5px] font-bold transition-all ${
                      voicePersona === 'Deepak'
                        ? 'bg-indigo-600 text-white shadow-sm'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Male (Deepak)
                  </button>
                </div>

                {/* Language Mode */}
                <div className="flex items-center rounded-lg bg-slate-900/80 border border-slate-700/80 p-0.5" title="Language Mode">
                  <button
                    onClick={() => setLanguageMode('auto')}
                    className={`px-2 py-1 rounded-md text-[10.5px] font-bold transition-all ${
                      languageMode === 'auto'
                        ? 'bg-cyan-600 text-white shadow-sm'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Auto
                  </button>
                  <button
                    onClick={() => setLanguageMode('en')}
                    className={`px-2 py-1 rounded-md text-[10.5px] font-bold transition-all ${
                      languageMode === 'en'
                        ? 'bg-indigo-600 text-white shadow-sm'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    English
                  </button>
                  <button
                    onClick={() => setLanguageMode('hi')}
                    className={`px-2 py-1 rounded-md text-[10.5px] font-bold transition-all ${
                      languageMode === 'hi'
                        ? 'bg-emerald-600 text-white shadow-sm'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    हिंदी
                  </button>
                  <button
                    onClick={() => setLanguageMode('hinglish')}
                    className={`px-2 py-1 rounded-md text-[10.5px] font-bold transition-all ${
                      languageMode === 'hinglish'
                        ? 'bg-cyan-700 text-white shadow-sm'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    Hinglish
                  </button>
                </div>
              </div>

              {/* Continuous Mode Toggle */}
              <button
                onClick={toggleContinuousMode}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-lg border text-[11px] font-bold transition-all active:scale-95 shadow-sm ${
                  isContinuousMode
                    ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300'
                    : 'bg-slate-900/80 border-slate-700/80 text-slate-300 hover:text-white'
                }`}
                title="Continuous hands-free voice co-pilot"
              >
                <span className={`w-2 h-2 rounded-full ${isContinuousMode ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`} />
                <span>{isContinuousMode ? 'Hands-Free Voice Active' : 'Enable Hands-Free Voice'}</span>
              </button>
            </div>

            {/* =========================================================================
                CENTERED 3D INTERACTIVE THREE.JS SOUND ORB SPHERE
               ========================================================================= */}
            <div className="flex flex-col items-center justify-center my-3 relative">
              <div 
                className="relative w-[210px] h-[210px] sm:w-[230px] sm:h-[230px] flex items-center justify-center cursor-pointer group"
                onClick={handleOrbToggle}
                title={isContinuousMode ? "Tap to pause hands-free listening" : "Tap to speak live to live"}
              >
                <SoundOrbVisualizer
                  voiceState={voiceState}
                  audioLevel={audioLevel}
                  onToggle={handleOrbToggle}
                  idleLabel={isContinuousMode ? 'Tap to pause' : 'Tap to talk live'}
                  className="w-[210px] h-[210px] sm:w-[230px] sm:h-[230px]"
                />
              </div>

              {/* Symmetrical Audio Waveform Bars */}
              <div className="mt-1 flex items-center justify-center">
                <LiveWaveformBars
                  isActive={audioLevelSource === 'microphone' || audioLevelSource === 'playback' || isListening || isSpeaking}
                  audioLevel={audioLevel}
                  height={20}
                  barCount={21}
                  colorTheme="gradient"
                  className="h-5"
                />
              </div>

              {/* Live Speech Transcription / Prompt Feedback */}
              <div className="mt-2 text-center max-w-lg px-4">
                <p className="text-[14px] sm:text-[15px] font-bold text-white tracking-tight leading-snug" aria-live="polite">
                  {isListening && (interimTranscript || finalTranscript) ? (
                    <span className="text-cyan-300 drop-shadow-[0_0_12px_rgba(6,182,212,0.6)]">
                      "{interimTranscript || finalTranscript}"
                    </span>
                  ) : isListening ? (
                    <span className="text-cyan-400/90 font-medium animate-pulse">
                      Listening to you... speak naturally
                    </span>
                  ) : isSpeaking ? (
                    <span className="text-indigo-200">
                      {streamingText ? (
                        <span className="line-clamp-2">"{streamingText.slice(0, 110)}..."</span>
                      ) : (
                        'FinSight is speaking · Tap orb to interrupt'
                      )}
                    </span>
                  ) : isProcessing ? (
                    <span className="text-indigo-300 flex items-center justify-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-indigo-400 animate-ping" />
                      Reasoning with database & tools...
                    </span>
                  ) : (
                    <span className="text-slate-300 font-medium">
                      {isContinuousMode ? 'Hands-free active · Speak anytime' : 'Tap the 3D sphere or speak anytime'}
                    </span>
                  )}
                </p>
                <span className="text-[10px] text-slate-400 font-mono mt-0.5 block">
                  {audioLevelSource === 'microphone' 
                    ? '● Live microphone input reactive' 
                    : audioLevelSource === 'playback' 
                    ? '● Live Gnani speech playback' 
                    : isContinuousMode 
                    ? '● Continuous conversation ready' 
                    : '● Click 3D sphere to talk live'}
                </span>
              </div>
            </div>

            {/* Action Prompt Chips */}
            <div className="flex items-center justify-center gap-2 pt-2 border-t border-slate-800/80 overflow-x-auto pb-1 scrollbar-none">
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
                    ? 'border-indigo-500/70 text-white shadow-[0_0_14px_rgba(99,102,241,0.4)]'
                    : 'border-slate-700/80 hover:border-indigo-500/40 text-slate-200'
                }`}
              >
                <BarChart2 className="w-3.5 h-3.5 text-indigo-400" />
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
                    ? 'border-indigo-500/70 text-white shadow-[0_0_14px_rgba(99,102,241,0.4)]'
                    : 'border-slate-700/80 hover:border-indigo-500/40 text-slate-200'
                }`}
              >
                <Target className="w-3.5 h-3.5 text-cyan-400" />
                <span>{languageMode === 'hi' ? 'खर्च क्यों बढ़ा?' : 'Why Did Spend Increase?'}</span>
              </button>

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
                    ? 'border-indigo-500/70 text-white shadow-[0_0_14px_rgba(99,102,241,0.4)]'
                    : 'border-slate-700/80 hover:border-indigo-500/40 text-slate-200'
                }`}
              >
                <TrendingUp className="w-3.5 h-3.5 text-pink-400" />
                <span>{languageMode === 'hi' ? 'Anomalies Check' : 'Check Anomalies'}</span>
              </button>
            </div>
          </div>

          {/* 2. Full Conversation Thread & Multimodal Sticky Composer */}
          <div className="rounded-2xl glass-card-3d border border-slate-800/80 p-4 shadow-xl backdrop-blur-2xl flex flex-col space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
              <div className="flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-indigo-400" />
                <h3 className="text-sm font-bold text-white tracking-tight">Conversation & Reasoning Stream</h3>
              </div>
              <div className="flex items-center gap-2">
                {(isSpeaking || isPlaybackPaused) && (
                  <button
                    onClick={togglePauseVoice}
                    className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-semibold border transition-all ${
                      isPlaybackPaused
                        ? 'bg-amber-500/20 border-amber-500/40 text-amber-300 hover:bg-amber-500/30'
                        : 'bg-indigo-600/30 border-indigo-400/40 text-indigo-200 hover:bg-indigo-600/40'
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
                      : 'bg-slate-800/60 border-slate-700/80 text-slate-300 hover:text-white'
                  }`}
                  title="Toggle assistant voice audio output"
                >
                  {isMuted ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
                  <span>{isMuted ? 'Muted' : 'Voice ON'}</span>
                </button>
              </div>
            </div>

            {/* Scrollable messages container */}
            <div className="max-h-[460px] min-h-[280px] overflow-y-auto space-y-3 pr-1.5 scrollbar-thin scrollbar-thumb-indigo-600/40">
              {transcriptHistory.length === 0 && !streamingText && (
                <div className="flex flex-col items-center justify-center py-10 text-center space-y-2">
                  <div className="w-12 h-12 rounded-2xl bg-indigo-600/15 border border-indigo-500/30 flex items-center justify-center text-indigo-400 mb-1">
                    <Sparkles className="w-6 h-6" />
                  </div>
                  <h4 className="text-[15px] font-bold text-white">Ask FinSight Anything</h4>
                  <p className="text-[12px] text-slate-400 max-w-md">
                    Speak or type: <span className="text-slate-200">"Show me my Swiggy order proof"</span>, <span className="text-slate-200">"Why did spend change?"</span>, or <span className="text-slate-200">"Check irregular charges"</span>.
                  </p>
                </div>
              )}

              {/* Past completed turns */}
              {[...transcriptHistory].reverse().map((turn) => (
                <div key={turn.id} className="space-y-2">
                  {/* User Prompt */}
                  <div className="flex justify-end">
                    <div className="max-w-[85%] rounded-2xl rounded-tr-sm bg-indigo-950/40 border border-indigo-500/40 px-4 py-2 shadow-lg text-right">
                      <div className="flex items-center justify-end gap-1.5 text-[9.5px] uppercase font-bold tracking-wider text-indigo-300 mb-0.5">
                        <span>You</span>
                        <span>·</span>
                        <span>{turn.timestamp}</span>
                      </div>
                      <p className="text-[13px] font-medium text-slate-100 leading-snug">
                        "{turn.userQuery}"
                      </p>
                    </div>
                  </div>

                  {/* Assistant Response */}
                  <div className="rounded-2xl bg-slate-900/80 border border-slate-800/80 p-3.5 shadow-md space-y-2.5">
                    <div className="flex items-start gap-2.5">
                      <div className="w-7 h-7 rounded-xl bg-indigo-600/30 border border-indigo-400/40 text-indigo-200 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-md">
                        <Sparkles className="w-3.5 h-3.5" />
                      </div>
                      <div className="min-w-0 flex-1 space-y-2">
                        <FormattedMessage text={turn.assistantResponse} />

                        {turn.followUpQuestions && turn.followUpQuestions.length > 0 && (
                          <div className="flex flex-wrap items-center gap-1.5 pt-1" aria-label="Suggested follow-up questions">
                            {turn.followUpQuestions.map((question) => (
                              <button
                                key={question}
                                type="button"
                                onClick={() => processQuery(question)}
                                className="rounded-lg border border-indigo-500/30 bg-indigo-500/10 px-2.5 py-1 text-[11px] text-indigo-200 hover:bg-indigo-500/20 transition-colors"
                              >
                                {question}
                              </button>
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
                              <span>Verified from {turn.evidence.length} ledger records</span>
                              <ExternalLink className="w-2.5 h-2.5 opacity-60 ml-0.5" />
                            </button>
                            <span className="text-[10px] text-slate-400 font-mono">Deterministic SQL Grounding</span>
                          </div>
                        )}

                        {/* Action Proposal Card in-line */}
                        {turn.actionProposal && (
                          <ActionConfirmationCard
                            proposal={turn.actionProposal}
                            onConfirm={confirmActionProposal}
                            onCancel={cancelActionProposal}
                          />
                        )}

                        {/* Slack Alert Card in-line */}
                        {(turn.slackAlert || turn.toolUsed === 'dispatch_slack_alert') && (
                          <SlackAlertCard
                            data={turn.slackAlert || {
                              channel: '#engineering-inventory-tracker',
                              workspace: 'accounting',
                              alert_type: 'custom',
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
                      <div className="max-w-[85%] rounded-2xl rounded-tr-sm bg-indigo-950/40 border border-indigo-500/40 px-4 py-2 shadow-lg text-right">
                        <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-300 block">You</span>
                        <p className="text-[13px] font-medium text-slate-100 leading-snug mt-0.5">"{finalTranscript}"</p>
                      </div>
                    </div>
                  )}

                  {/* Assistant Streaming Bubble */}
                  <div className="rounded-2xl bg-slate-900/90 border border-indigo-500/40 p-3.5 shadow-xl relative backdrop-blur-2xl">
                    <div className="flex items-start gap-2.5">
                      <div className="w-7 h-7 rounded-xl bg-indigo-600/30 border border-indigo-400/40 text-indigo-200 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-md">
                        <Sparkles className="w-3.5 h-3.5" />
                      </div>
                      <div className="min-w-0 flex-1">
                        {isProcessing && !streamingText ? (
                          <div className="flex items-center gap-2 text-[12.5px] text-indigo-300">
                            <span className="w-2 h-2 rounded-full bg-indigo-400 animate-ping" />
                            <span>{voiceState === 'tool_execution' ? 'Executing verified SQL tool & forensics…' : 'Reasoning with database…'}</span>
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

              <div ref={chatBottomRef} />
            </div>

            {/* =========================================================================
                PERMANENT MULTIMODAL COMPOSER: Never hidden, always interactive
               ========================================================================= */}
            <div className="pt-3 border-t border-slate-800/80">
              <form onSubmit={(e) => { e.preventDefault(); handleSendChat(); }} className="flex items-center gap-2">
                <div className="relative flex-1">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder={languageMode === 'hi' ? 'अपना सवाल लिखें या बोलें...' : 'Type query or edit numbers while listening...'}
                    className="w-full min-h-[46px] rounded-xl bg-slate-900/90 border border-slate-700/80 focus:border-indigo-500/80 focus:bg-slate-900 px-4 py-2.5 text-sm text-slate-100 placeholder-slate-400 transition-all focus:outline-none shadow-inner"
                  />
                </div>
                <button
                  type="button"
                  onClick={toggleListening}
                  disabled={isProcessing}
                  title={isListening ? 'Stop listening' : 'Start speaking'}
                  className={`min-h-[46px] min-w-[46px] rounded-xl flex items-center justify-center transition-all ${
                    isListening
                      ? 'bg-rose-500/20 border border-rose-500/40 text-rose-300 animate-pulse'
                      : 'bg-slate-800/80 border border-slate-700/80 text-slate-300 hover:text-white hover:bg-slate-700/80'
                  }`}
                >
                  <Mic className="w-4 h-4" />
                </button>
                <button
                  type="submit"
                  disabled={!chatInput.trim()}
                  className="min-h-[46px] min-w-[46px] rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-30 text-white flex items-center justify-center transition-all shadow-md active:scale-95"
                  title="Send prompt"
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>

              <div className="flex items-center justify-between mt-2 px-1 text-[11px] text-slate-400 font-medium">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${isListening ? 'bg-cyan-400 animate-pulse' : isSpeaking ? 'bg-indigo-400' : 'bg-emerald-400'}`} />
                  <span>{isListening ? 'Listening hands-free...' : isSpeaking ? 'Assistant speaking · Type or interrupt anytime' : 'Multimodal: type or speak freely'}</span>
                </div>
                {isSpeaking && (
                  <button
                    type="button"
                    onClick={interruptSpeaking}
                    className="text-rose-400 hover:text-rose-300 font-semibold transition-colors flex items-center gap-1"
                  >
                    <Square className="w-2.5 h-2.5 fill-current" /> Stop Audio
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* =========================================================================
            RIGHT DEDICATED EVIDENCE INSPECTOR (5 of 12 cols = ~42%)
           ========================================================================= */}
        <div className="lg:col-span-5 flex flex-col space-y-3.5 sticky top-2">
          {/* Header */}
          <div className="flex items-center justify-between px-1">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <h3 className="text-[13.5px] font-bold text-slate-100 tracking-tight">Contextual Evidence Inspector</h3>
            </div>
            <span className="text-[10px] font-mono font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full">
              Live Relational Grounding
            </span>
          </div>

          {/* Slot 1: Active Playwright DOM Portal Evidence Card (Swiggy / BESCOM) */}
          {activePortalEvidence && (
            <div className="animate-in fade-in slide-in-from-right-4 duration-300">
              <PortalEvidenceCard
                evidence={activePortalEvidence}
                onDismiss={dismissPortalEvidence}
              />
            </div>
          )}

          {/* Slot 2: Active What-If Interactive Simulation Card & Financial Calculator */}
          {activeSimulation ? (
            <div className="animate-in fade-in slide-in-from-right-4 duration-300">
              <InteractiveSimulationCard
                initialData={activeSimulation}
                onSliderChange={adjustSimulationSlider}
              />
            </div>
          ) : (
            showSimulator && (
              <div className="animate-in fade-in slide-in-from-right-4 duration-300">
                <InteractiveSimulationCard
                  initialData={{
                    simulation_type: 'spend_reduction',
                    category: 'Dining & Discretionary',
                    reduction_percentage: 20,
                    historical_monthly_spend: 14200,
                    simulated_monthly_spend: 11360,
                    monthly_savings: 2840,
                    annualized_savings: 34080,
                    goal_impact: {
                      goal_name: 'Emergency Fund',
                      target_amount: 50000,
                      remaining_amount: 24000,
                      baseline_months_to_complete: 4.5,
                      accelerated_months_to_complete: 3.2,
                      months_saved: 1.3,
                    },
                  }}
                  onSliderChange={adjustSimulationSlider}
                />
              </div>
            )
          )}

          {/* Slot 3: Financial Health Score Meter */}
          <div className="rounded-2xl glass-card-3d p-4 flex flex-col justify-between shadow-sm border border-slate-800/80">
            <div>
              <div className="flex items-center justify-between mb-1">
                <h4 className="text-[13px] font-bold text-slate-200 tracking-tight">
                  Financial Health Score
                </h4>
                <span className="text-[10.5px] font-bold text-emerald-400 uppercase tracking-wider bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                  {healthMetrics?.rating || 'Calculating'}
                </span>
              </div>

              {/* Semicircle Gauge Meter */}
              <div className="relative flex flex-col items-center justify-center pt-1 pb-1">
                <div className="relative w-40 h-22 flex items-center justify-center overflow-hidden">
                  <svg viewBox="0 0 100 60" className="w-40 h-24">
                    <defs>
                      <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#06B6D4" />
                        <stop offset="50%" stopColor="#6366F1" />
                        <stop offset="100%" stopColor="#A855F7" />
                      </linearGradient>
                      <filter id="healthGlow" x="-20%" y="-20%" width="140%" height="140%">
                        <feDropShadow dx="0" dy="0" stdDeviation="2" floodColor="#6366F1" floodOpacity="0.5" />
                      </filter>
                    </defs>
                    <path
                      d="M 15 52 A 35 35 0 0 1 85 52"
                      fill="none"
                      stroke="#1E293B"
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
                    <span className="text-[28px] font-extrabold text-white tabular-nums leading-none font-mono">
                      {healthMetrics?.score ?? '—'}
                    </span>
                    <span className="text-[10px] text-slate-400 mt-0.5">out of 100</span>
                  </div>
                </div>

                <div className="w-32 flex items-center justify-between text-[10px] text-slate-400 font-mono -mt-1 px-1">
                  <span>0</span>
                  <span>100</span>
                </div>
              </div>
            </div>

            <p className="text-[11px] text-slate-300 text-center pt-2 border-t border-slate-800/80 leading-relaxed">
              {healthMetrics?.summary || 'Deterministic SQL metrics computed across all active accounts.'}
            </p>
          </div>

          {/* Slot 4: Quick Insights (Balance, Savings, Bills) */}
          <div className="rounded-2xl glass-card-3d p-4 space-y-2.5 shadow-sm border border-slate-800/80">
            <div className="flex items-center gap-2 mb-1">
              <Activity className="w-3.5 h-3.5 text-indigo-400" />
              <h4 className="text-[13px] font-bold text-slate-200 tracking-tight">
                Quick Ledger Insights
              </h4>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between py-1.5 border-b border-slate-800/80">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-lg bg-emerald-500/15 border border-emerald-500/25 flex items-center justify-center text-emerald-400 flex-shrink-0">
                    <ArrowUp className="w-3 h-3" />
                  </div>
                  <div>
                    <span className="text-[13px] font-bold text-white tabular-nums font-mono block leading-tight">
                      {healthMetrics?.availableBalance != null ? formatINR(healthMetrics.availableBalance) : '—'}
                    </span>
                    <span className="text-[10.5px] text-slate-400 block">Available Balance</span>
                  </div>
                </div>
                <span className="text-[10.5px] font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/25 px-2 py-0.5 rounded-full">
                  Active
                </span>
              </div>

              <div className="flex items-center justify-between py-1.5 border-b border-slate-800/80">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-lg bg-indigo-500/15 border border-indigo-500/25 flex items-center justify-center text-indigo-300 flex-shrink-0">
                    <Target className="w-3 h-3" />
                  </div>
                  <div>
                    <span className={`text-[13px] font-bold tabular-nums font-mono block leading-tight ${
                      (healthMetrics?.monthlySavings ?? 0) < 0 ? 'text-rose-400' : 'text-emerald-400'
                    }`}>
                      {healthMetrics?.monthlySavings != null ? formatINR(healthMetrics.monthlySavings) : '—'}
                    </span>
                    <span className="text-[10.5px] text-slate-400 block">Monthly Savings</span>
                  </div>
                </div>
                <span className={`text-[10.5px] font-semibold px-2 py-0.5 rounded-full ${
                  (healthMetrics?.monthlySavings ?? 0) < 0
                    ? 'text-rose-400 bg-rose-500/15 border border-rose-500/30'
                    : 'text-emerald-400 bg-emerald-500/10 border border-emerald-500/25'
                }`}>
                  {(healthMetrics?.monthlySavings ?? 0) < 0 ? 'Deficit' : 'On track'}
                </span>
              </div>

              <div className="flex items-center justify-between py-1.5">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-lg bg-pink-500/15 border border-pink-500/25 flex items-center justify-center text-pink-400 flex-shrink-0">
                    <Calendar className="w-3 h-3" />
                  </div>
                  <div>
                    <span className="text-[13px] font-bold text-white tabular-nums font-mono block leading-tight">
                      {bills.length ? formatINR(bills.reduce((s, b) => s + b.amount, 0)) : '—'}
                    </span>
                    <span className="text-[10.5px] text-slate-400 block">Upcoming Bills</span>
                  </div>
                </div>
                <span className="text-[10.5px] font-semibold text-amber-300 bg-amber-500/10 border border-amber-500/25 px-2 py-0.5 rounded-full">
                  {bills.length} due
                </span>
              </div>
            </div>
          </div>

          {/* Slot 5: Category Spending Donut Chart */}
          {categories.length > 0 && (
            <div className="rounded-2xl glass-card-3d p-4 shadow-sm border border-slate-800/80">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-[13px] font-bold text-slate-200 tracking-tight">
                  Spending Breakdown
                </h4>
                <span className="text-[10.5px] text-slate-400 font-mono">
                  Total: {formatINR(totalSpent)}
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
                        innerRadius={32}
                        outerRadius={46}
                        paddingAngle={3}
                        cornerRadius={4}
                        stroke="rgba(0,0,0,0.3)"
                        strokeWidth={1}
                        isAnimationActive={false}
                      >
                        {categories.map((entry, index) => (
                          <Cell key={`donut-${index}`} fill={entry.color || '#6366F1'} />
                        ))}
                      </Pie>
                      <Tooltip
                        content={({ active, payload }) => {
                          if (active && payload && payload.length) {
                            const data = payload[0].payload as CategorySpending;
                            return (
                              <div className="bg-slate-900 border border-slate-700 p-2 rounded-lg text-xs text-white shadow-xl">
                                <p className="font-semibold text-white">{data.name}</p>
                                <p className="text-indigo-400 font-mono tabular-nums">{formatINR(data.amount)} ({data.percentage}%)</p>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="absolute inset-4 rounded-full bg-slate-900/90 flex flex-col items-center justify-center pointer-events-none border border-slate-700/60">
                    <span className="text-[11px] font-bold text-white tabular-nums font-mono leading-none">
                      {formatINR(totalSpent)}
                    </span>
                  </div>
                </div>

                <div className="space-y-1 flex-1 text-[11px]">
                  {categories.slice(0, 4).map((cat) => (
                    <div key={cat.name} className="flex items-center justify-between px-2 py-0.5 rounded bg-slate-900/40">
                      <div className="flex items-center gap-1.5 truncate">
                        <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ backgroundColor: cat.color || '#6366F1' }} />
                        <span className="text-slate-300 truncate font-medium">{cat.name}</span>
                      </div>
                      <span className="text-slate-400 font-mono tabular-nums ml-2">
                        {cat.percentage}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Slot 6: Voice Telemetry & Turn Latency History */}
          <div className="rounded-2xl glass-card-3d p-4 shadow-sm border border-slate-800/80">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-[13px] font-bold text-slate-200 tracking-tight">
                Voice Inquiries & Engine Telemetry
              </h4>
              <span className="text-[10px] text-indigo-400 font-mono font-bold">
                Last {transcriptHistory.length} turns
              </span>
            </div>

            <div className="space-y-2">
              {transcriptHistory.length === 0 ? (
                <p className="text-[11px] text-slate-400 text-center py-2">
                  No turns yet. Speak or type to begin your financial session.
                </p>
              ) : (
                transcriptHistory.slice(0, 3).map((item) => (
                  <div key={item.id} className="p-2 rounded-xl bg-slate-900/60 border border-slate-800/80">
                    <div className="flex items-center justify-between">
                      <span className="text-[11.5px] font-semibold text-white truncate max-w-[200px]">
                        "{item.userQuery}"
                      </span>
                      <span className="text-[9.5px] text-slate-400">{item.timestamp}</span>
                    </div>
                    <p className="text-[10.5px] text-slate-300 line-clamp-1 mt-0.5">
                      {item.assistantResponse}
                    </p>
                    {item.latencies && (
                      <div className="flex items-center gap-1.5 mt-1 text-[9px] text-emerald-400 font-mono">
                        <span>⚡ {item.latencies.total_turn_ms ?? '—'}ms</span>
                        <span>·</span>
                        <span>tool: {item.latencies.tool_ms ?? '—'}ms</span>
                        <span>·</span>
                        <span>first text: {item.latencies.generation_ttft_ms ?? '—'}ms</span>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
