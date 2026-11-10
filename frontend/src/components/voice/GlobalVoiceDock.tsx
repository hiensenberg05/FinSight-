import React, { useState } from 'react';
import { 
  Mic, 
  MicOff, 
  Square, 
  Keyboard, 
  Send, 
  Sparkles, 
  X, 
  AlertTriangle, 
  CheckCircle2, 
  ArrowRight,
  TrendingUp,
  CreditCard,
  Target,
  Volume2,
  VolumeX
} from 'lucide-react';
import { useVoice } from '../../voice/VoiceContext';
import { SoundOrbMini } from './SoundOrbMini';
import { SoundOrbVisualizer } from './SoundOrbVisualizer';
import { formatINR } from '../../data/mock';

export const GlobalVoiceDock: React.FC = () => {
  const {
    voiceState,
    interimTranscript,
    finalTranscript,
    audioLevel,
    currentResponse,
    isMicOn,
    micPermissionDenied,
    textInputOpen,
    pendingTransfer,
    activePage,
    isContinuousMode,
    isWsConnected,
    isMuted,
    isMicMuted,
    voiceError,
    streamingText,
    toggleListening,
    toggleContinuousMode,
    toggleMicMute,
    toggleMute,
    processQuery,
    interruptSpeaking,
    setTextInputOpen,
    confirmTransfer,
    cancelTransfer,
    dismissCard,
  } = useVoice();

  const [typedInput, setTypedInput] = useState('');

  const isAssistantPage = activePage === 'ai-assistant';
  const isListening = voiceState === 'listening';
  const isSpeaking = voiceState === 'speaking';
  const isThinking = voiceState === 'thinking';
  const isError = voiceState === 'error';

  const getStateLabel = () => {
    switch (voiceState) {
      case 'listening':
        return isContinuousMode ? 'Listening hands-free... (Speak anytime)' : 'Listening...';
      case 'thinking':
        return 'Reasoning with database...';
      case 'speaking':
        return 'Speaking... (Speak or click to interrupt)';
      case 'error':
        return "Didn't catch that. Retrying...";
      case 'idle':
      default:
        return isContinuousMode ? 'Hands-Free Ready · Speak anytime' : 'Tap or press Space to speak';
    }
  };

  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!typedInput.trim()) return;
    processQuery(typedInput);
    setTypedInput('');
  };

  if (isContinuousMode) {
    const statusLabel = voiceState === 'listening'
      ? 'Listening to you'
      : voiceState === 'thinking' || voiceState === 'tool_execution'
      ? 'Working on your question'
      : voiceState === 'speaking'
      ? 'FinSight is speaking'
      : voiceState === 'error'
      ? 'Voice connection needs attention'
      : 'Live voice is ready';
    const liveText = voiceState === 'listening'
      ? interimTranscript || finalTranscript || 'Speak naturally. Your words will appear here.'
      : streamingText || currentResponse?.spokenText || 'Your spoken replies and conversation stay in the assistant thread.';

    return (
      <section
        role="region"
        aria-label="FinSight live voice session"
        className="fixed bottom-4 left-1/2 z-40 w-[min(720px,calc(100vw-24px))] -translate-x-1/2 rounded-2xl border border-slate-700/80 bg-[#0E1322]/95 px-3.5 py-2 text-white shadow-[0_16px_50px_rgba(0,0,0,0.65)] backdrop-blur-xl flex items-center justify-between gap-3 transition-all"
      >
        {/* Left: Live Visualizer & Status */}
        <div className="flex items-center gap-3 min-w-0">
          <div 
            className="relative flex-shrink-0 flex items-center justify-center cursor-pointer p-0.5" 
            onClick={toggleListening} 
            title={isMicMuted ? 'Mic is muted' : 'Tap to pause/resume'}
          >
            <SoundOrbMini voiceState={voiceState} audioLevel={audioLevel} />
          </div>
          <div className="min-w-0 flex flex-col justify-center">
            <div className="flex items-center gap-2">
              <span className={`inline-block h-2 w-2 rounded-full ${voiceState === 'error' ? 'bg-amber-400' : voiceState === 'listening' ? 'bg-cyan-400 animate-pulse' : voiceState === 'speaking' ? 'bg-indigo-400' : 'bg-emerald-400'}`} />
              <span className="text-[12px] font-semibold text-slate-100 tracking-tight leading-none truncate">
                {voiceState === 'error' ? (voiceError || statusLabel) : statusLabel}
              </span>
              <span className="hidden sm:inline-block text-[10.5px] text-slate-400 font-mono">
                {isWsConnected ? '· 14ms gateway' : '· connecting'}
              </span>
            </div>
            <p className="text-[11px] text-slate-300 truncate max-w-[190px] sm:max-w-[320px] mt-0.5 leading-tight" aria-live="polite">
              {liveText}
            </p>
          </div>
        </div>

        {/* Right: Tactile Audio Controls */}
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <button
            type="button"
            onClick={toggleMicMute}
            aria-pressed={isMicMuted}
            title={isMicMuted ? 'Unmute microphone' : 'Mute microphone'}
            className={`flex h-8 items-center gap-1.5 rounded-lg border px-2.5 text-[11px] font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 ${
              isMicMuted 
                ? 'border-rose-500/40 bg-rose-500/15 text-rose-300' 
                : 'border-slate-700/80 bg-slate-800/60 text-slate-300 hover:bg-slate-700/60 hover:text-white'
            }`}
          >
            {isMicMuted ? <MicOff className="h-3.5 w-3.5" /> : <Mic className="h-3.5 w-3.5" />}
            <span className="hidden md:inline">{isMicMuted ? 'Unmute' : 'Mute'}</span>
          </button>

          <button
            type="button"
            onClick={toggleMute}
            aria-pressed={isMuted}
            title={isMuted ? 'Unmute assistant speaker' : 'Mute assistant speaker'}
            className={`flex h-8 items-center gap-1.5 rounded-lg border px-2.5 text-[11px] font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 ${
              isMuted 
                ? 'border-amber-500/40 bg-amber-500/15 text-amber-300' 
                : 'border-slate-700/80 bg-slate-800/60 text-slate-300 hover:bg-slate-700/60 hover:text-white'
            }`}
          >
            {isMuted ? <VolumeX className="h-3.5 w-3.5" /> : <Volume2 className="h-3.5 w-3.5" />}
            <span className="hidden md:inline">{isMuted ? 'Speaker Off' : 'Speaker'}</span>
          </button>

          {voiceState === 'speaking' && (
            <button
              type="button"
              onClick={interruptSpeaking}
              title="Interrupt and stop speaking"
              className="flex h-8 items-center gap-1.5 rounded-lg border border-rose-500/40 bg-rose-500/20 px-2.5 text-[11px] font-semibold text-rose-300 transition hover:bg-rose-500/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-400"
            >
              <Square className="h-3 w-3 fill-current" />
              <span>Stop</span>
            </button>
          )}

          <button
            type="button"
            onClick={toggleContinuousMode}
            aria-label="End live voice session"
            title="Close live voice capsule"
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-700/80 bg-slate-800/40 text-slate-400 transition hover:bg-slate-700/60 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      </section>
    );
  }

  if (isAssistantPage) return null;

  // Generate 16 responsive waveform bars
  const renderWaveform = () => {
    const barsCount = 14;
    return (
      <div className="flex items-center gap-[3px] h-6 px-1">
        {Array.from({ length: barsCount }).map((_, idx) => {
          let height = 4;
          if (isListening) {
            // Audio reactive dynamic height
            const waveMod = Math.sin((idx / barsCount) * Math.PI) * 0.9;
            height = Math.max(4, Math.round(4 + audioLevel * 20 * waveMod + (idx % 3) * 2));
          } else if (isSpeaking) {
            height = Math.max(5, Math.round(6 + Math.sin(Date.now() / 150 + idx) * 8 + 4));
          } else if (isThinking) {
            height = Math.max(4, Math.round(4 + ((idx + Math.floor(Date.now() / 200)) % 4) * 3));
          }

          return (
            <span
              key={idx}
              className={`w-[2.5px] rounded-full transition-all duration-75 ${
                isListening
                  ? 'bg-cyan-400'
                  : isSpeaking
                  ? 'bg-violet-400'
                  : isThinking
                  ? 'bg-pink-400 animate-pulse'
                  : 'bg-white/25'
              }`}
              style={{ height: `${height}px` }}
            />
          );
        })}
      </div>
    );
  };

  return (
    <div className="fixed bottom-3 left-1/2 -translate-x-1/2 z-50 flex flex-col items-center pointer-events-none max-w-[95vw] w-full sm:w-auto">
      {/* =========================================================================
          1. LIVE INTERIM TRANSCRIPT (Requirement 3: Large type 24px+ above dock)
         ========================================================================= */}
      {isListening && interimTranscript && (
        <div className="mb-2 pointer-events-auto px-5 py-2.5 rounded-2xl bg-[#0E1322]/95 border border-indigo-500/40 backdrop-blur-xl shadow-[0_12px_40px_rgba(0,0,0,0.8)] animate-in fade-in zoom-in-95 max-w-xl text-center">
          <p className="text-[22px] sm:text-[24px] font-bold text-white tracking-tight leading-tight select-none">
            "{interimTranscript}"
          </p>
        </div>
      )}

      {/* =========================================================================
          2. PENDING TRANSFER CONFIRMATION MODAL CARD (Voice Actionable)
         ========================================================================= */}
      {pendingTransfer && (
        <div className="mb-2 pointer-events-auto w-80 rounded-2xl bg-[#111726] border-2 border-indigo-500/60 p-4 shadow-2xl backdrop-blur-xl animate-in fade-in slide-in-from-bottom-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-300">
              Transfer Confirmation
            </span>
            <span className="text-[10px] text-amber-300 bg-amber-400/10 px-2 py-0.5 rounded-full border border-amber-400/25">
              Requires confirmation
            </span>
          </div>

          <div className="text-center py-2 bg-white/[0.02] border border-white/[0.04] rounded-xl mb-3">
            <span className="text-[12px] text-slate-400 block">Sending to</span>
            <h4 className="text-[16px] font-bold text-white mt-0.5">{pendingTransfer.payee}</h4>
            <div className="text-[26px] font-bold text-emerald-400 tabular-nums mt-0.5 font-mono">
              ₹{pendingTransfer.amount.toLocaleString('en-IN')}
            </div>
            <span className="text-[11px] text-slate-400 block mt-0.5">from Everyday account (HDFC •• 4821)</span>
          </div>

          <div className="text-[11.5px] text-slate-300 text-center mb-3">
            Say <strong>"Yes"</strong> or <strong>"Confirm"</strong>, or tap below:
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={confirmTransfer}
              className="flex-1 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-[12px] shadow-lg transition-transform active:scale-95"
            >
              Confirm
            </button>
            <button
              onClick={cancelTransfer}
              className="px-3.5 py-2 rounded-xl bg-white/[0.06] hover:bg-white/[0.1] text-slate-400 hover:text-white text-[12px] transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* =========================================================================
          3. SLIDE-UP ANSWER CARD (When outside AI Assistant page)
         ========================================================================= */}
      {!isAssistantPage && !pendingTransfer && currentResponse && (
        <div className="mb-2 pointer-events-auto w-[420px] max-w-[90vw] rounded-2xl bg-[#0E1322]/95 border border-indigo-500/30 p-4 shadow-2xl backdrop-blur-xl animate-in fade-in slide-in-from-bottom-3 relative">
          <button
            onClick={dismissCard}
            className="absolute top-3 right-3 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>

          <div className="flex items-start gap-2.5 pr-6">
            <div className="w-7 h-7 rounded-lg bg-indigo-600/20 border border-indigo-500/30 text-indigo-300 flex items-center justify-center flex-shrink-0 mt-0.5">
              <Sparkles className="w-3.5 h-3.5" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-[13px] font-semibold text-white leading-snug">
                {currentResponse.spokenText}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          4. CONTEXTUAL FOLLOW-UP CHIPS (Requirement 7)
         ========================================================================= */}
      {currentResponse?.followUpChips && currentResponse.followUpChips.length > 0 && !isListening && (
        <div className="mb-2 pointer-events-auto flex items-center justify-center gap-2 flex-wrap max-w-xl">
          {currentResponse.followUpChips.map((chip, idx) => (
            <button
              key={idx}
              onClick={() => processQuery(chip)}
              className="px-3 py-1 rounded-full bg-[#13102C]/90 hover:bg-[#1E1945] border border-violet-500/25 hover:border-violet-500/50 text-[11.5px] font-medium text-[#D2CFE8] shadow-md transition-all active:scale-95 whitespace-nowrap"
            >
              {chip}
            </button>
          ))}
        </div>
      )}

      {/* =========================================================================
          5. MIC DENIED INLINE EXPLANATION (Requirement 8)
         ========================================================================= */}
      {micPermissionDenied && (
        <div className="mb-2 pointer-events-auto px-4 py-1.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-[11px] text-amber-300 flex items-center gap-2">
          <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
          <span>Microphone access blocked. Use keyboard input below or allow permissions.</span>
        </div>
      )}

      {/* =========================================================================
          6. PRIMARY VOICE DOCK CAPSULE (Apple Glossy 3D Glass Pill)
         ========================================================================= */}
      <div className="pointer-events-auto flex items-center gap-2.5 px-3.5 py-2 rounded-full glass-card-3d border border-white/[0.18] shadow-[0_20px_60px_rgba(0,0,0,0.85)] backdrop-blur-2xl transition-all">
        {/* Left: Mini Orb on pages other than AI Assistant */}
        {!isAssistantPage && (
          <SoundOrbMini
            voiceState={voiceState}
            audioLevel={audioLevel}
            onClick={toggleListening}
          />
        )}

        {/* Text Input Mode vs. Voice Bar Mode */}
        {textInputOpen ? (
          <form onSubmit={handleTextSubmit} className="flex items-center gap-2 min-w-[260px] sm:min-w-[340px]">
            <input
              type="text"
              autoFocus
              placeholder="Ask anything about your money..."
              value={typedInput}
              onChange={(e) => setTypedInput(e.target.value)}
              className="flex-1 glass-inset-tray border border-white/[0.08] focus:border-violet-500/60 rounded-xl px-3 py-1.5 text-[12.5px] text-white placeholder-[#8E8AA5] focus:outline-none transition-colors"
            />
            <button
              type="submit"
              disabled={!typedInput.trim()}
              className="w-8 h-8 rounded-xl bg-violet-600 disabled:opacity-40 hover:bg-violet-500 text-white flex items-center justify-center transition-transform active:scale-95 flex-shrink-0 shadow-md"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
            <button
              type="button"
              onClick={() => setTextInputOpen(false)}
              className="text-[#8E8AA5] hover:text-white px-1 transition-colors text-[12px]"
            >
              Cancel
            </button>
          </form>
        ) : (
          <div className="flex items-center gap-3">
            {/* Primary Mic Button */}
            <button
              onClick={toggleListening}
              aria-label={isListening ? 'Stop listening' : 'Start speaking'}
              className={`relative w-9 h-9 rounded-full flex items-center justify-center transition-all active:scale-90 flex-shrink-0 ${
                isListening
                  ? 'bg-rose-500 text-white shadow-[0_0_24px_#f43f5e] border-t border-rose-300'
                  : isSpeaking
                  ? 'bg-violet-600 text-white shadow-[0_0_18px_rgba(139,92,246,0.5)] border-t border-violet-400'
                  : 'bg-gradient-to-b from-[#281A4D] to-[#120B24] border-t border-violet-400/40 border-b border-black/50 text-violet-200 shadow-[inset_0_1px_1px_rgba(255,255,255,0.2),0_4px_12px_rgba(0,0,0,0.5)] hover:border-violet-400/60'
              }`}
            >
              {isListening ? (
                <Square className="w-3.5 h-3.5 fill-current" />
              ) : (
                <Mic className="w-4 h-4" />
              )}
            </button>

            {/* Waveform Visualizer */}
            {renderWaveform()}

            {/* State Label with Metallic Font */}
            <div className="min-w-0 pr-1">
              <span className="text-[12px] font-extrabold text-metallic-silver block leading-tight truncate">
                {getStateLabel()}
              </span>
              <span className="text-[10px] text-[#8E8AA5] block leading-tight font-medium">
                {isListening 
                  ? 'Listening to speech... Space to finish' 
                  : isSpeaking
                  ? 'Tap mic or press Space to interrupt'
                  : isThinking
                  ? 'Analyzing financial intelligence...'
                  : 'Try: "Show my spending this month" · Space'}
              </span>
            </div>

            {/* Active "Mic on" Trust Indicator */}
            {isListening && (
              <div className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-rose-500/15 border border-rose-500/30 text-[10px] font-semibold text-rose-300 animate-pulse">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
                <span>Mic on</span>
              </div>
            )}

            {/* Keyboard Input Mode Toggle */}
            <button
              onClick={() => setTextInputOpen(true)}
              title="Switch to typing"
              className="w-8 h-8 rounded-full glass-card-3d text-[#8E8AA5] hover:text-white flex items-center justify-center transition-colors flex-shrink-0"
            >
              <Keyboard className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
