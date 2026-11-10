import React from 'react';
import { motion } from 'framer-motion';

export interface TabOption {
  id: string;
  label: string;
  icon?: React.ElementType;
}

interface GlidingTabsProps {
  tabs: TabOption[];
  activeTab: string;
  onChange: (tabId: string) => void;
  layoutId?: string;
  size?: 'sm' | 'md';
}

export const GlidingTabs: React.FC<GlidingTabsProps> = ({
  tabs,
  activeTab,
  onChange,
  layoutId = 'gliding-pill-indicator',
  size = 'md',
}) => {
  return (
    <div className="inline-flex items-center p-1 rounded-xl bg-[#0C0B14] border border-white/[0.06] shadow-[inset_0_1px_1px_rgba(0,0,0,0.6)]">
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        const Icon = tab.icon;

        return (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className={`relative flex items-center gap-1.5 font-medium rounded-lg transition-colors select-none z-10 ${
              size === 'sm' ? 'px-2.5 py-1 text-[11px]' : 'px-3.5 py-1.5 text-xs'
            } ${
              isActive
                ? 'text-white'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            {Icon && <Icon className="w-3.5 h-3.5" />}
            <span>{tab.label}</span>

            {/* Framer Motion Gliding Pill Indicator */}
            {isActive && (
              <motion.div
                layoutId={layoutId}
                transition={{ type: 'spring', stiffness: 500, damping: 35 }}
                className="absolute inset-0 rounded-lg bg-gradient-to-b from-violet-600/35 to-violet-700/15 border border-violet-400/40 shadow-[inset_0_1px_0_rgba(255,255,255,0.25),0_0_16px_rgba(139,92,246,0.25)] -z-10"
              />
            )}
          </button>
        );
      })}
    </div>
  );
};
