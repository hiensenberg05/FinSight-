import React from 'react';
import { VoiceState } from '../../voice/VoiceContext';

interface SoundOrbMiniProps {
  voiceState: VoiceState;
  audioLevel?: number;
  onClick?: () => void;
}

export const SoundOrbMini: React.FC<SoundOrbMiniProps> = ({
  voiceState,
  audioLevel = 0,
  onClick,
}) => {
  const isListening = voiceState === 'listening';
  const isSpeaking = voiceState === 'speaking';
  const isThinking = voiceState === 'thinking';

  const dynamicScale = isListening
    ? 1 + Math.min(audioLevel * 0.45, 0.3)
    : isSpeaking
    ? 1.08
    : isThinking
    ? 0.95
    : 1;

  return (
    <div
      onClick={onClick}
      role="button"
      tabIndex={0}
      aria-label="Voice Engine Mini Orb"
      className="relative w-10 h-10 rounded-full flex items-center justify-center cursor-pointer select-none flex-shrink-0 group focus-visible:outline-none"
    >
      {/* Blurred Chromatic Rings */}
      <div
        className="absolute inset-0 rounded-full transition-transform duration-150 pointer-events-none"
        style={{ transform: `scale(${dynamicScale})` }}
      >
        <div
          className="absolute inset-0.5 rounded-full opacity-70 filter blur-[6px] mix-blend-screen animate-orb-slow"
          style={{
            background: 'radial-gradient(circle, #8B5CF6 0%, #EC4899 50%, #06B6D4 100%)',
          }}
        />
      </div>

      {/* Center Dark Core */}
      <div className="relative w-7 h-7 rounded-full bg-[#0D0B23] border border-violet-400/40 shadow-inner flex items-center justify-center z-10">
        <div className="flex items-center gap-[2px] h-3">
          <span
            className={`w-[1.5px] rounded-full transition-all duration-100 ${
              isListening ? 'h-3 bg-cyan-300' : isSpeaking ? 'h-2.5 bg-violet-300' : isThinking ? 'h-2 bg-pink-300 animate-pulse' : 'h-1.5 bg-white/75'
            }`}
          />
          <span
            className={`w-[1.5px] rounded-full transition-all duration-100 ${
              isListening ? 'h-4 bg-violet-300' : isSpeaking ? 'h-3.5 bg-white' : isThinking ? 'h-2.5 bg-pink-300 animate-pulse' : 'h-2 bg-white/75'
            }`}
          />
          <span
            className={`w-[1.5px] rounded-full transition-all duration-100 ${
              isListening ? 'h-2.5 bg-pink-300' : isSpeaking ? 'h-2 bg-violet-300' : isThinking ? 'h-2 bg-pink-300 animate-pulse' : 'h-1.5 bg-white/75'
            }`}
          />
        </div>
      </div>
    </div>
  );
};
