import React, { useState, useRef } from 'react';
import { Mic, MicOff, Send, Sparkles, AlertCircle, Loader2 } from 'lucide-react';
import { VoiceState } from '../../types';
import { AudioWaveform } from '../voice/AudioWaveform';

interface MessageComposerProps {
  onSendMessage: (text: string) => void;
  voiceState: VoiceState;
  audioLevel?: number;
  errorMessage?: string | null;
  onToggleVoice: () => void;
  disabled?: boolean;
}

export const MessageComposer: React.FC<MessageComposerProps> = ({
  onSendMessage,
  voiceState,
  audioLevel = 0,
  errorMessage,
  onToggleVoice,
  disabled = false,
}) => {
  const [inputText, setInputText] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputText.trim() && !disabled && voiceState !== 'processing') {
      onSendMessage(inputText.trim());
      setInputText('');
    }
  };

  const isListening = voiceState === 'listening';
  const isSpeaking = voiceState === 'speaking';
  const isProcessing = voiceState === 'processing';

  return (
    <div className="w-full flex flex-col gap-1.5">
      {/* Error or Alert Feedback Banner */}
      {errorMessage && (
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-[11px] animate-fadeIn">
          <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 text-rose-400" />
          <span className="truncate">{errorMessage}</span>
          <span className="ml-auto text-[10px] text-rose-400/80 underline cursor-pointer" onClick={() => onToggleVoice()}>Retry</span>
        </div>
      )}

      {/* Main Composer Capsule */}
      <form
        onSubmit={handleSubmit}
        className={`relative w-full rounded-full bg-[#12182B] border transition-all duration-300 px-3 py-1.5 flex items-center gap-2 shadow-panel border-t-white/10 ring-1 ring-inset ring-white/[0.04] ${
          isListening
            ? 'border-emerald-500/70 shadow-[0_0_20px_rgba(16,185,129,0.3)] bg-[#101b2a]'
            : isProcessing
            ? 'border-cyan-500/60 shadow-[0_0_15px_rgba(6,182,212,0.2)]'
            : 'border-slate-700/60 focus-within:border-purple-500/70 focus-within:shadow-glow-purple'
        }`}
      >
        {/* Dynamic Voice Activity Waveform */}
        <div className="pl-1.5 flex items-center justify-center">
          {isListening ? (
            <AudioWaveform active={true} audioLevel={audioLevel} color="bg-emerald-400" barsCount={12} />
          ) : isSpeaking ? (
            <AudioWaveform active={true} color="bg-purple-400" barsCount={12} />
          ) : isProcessing ? (
            <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />
          ) : (
            <Sparkles className="w-4 h-4 text-purple-400/80" />
          )}
        </div>

        {/* Text Input */}
        <input
          ref={inputRef}
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          disabled={disabled || isListening || isProcessing}
          placeholder={
            isListening
              ? 'Listening to your voice (Gnani Prisma STT)... speak now'
              : isProcessing
              ? 'FinSight is retrieving and calculating records...'
              : 'Ask me anything about your finances...'
          }
          className="w-full bg-transparent border-none outline-none text-xs sm:text-sm text-slate-100 placeholder-slate-400 px-1 py-1 focus:ring-0 disabled:opacity-60"
        />

        {/* Prominent Microphone Voice Button */}
        <button
          type="button"
          onClick={onToggleVoice}
          disabled={disabled || isProcessing}
          title={isListening ? 'Stop listening' : 'Start voice conversation (Gnani STT)'}
          className={`relative p-2 rounded-full transition-all duration-200 flex items-center justify-center flex-shrink-0 ${
            isListening
              ? 'bg-emerald-500 text-white shadow-[0_0_20px_rgba(16,185,129,0.6)] animate-pulse'
              : 'bg-[#182038] hover:bg-purple-600/30 text-purple-300 hover:text-white border border-slate-700/60 hover:border-purple-500/40'
          }`}
        >
          {isListening ? (
            <MicOff className="w-4 h-4 text-white" />
          ) : (
            <Mic className="w-4 h-4" />
          )}
        </button>

        {/* Send Button */}
        <button
          type="submit"
          disabled={!inputText.trim() || disabled || isListening || isProcessing}
          className={`p-2 rounded-full transition-all duration-200 flex items-center justify-center flex-shrink-0 ${
            inputText.trim() && !disabled && !isListening && !isProcessing
              ? 'bg-purple-600 hover:bg-purple-500 text-white shadow-glow-purple cursor-pointer'
              : 'bg-[#1A2238] text-slate-600 cursor-not-allowed opacity-60'
          }`}
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
