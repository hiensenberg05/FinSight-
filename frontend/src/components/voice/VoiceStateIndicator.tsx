import React from 'react';
import { VoiceState } from '../../types';
import { Mic, Volume2, Loader2, Sparkles, AlertCircle, Pause } from 'lucide-react';

interface VoiceStateIndicatorProps {
  state: VoiceState;
  showText?: boolean;
}

export const VoiceStateIndicator: React.FC<VoiceStateIndicatorProps> = ({
  state,
  showText = true,
}) => {
  const getConfig = () => {
    switch (state) {
      case 'listening':
        return {
          label: 'Gnani Prisma STT: Listening',
          color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
          dot: 'bg-emerald-400 animate-ping',
          icon: Mic,
        };
      case 'processing':
        return {
          label: 'Reasoning & Tool Execution',
          color: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30',
          dot: 'bg-cyan-400 animate-pulse',
          icon: Loader2,
        };
      case 'speaking':
        return {
          label: 'Gnani Timbre TTS: Speaking',
          color: 'text-purple-300 bg-purple-500/15 border-purple-500/30',
          dot: 'bg-purple-400 animate-pulse',
          icon: Volume2,
        };
      case 'interrupted':
        return {
          label: 'Speech Paused',
          color: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
          dot: 'bg-amber-400',
          icon: Pause,
        };
      case 'error':
        return {
          label: 'Voice Pipeline Error',
          color: 'text-rose-400 bg-rose-500/10 border-rose-500/30',
          dot: 'bg-rose-400',
          icon: AlertCircle,
        };
      default:
        return {
          label: 'Voice Engine Ready',
          color: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
          dot: 'bg-purple-400',
          icon: Sparkles,
        };
    }
  };

  const { label, color, dot, icon: Icon } = getConfig();

  return (
    <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium border backdrop-blur-sm transition-all ${color}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dot}`} />
      <Icon className={`w-3 h-3 ${state === 'processing' ? 'animate-spin' : ''}`} />
      {showText && <span>{label}</span>}
    </div>
  );
};
