import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { VoiceState } from '../../types';
import { Volume2, Mic, Loader2, Sparkles, AlertCircle } from 'lucide-react';

interface VoiceOrbVisualizerProps {
  state: VoiceState;
  audioLevel?: number;
  onClick?: () => void;
}

export const VoiceOrbVisualizer: React.FC<VoiceOrbVisualizerProps> = ({
  state,
  audioLevel = 0,
  onClick,
}) => {
  const shouldReduceMotion = useReducedMotion();

  const getStatusText = () => {
    switch (state) {
      case 'listening':
        return 'Listening...';
      case 'processing':
        return 'Thinking...';
      case 'speaking':
        return 'Speaking...';
      case 'error':
        return 'Connection Error';
      case 'interrupted':
        return 'Paused';
      default:
        return 'Voice Engine Active';
    }
  };

  const isListening = state === 'listening';
  const isSpeaking = state === 'speaking';
  const isProcessing = state === 'processing';

  return (
    <div
      onClick={onClick}
      className="relative flex flex-col items-center justify-center cursor-pointer select-none group"
      title="Click to toggle FinSight Voice Assistant"
    >
      {/* 1. Multi-layer chromatic blurred aura */}
      <motion.div
        animate={
          shouldReduceMotion
            ? {}
            : {
                scale: isListening || isSpeaking ? [1, 1.25 + audioLevel * 0.3, 1] : [1, 1.08, 1],
                opacity: isListening || isSpeaking ? [0.45, 0.75, 0.45] : [0.25, 0.4, 0.25],
                rotate: [0, 180, 360],
              }
        }
        transition={{
          scale: { duration: 2.2, repeat: Infinity, ease: 'easeInOut' },
          opacity: { duration: 2.2, repeat: Infinity, ease: 'easeInOut' },
          rotate: { duration: 20, repeat: Infinity, ease: 'linear' },
        }}
        className="absolute w-44 h-44 rounded-full bg-gradient-to-tr from-violet-600 via-indigo-500 to-fuchsia-500 blur-3xl pointer-events-none"
      />

      {/* 2. Outer Orbital Glass Ring */}
      <div className="relative w-36 h-36 flex items-center justify-center">
        {/* Swirling Chromatic Wave Rings (Ethereal fluid arcs inspired by Raycast / Linear) */}
        <motion.div
          animate={shouldReduceMotion ? {} : { rotate: 360 }}
          transition={{ duration: isProcessing ? 4 : 22, repeat: Infinity, ease: 'linear' }}
          className="absolute inset-0 rounded-full border border-violet-400/25 bg-white/[0.03] backdrop-blur-md shadow-[0_0_24px_rgba(139,92,246,0.15)]"
        />

        <motion.div
          animate={shouldReduceMotion ? {} : { rotate: -360 }}
          transition={{ duration: 16, repeat: Infinity, ease: 'linear' }}
          className="absolute inset-2 rounded-full border border-dashed border-fuchsia-400/20"
        />

        {/* Chromatic Fluid Ribbon Arcs (SVG Fluid Neon Waves) */}
        <svg
          viewBox="0 0 160 160"
          className="absolute inset-0 w-full h-full pointer-events-none drop-shadow-[0_0_12px_rgba(168,85,247,0.4)]"
        >
          <defs>
            <linearGradient id="chromaticGradient1" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#8B5CF6" stopOpacity="0.9" />
              <stop offset="50%" stopColor="#EC4899" stopOpacity="0.7" />
              <stop offset="100%" stopColor="#06B6D4" stopOpacity="0.8" />
            </linearGradient>
            <linearGradient id="chromaticGradient2" x1="100%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#6366F1" stopOpacity="0.8" />
              <stop offset="50%" stopColor="#A855F7" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#F43F5E" stopOpacity="0.7" />
            </linearGradient>
          </defs>

          {/* Fluid Ribbon 1 */}
          <motion.path
            d="M 80, 20 C 120, 25 140, 60 135, 95 C 130, 130 95, 140 65, 135 C 30, 130 20, 95 25, 65 C 30, 35 50, 15 80, 20 Z"
            fill="none"
            stroke="url(#chromaticGradient1)"
            strokeWidth="1.8"
            animate={
              shouldReduceMotion
                ? {}
                : {
                    d: [
                      'M 80, 20 C 120, 25 140, 60 135, 95 C 130, 130 95, 140 65, 135 C 30, 130 20, 95 25, 65 C 30, 35 50, 15 80, 20 Z',
                      'M 80, 15 C 110, 35 145, 75 125, 105 C 105, 135 65, 145 45, 120 C 25, 95 15, 60 35, 35 C 55, 10 65, 5 80, 15 Z',
                      'M 80, 20 C 120, 25 140, 60 135, 95 C 130, 130 95, 140 65, 135 C 30, 130 20, 95 25, 65 C 30, 35 50, 15 80, 20 Z',
                    ],
                    rotate: [0, 120, 360],
                  }
            }
            transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
          />

          {/* Fluid Ribbon 2 */}
          <motion.path
            d="M 80, 25 C 115, 40 135, 80 120, 110 C 105, 140 60, 135 40, 115 C 20, 95 25, 50 45, 30 C 65, 10 70, 20 80, 25 Z"
            fill="none"
            stroke="url(#chromaticGradient2)"
            strokeWidth="1.6"
            strokeDasharray="6 4"
            animate={
              shouldReduceMotion
                ? {}
                : {
                    rotate: [360, 0],
                  }
            }
            transition={{ duration: 12, repeat: Infinity, ease: 'linear' }}
          />
        </svg>

        {/* 3. Central Dark Glass Hub */}
        <div className="relative w-20 h-20 rounded-full bg-[#0C0B14]/90 border border-white/[0.12] shadow-[inset_0_1px_0_rgba(255,255,255,0.2),0_8px_24px_rgba(0,0,0,0.6)] flex flex-col items-center justify-center p-2 backdrop-blur-xl group-hover:border-violet-400/40 transition-all">
          {/* Audio Wave Glyph / Pulse Icon */}
          <div className="text-violet-300 mb-1">
            {isListening ? (
              <Mic className="w-5 h-5 text-emerald-400 animate-pulse" />
            ) : isProcessing ? (
              <Loader2 className="w-5 h-5 text-cyan-400 animate-spin" />
            ) : isSpeaking ? (
              <Volume2 className="w-5 h-5 text-violet-300 animate-pulse" />
            ) : (
              // Audio wave bars
              <div className="flex items-center gap-[2.5px] h-4">
                <span className="w-[2px] h-2.5 bg-violet-400 rounded-full" />
                <span className="w-[2px] h-4 bg-violet-300 rounded-full" />
                <span className="w-[2px] h-2 bg-violet-400 rounded-full" />
              </div>
            )}
          </div>

          {/* Monospaced Status Indicator Text */}
          <span className="text-[9px] font-mono font-semibold tracking-tight text-text-secondary text-center leading-tight">
            {getStatusText()}
          </span>
        </div>
      </div>
    </div>
  );
};
