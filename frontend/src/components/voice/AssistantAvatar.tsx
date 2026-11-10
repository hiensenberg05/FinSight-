import React from 'react';
import { motion, useReducedMotion, Variants } from 'framer-motion';
import { VoiceState } from '../../types';

interface AssistantAvatarProps {
  state: VoiceState;
  audioLevel?: number;
  onClick?: () => void;
}

export const AssistantAvatar: React.FC<AssistantAvatarProps> = ({
  state,
  audioLevel = 0,
  onClick,
}) => {
  const shouldReduceMotion = useReducedMotion();

  // Floating animation configs based on state
  const floatVariants: Variants = {
    idle: {
      y: shouldReduceMotion ? 0 : [0, -6, 0],
      rotate: shouldReduceMotion ? 0 : [0, 1, -1, 0],
      transition: { duration: 4, repeat: Infinity, ease: 'easeInOut' as const },
    },
    listening: {
      y: shouldReduceMotion ? 0 : [0, -4, 0],
      scale: 1.05,
      transition: { duration: 1.8, repeat: Infinity, ease: 'easeInOut' as const },
    },
    processing: {
      y: shouldReduceMotion ? 0 : [-2, 2, -2],
      rotate: shouldReduceMotion ? 0 : [-2, 2, -2],
      transition: { duration: 1.2, repeat: Infinity, ease: 'easeInOut' as const },
    },
    speaking: {
      y: shouldReduceMotion ? 0 : [0, -7, 0],
      transition: { duration: 2, repeat: Infinity, ease: 'easeInOut' as const },
    },
    interrupted: {
      y: 0,
      rotate: 0,
      scale: 1,
      transition: { duration: 0.3 },
    },
    error: {
      y: [0, -2, 2, 0],
      transition: { duration: 0.4 },
    },
  };

  // Status tag configuration
  const getStatusConfig = () => {
    switch (state) {
      case 'listening':
        return { label: 'Listening', bg: 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300', dot: 'bg-emerald-400 animate-ping' };
      case 'processing':
        return { label: 'Thinking', bg: 'bg-cyan-500/15 border-cyan-500/40 text-cyan-300', dot: 'bg-cyan-400 animate-pulse' };
      case 'speaking':
        return { label: 'Speaking', bg: 'bg-purple-500/20 border-purple-400/50 text-purple-200', dot: 'bg-purple-400 animate-pulse' };
      case 'error':
        return { label: 'Mic Error', bg: 'bg-rose-500/20 border-rose-500/40 text-rose-300', dot: 'bg-rose-400' };
      case 'interrupted':
        return { label: 'Paused', bg: 'bg-amber-500/15 border-amber-500/40 text-amber-300', dot: 'bg-amber-400' };
      default:
        return { label: 'Active', bg: 'bg-purple-900/30 border-purple-500/30 text-purple-300', dot: 'bg-purple-400' };
    }
  };

  const status = getStatusConfig();
  const isSpeaking = state === 'speaking';
  const isListening = state === 'listening';
  const isProcessing = state === 'processing';

  return (
    <div 
      onClick={onClick}
      className="relative flex flex-col items-center justify-center select-none cursor-pointer group"
      title="Click to interact with FinSight Voice Assistant"
    >
      {/* Top Status Capsule (Matching Reference "Active" pill) */}
      <div className="absolute -top-3 right-0 z-30">
        <div className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-semibold border backdrop-blur-md shadow-sm transition-all duration-300 ${status.bg}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${status.dot}`} />
          {status.label}
        </div>
      </div>

      {/* Atmospheric Vertical Ambient Light Beam (from reference screenshot) */}
      <div className="absolute top-12 w-48 h-64 pointer-events-none overflow-hidden flex justify-center -z-10">
        <motion.div
          animate={{
            opacity: isSpeaking || isListening ? [0.65, 0.95, 0.65] : [0.35, 0.55, 0.35],
            scaleX: isListening ? [1, 1.35, 1] : [1, 1.15, 1],
          }}
          transition={{ duration: 2.8, repeat: Infinity, ease: 'easeInOut' }}
          className="w-28 h-full bg-gradient-to-b from-purple-500/50 via-violet-600/25 to-transparent blur-2xl"
        />
      </div>

      {/* Floating Metallic Assistant Body */}
      <motion.div
        variants={floatVariants}
        animate={state}
        className="relative w-24 h-28 flex items-center justify-center"
      >
        <svg
          viewBox="0 0 120 140"
          className="w-full h-full drop-shadow-[0_10px_20px_rgba(124,58,237,0.4)]"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Definitions for Metallic Materials & Glows */}
          <defs>
            {/* White/Silver Metallic Chrome Gradient */}
            <linearGradient id="metallicHead" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#FFFFFF" />
              <stop offset="35%" stopColor="#E2E8F0" />
              <stop offset="70%" stopColor="#CBD5E1" />
              <stop offset="100%" stopColor="#94A3B8" />
            </linearGradient>

            <linearGradient id="metallicTorso" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#F8FAFC" />
              <stop offset="45%" stopColor="#E2E8F0" />
              <stop offset="85%" stopColor="#94A3B8" />
              <stop offset="100%" stopColor="#64748B" />
            </linearGradient>

            {/* Dark Glossy Obsidian Visor */}
            <linearGradient id="visorGlass" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#1E1B4B" />
              <stop offset="60%" stopColor="#0B0F19" />
              <stop offset="100%" stopColor="#030712" />
            </linearGradient>

            {/* Glowing Purple Core */}
            <radialGradient id="reactorGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#E9D5FF" />
              <stop offset="40%" stopColor="#A855F7" />
              <stop offset="80%" stopColor="#7C3AED" />
              <stop offset="100%" stopColor="#4C1D95" />
            </radialGradient>

            {/* Specular Highlight */}
            <linearGradient id="specular" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#FFFFFF" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#FFFFFF" stopOpacity="0" />
            </linearGradient>

            {/* Filter for Ambient Violet Glow */}
            <filter id="coreBlur" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* 1. Thruster Glow at base */}
          <motion.ellipse
            cx="60"
            cy="125"
            rx={isSpeaking ? 16 : 12}
            ry={isSpeaking ? 7 : 5}
            fill="#A855F7"
            opacity={isSpeaking ? 0.9 : 0.6}
            filter="url(#coreBlur)"
            animate={{
              rx: isSpeaking ? [12, 18, 12] : [10, 14, 10],
              opacity: isSpeaking ? [0.7, 1, 0.7] : [0.5, 0.8, 0.5],
            }}
            transition={{ duration: 0.8, repeat: Infinity }}
          />

          {/* 2. Floating Antenna / Sensor Node */}
          <circle cx="60" cy="14" r="3.5" fill="#C084FC" />
          <line x1="60" y1="17" x2="60" y2="23" stroke="#94A3B8" strokeWidth="2" strokeLinecap="round" />
          <motion.circle
            cx="60"
            cy="14"
            r="5"
            stroke="#A855F7"
            strokeWidth="1"
            fill="none"
            animate={{ scale: [1, 1.8, 1], opacity: [0.8, 0, 0.8] }}
            transition={{ duration: 1.8, repeat: Infinity }}
          />

          {/* 3. Metallic Head Chassis */}
          <rect
            x="32"
            y="23"
            width="56"
            height="46"
            rx="18"
            fill="url(#metallicHead)"
            stroke="#FFFFFF"
            strokeWidth="1.2"
          />

          {/* Head Specular Top Edge */}
          <path
            d="M38 25 C45 23.5, 75 23.5, 82 25"
            stroke="url(#specular)"
            strokeWidth="2.5"
            strokeLinecap="round"
          />

          {/* Ear / Headset Accent Nodes with Violet Glow */}
          <rect x="27" y="38" width="5" height="16" rx="2.5" fill="#64748B" />
          <rect x="26" y="41" width="3" height="10" rx="1.5" fill="#A855F7" />
          <rect x="88" y="38" width="5" height="16" rx="2.5" fill="#64748B" />
          <rect x="91" y="41" width="3" height="10" rx="1.5" fill="#A855F7" />

          {/* 4. Glossy Obsidian Visor Faceplate */}
          <rect
            x="38"
            y="32"
            width="44"
            height="28"
            rx="10"
            fill="url(#visorGlass)"
            stroke="#334155"
            strokeWidth="1"
          />

          {/* Visor Specular Sheen (Curved highlight reflection) */}
          <path
            d="M42 35 C50 33, 70 33, 78 35"
            stroke="white"
            strokeOpacity="0.45"
            strokeWidth="1.5"
            strokeLinecap="round"
          />

          {/* 5. Expressive Glowing Eyes (Reacts to voice state) */}
          <g>
            {isProcessing ? (
              // Thinking Orbit Ring in Visor
              <motion.circle
                cx="60"
                cy="46"
                r="7"
                stroke="#38BDF8"
                strokeWidth="2"
                strokeDasharray="14 6"
                fill="none"
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              />
            ) : isListening ? (
              // Alert Listening Eyes (Cyan/Violet Slits)
              <>
                <motion.rect
                  x="45"
                  y="42"
                  width="10"
                  height="8"
                  rx="3"
                  fill="#38BDF8"
                  filter="url(#coreBlur)"
                  animate={{ scaleY: [1, 1.25, 1] }}
                  transition={{ duration: 0.8, repeat: Infinity }}
                />
                <motion.rect
                  x="65"
                  y="42"
                  width="10"
                  height="8"
                  rx="3"
                  fill="#38BDF8"
                  filter="url(#coreBlur)"
                  animate={{ scaleY: [1, 1.25, 1] }}
                  transition={{ duration: 0.8, repeat: Infinity }}
                />
              </>
            ) : isSpeaking ? (
              // Speaking Wave Eyes/Visor Audio Display
              <>
                <ellipse cx="49" cy="45" rx="5" ry="6" fill="#C084FC" filter="url(#coreBlur)" />
                <ellipse cx="71" cy="45" rx="5" ry="6" fill="#C084FC" filter="url(#coreBlur)" />
                <motion.line
                  x1="54"
                  y1="53"
                  x2="66"
                  y2="53"
                  stroke="#E9D5FF"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  animate={{ scaleX: [0.8, 1.2, 0.8] }}
                  transition={{ duration: 0.35, repeat: Infinity }}
                />
              </>
            ) : (
              // Friendly Idle Visor Eyes
              <>
                <ellipse cx="49" cy="45" rx="4.5" ry="5.5" fill="#A855F7" />
                <ellipse cx="71" cy="45" rx="4.5" ry="5.5" fill="#A855F7" />
                <circle cx="50" cy="43.5" r="1.5" fill="#FFFFFF" />
                <circle cx="72" cy="43.5" r="1.5" fill="#FFFFFF" />
              </>
            )}
          </g>

          {/* 6. Articulated Metallic Neck */}
          <path d="M52 69 L68 69 L65 74 L55 74 Z" fill="#475569" />

          {/* 7. Metallic Torso Body & Articulated Shoulders */}
          <path
            d="M34 80 C34 75, 42 74, 60 74 C78 74, 86 75, 86 80 L80 114 C80 118, 72 120, 60 120 C48 120, 40 118, 40 114 Z"
            fill="url(#metallicTorso)"
            stroke="#CBD5E1"
            strokeWidth="1.2"
          />

          {/* Articulated Shoulder Spheres */}
          <circle cx="31" cy="85" r="7" fill="url(#metallicHead)" stroke="#FFFFFF" strokeWidth="1" />
          <circle cx="89" cy="85" r="7" fill="url(#metallicHead)" stroke="#FFFFFF" strokeWidth="1" />

          {/* Chest Inset Panel */}
          <path
            d="M46 82 L74 82 L70 108 L50 108 Z"
            fill="#1E293B"
            stroke="#475569"
            strokeWidth="1"
          />

          {/* 8. Glowing Violet Chest Reactor Core */}
          <circle cx="60" cy="94" r="7.5" fill="url(#reactorGlow)" filter="url(#coreBlur)" />
          <circle cx="60" cy="94" r="4" fill="#FFFFFF" />
          <motion.circle
            cx="60"
            cy="94"
            r="9"
            stroke="#C084FC"
            strokeWidth="1.2"
            fill="none"
            animate={{
              scale: isSpeaking || isListening ? [1, 1.3, 1] : [1, 1.15, 1],
              opacity: [0.6, 1, 0.6],
            }}
            transition={{ duration: 1.5, repeat: Infinity }}
          />

          {/* Floating Lower Chassis / Propulsion Emitter */}
          <ellipse cx="60" cy="118" rx="14" ry="4" fill="#334155" />
          <ellipse cx="60" cy="119" rx="8" ry="2.5" fill="#7C3AED" />
        </svg>
      </motion.div>
    </div>
  );
};
