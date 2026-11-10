import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { VoiceState } from '../../types';
import { Mic, Loader2, Volume2, Sparkles, AlertCircle, Pause } from 'lucide-react';

interface AssistantOrbProps {
  state: VoiceState;
  audioLevel?: number;
  onClick?: () => void;
}

export const AssistantOrb: React.FC<AssistantOrbProps> = ({
  state,
  audioLevel = 0,
  onClick,
}) => {
  const shouldReduceMotion = useReducedMotion();

  // Distinct animation values for each state
  const getOrbStateStyles = () => {
    switch (state) {
      case 'listening':
        return {
          coreGlow: 'from-emerald-400/40 via-purple-600/30 to-violet-950',
          borderColor: 'border-emerald-400/60 shadow-[0_0_30px_rgba(16,185,129,0.35)]',
          pulseScale: [1, 1.15 + audioLevel * 0.2, 1],
        };
      case 'processing':
        return {
          coreGlow: 'from-cyan-400/40 via-purple-700/40 to-slate-950',
          borderColor: 'border-cyan-400/50 shadow-[0_0_25px_rgba(6,182,212,0.35)]',
          pulseScale: [0.98, 1.04, 0.98],
        };
      case 'speaking':
        return {
          coreGlow: 'from-purple-300/50 via-violet-600/40 to-indigo-950',
          borderColor: 'border-purple-400/70 shadow-glow-purple-lg',
          pulseScale: [1, 1.12, 1],
        };
      case 'interrupted':
        return {
          coreGlow: 'from-amber-400/30 via-purple-900/30 to-slate-950',
          borderColor: 'border-amber-400/50 shadow-[0_0_20px_rgba(245,158,11,0.25)]',
          pulseScale: 1,
        };
      case 'error':
        return {
          coreGlow: 'from-rose-500/30 via-slate-900 to-black',
          borderColor: 'border-rose-500/50 shadow-[0_0_20px_rgba(244,63,94,0.3)]',
          pulseScale: 1,
        };
      default: // idle
        return {
          coreGlow: 'from-purple-400/30 via-[#1C123D] to-[#0A0718]',
          borderColor: 'border-purple-400/40 shadow-glow-purple',
          pulseScale: [1, 1.06, 1],
        };
    }
  };

  const currentStyle = getOrbStateStyles();

  return (
    <div
      onClick={onClick}
      className="relative flex items-center justify-center cursor-pointer group select-none"
      title="FinSight Core Intelligence Orb"
    >
      {/* Outer Atmospheric Aura (Soft Violet Ambient Reflection) */}
      <motion.div
        animate={
          shouldReduceMotion
            ? {}
            : {
                scale: currentStyle.pulseScale,
                opacity: state === 'listening' || state === 'speaking' ? [0.5, 0.85, 0.5] : [0.3, 0.55, 0.3],
              }
        }
        transition={{ duration: 2.2, repeat: Infinity, ease: 'easeInOut' }}
        className="absolute w-28 h-28 rounded-full bg-gradient-to-tr from-purple-600/30 via-violet-500/20 to-cyan-400/10 blur-xl pointer-events-none"
      />

      {/* Outer Layered Metallic Concentric Rings */}
      <motion.div
        animate={
          state === 'processing'
            ? { rotate: 360 }
            : shouldReduceMotion
            ? {}
            : { rotate: 360 }
        }
        transition={{
          duration: state === 'processing' ? 2.5 : 24,
          repeat: Infinity,
          ease: 'linear',
        }}
        className="absolute w-24 h-24 rounded-full border border-dashed border-purple-400/25 pointer-events-none"
      />

      <motion.div
        animate={shouldReduceMotion ? {} : { rotate: -360 }}
        transition={{ duration: 32, repeat: Infinity, ease: 'linear' }}
        className="absolute w-26 h-26 rounded-full border border-purple-500/15 pointer-events-none"
      />

      {/* Main Glass Sphere with Refined Specular Highlights */}
      <motion.div
        animate={
          shouldReduceMotion
            ? {}
            : {
                scale: state === 'speaking' ? [1, 1.05, 1] : 1,
              }
        }
        transition={{ duration: 0.6, repeat: Infinity }}
        className={`relative w-16 h-16 rounded-full bg-gradient-to-br ${currentStyle.coreGlow} border ${currentStyle.borderColor} flex items-center justify-center backdrop-blur-md overflow-hidden transition-all duration-300 group-hover:scale-105`}
      >
        {/* Curved Glass Specular Highlight (Reflection of light on sphere) */}
        <div className="absolute top-1 left-2.5 w-8 h-3.5 rounded-full bg-white/25 blur-[1px] -rotate-[30deg] pointer-events-none" />
        <div className="absolute bottom-1 right-2.5 w-6 h-2 rounded-full bg-purple-300/10 blur-[1px] rotate-[20deg] pointer-events-none" />

        {/* State Icon in Center */}
        <div className="relative z-10 transition-transform duration-200">
          {state === 'listening' ? (
            <Mic className="w-6 h-6 text-emerald-300 animate-pulse" />
          ) : state === 'processing' ? (
            <Loader2 className="w-6 h-6 text-cyan-300 animate-spin" />
          ) : state === 'speaking' ? (
            <Volume2 className="w-6 h-6 text-purple-200 animate-pulse" />
          ) : state === 'interrupted' ? (
            <Pause className="w-6 h-6 text-amber-300" />
          ) : state === 'error' ? (
            <AlertCircle className="w-6 h-6 text-rose-300" />
          ) : (
            <Sparkles className="w-6 h-6 text-purple-200 group-hover:rotate-12 transition-transform" />
          )}
        </div>

        {/* Inner Pulsing Core Energy */}
        <motion.div
          animate={
            shouldReduceMotion
              ? {}
              : {
                  scale: state === 'listening' ? [0.9, 1.25, 0.9] : [0.95, 1.1, 0.95],
                  opacity: state === 'listening' ? [0.5, 0.9, 0.5] : [0.3, 0.6, 0.3],
                }
          }
          transition={{ duration: 1.4, repeat: Infinity, ease: 'easeInOut' }}
          className="absolute inset-1 rounded-full bg-purple-500/20 blur-sm pointer-events-none"
        />
      </motion.div>
    </div>
  );
};
