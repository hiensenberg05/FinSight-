import React from 'react';

interface LiveWaveformBarsProps {
  isActive: boolean;
  audioLevel?: number; // 0.0 to 1.0
  barCount?: number;
  height?: number; // Max height in px (default 36)
  colorTheme?: 'cyan' | 'violet' | 'gradient';
  className?: string;
}

// Symmetrical height multiplier template matching pin_preview.jpg
const baseMultiplier = [
  0.4, 0.7, 0.5, 0.9, 0.6, 1.0, 0.5, 0.8, 0.4, 0.9, 
  0.5, 1.0, 0.6, 0.9, 0.5, 0.7, 0.4
];

export const LiveWaveformBars: React.FC<LiveWaveformBarsProps> = ({
  isActive,
  audioLevel = 0,
  barCount = 17,
  height = 36,
  colorTheme = 'cyan',
  className = '',
}) => {
  return (
    <div className={`flex items-center justify-center gap-[3px] select-none ${className}`}>
      {Array.from({ length: barCount }).map((_, i) => {
        // Individualized wave harmonic for each bar
        const mult = baseMultiplier[i % baseMultiplier.length] || 0.6;
        const measuredLevel = isActive ? Math.min(1, Math.max(0, audioLevel)) : 0;
        const barHeight = Math.max(2, Math.min(height, 2 + measuredLevel * height * mult));

        // Color & Glow styles inspired by pin_preview.jpg (electric neon blue & cyan)
        const getBarColor = () => {
          if (!isActive) return '#3B82F6/40';
          if (colorTheme === 'violet') return '#8B5CF6';
          if (colorTheme === 'gradient') {
            return i < barCount / 2 ? '#38BDF8' : '#8B5CF6';
          }
          // Default neon electric cyan/blue
          return '#38BDF8';
        };

        const barColor = getBarColor();

        return (
          <div
            key={i}
            className="w-[3px] rounded-full transition-all duration-75"
            style={{
              height: `${barHeight}px`,
              backgroundColor: isActive && measuredLevel > 0.03 ? barColor : 'rgba(147, 197, 253, 0.35)',
              boxShadow: isActive && measuredLevel > 0.03
                ? '0 0 8px rgba(56, 189, 248, 0.75), 0 0 16px rgba(6, 182, 212, 0.4)'
                : 'none',
            }}
          />
        );
      })}
    </div>
  );
};
