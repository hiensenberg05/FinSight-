import React, { useState } from 'react';
import { Mic, Square, CornerDownLeft } from 'lucide-react';
import { VoiceState } from '../../types';
import { LiveWaveformBars } from './LiveWaveformBars';

interface VoiceInputBarProps {
  onSendMessage: (text: string) => void;
  voiceState: VoiceState;
  audioLevel?: number;
  onToggleVoice: () => void;
  disabled?: boolean;
}

export const VoiceInputBar: React.FC<VoiceInputBarProps> = ({
  onSendMessage,
  voiceState,
  audioLevel = 0,
  onToggleVoice,
  disabled = false,
}) => {
  const [inputText, setInputText] = useState('');

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
  const isVoiceActive = isListening || isSpeaking || isProcessing;

  return (
    <form
      onSubmit={handleSubmit}
      className="relative w-full rounded-full bg-[#0A0818] border border-[#261E52] p-2 pl-3 pr-4 flex items-center gap-3.5 shadow-[0_8px_24px_rgba(0,0,0,0.5),inset_0_1px_0_rgba(255,255,255,0.06)]"
    >
      {/* 1. Circular Mic Trigger Button */}
      <button
        type="button"
        onClick={onToggleVoice}
        disabled={disabled || isProcessing}
        title={isListening ? 'Stop listening' : 'Start speaking'}
        className={`relative w-11 h-11 rounded-full flex items-center justify-center transition-all duration-200 select-none cursor-pointer flex-shrink-0 active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-400 ${
          isListening
            ? 'bg-rose-500 text-white shadow-[0_0_20px_rgba(244,63,94,0.6)] animate-pulse'
            : 'bg-[#4A32BA] border border-[#6D4FFF] text-white shadow-[0_0_16px_rgba(109,79,255,0.4)] hover:brightness-110'
        }`}
      >
        <Mic className="w-5 h-5 text-white" />
      </button>

      {/* 2. Frequency Waveform Bars (reacts to mic level in listening, flat in idle) */}
      <div className="flex items-center flex-shrink-0">
        <LiveWaveformBars
          isActive={isVoiceActive}
          audioLevel={audioLevel}
          barCount={24}
          height={26}
          colorTheme="violet"
        />
      </div>

      {/* 3. Text Prompt / Input */}
      <div className="flex-1 min-w-0 flex flex-col justify-center">
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          disabled={disabled || isListening || isProcessing}
          placeholder={
            isListening
              ? 'Listening... speak naturally in English or Hinglish'
              : isProcessing
              ? 'Thinking...'
              : 'Speak naturally...'
          }
          className="w-full bg-transparent border-none outline-none text-[14px] text-white placeholder:text-[#7C7896] font-medium focus:ring-0"
        />
        {!inputText && !isListening && (
          <span className="text-[12px] text-[#6B6785] truncate block">
            Try: "Show my investment performance" or "Set a savings goal"
          </span>
        )}
      </div>

      {/* 4. Right Stop / Submit Icon Button */}
      <button
        type={inputText.trim() ? 'submit' : 'button'}
        onClick={isListening ? onToggleVoice : undefined}
        disabled={!inputText.trim() && !isListening}
        className={`w-8 h-8 rounded-lg border border-[#261E52] flex items-center justify-center transition-all duration-150 flex-shrink-0 ${
          inputText.trim()
            ? 'bg-violet-600 border-violet-400 text-white hover:bg-violet-500 shadow-sm'
            : isListening
            ? 'bg-rose-500/20 border-rose-500/40 text-rose-300 hover:bg-rose-500/30'
            : 'bg-transparent text-[#5A5675] cursor-default'
        }`}
      >
        {isListening ? (
          <Square className="w-3.5 h-3.5 fill-current" />
        ) : (
          <CornerDownLeft className="w-3.5 h-3.5" />
        )}
      </button>
    </form>
  );
};
