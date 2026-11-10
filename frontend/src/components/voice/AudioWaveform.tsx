import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';

interface AudioWaveformProps {
  active: boolean;
  audioLevel?: number; // 0.0 - 1.0 from Web Audio API
  color?: string;
  barsCount?: number;
}

export const AudioWaveform: React.FC<AudioWaveformProps> = ({
  active,
  audioLevel = 0,
  color = 'bg-purple-400',
  barsCount = 16,
}) => {
  const shouldReduceMotion = useReducedMotion();

  return (
    <div className="flex items-center justify-center gap-[2.5px] h-6 px-2 select-none">
      {Array.from({ length: barsCount }).map((_, i) => {
        // Compute dynamic height based on audioLevel + sine pattern
        const dynamicFactor = Math.sin((i / barsCount) * Math.PI);
        const dynamicHeight = active
          ? Math.max(2, Math.min(22, 2 + audioLevel * 20 * dynamicFactor))
          : 2;

        return (
          <motion.span
            key={i}
            className={`w-[2px] rounded-full transition-all duration-75 ${color}`}
            style={{
              height: `${dynamicHeight}px`,
              opacity: active ? 0.75 + dynamicFactor * 0.25 : 0.25,
            }}
            animate={undefined}
            transition={{ duration: shouldReduceMotion ? 0 : 0.075 }}
          />
        );
      })}
    </div>
  );
};
