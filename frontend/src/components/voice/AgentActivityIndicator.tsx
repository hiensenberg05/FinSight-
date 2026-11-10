import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Database, Calculator, Sparkles, Check, Compass, ShieldCheck, Cpu } from 'lucide-react';
import { useVoice } from '../../voice/VoiceContext';

interface AgentActivityIndicatorProps {
  queryText?: string;
  onComplete?: () => void;
}

export const AgentActivityIndicator: React.FC<AgentActivityIndicatorProps> = () => {
  const { executionStages, activeToolCall } = useVoice();

  // Standard ordered pipeline stages
  const defaultStages = [
    {
      id: 'intent_identified',
      defaultLabel: 'Identifying user intent & conversational context...',
      icon: Compass,
    },
    {
      id: 'tool_invoked',
      defaultLabel: activeToolCall ? `Selected tool: ${activeToolCall.tool}` : 'Selecting deterministic financial tool...',
      icon: Cpu,
    },
    {
      id: 'records_processed',
      defaultLabel: 'Querying & processing verified ledger transactions...',
      icon: Database,
    },
    {
      id: 'math_calculated',
      defaultLabel: 'Verifying deterministic financial calculations (zero LLM math)...',
      icon: Calculator,
    },
    {
      id: 'evidence_generated',
      defaultLabel: 'Generating audit provenance & citation references...',
      icon: ShieldCheck,
    },
  ];

  // Map backend stages
  const stageMap = new Map(executionStages.map((s) => [s.stage, s]));
  const currentStageIndex = executionStages.length > 0 ? executionStages.length - 1 : 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -6, scale: 0.98 }}
      transition={{ duration: 0.2 }}
      className="w-full max-w-md bg-[#12182B]/95 border border-purple-500/30 rounded-2xl p-3.5 my-2 backdrop-blur-md shadow-glow-purple"
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-2.5 pb-2 border-b border-purple-500/20">
        <div className="w-5 h-5 rounded-full bg-purple-600/30 border border-purple-400/40 flex items-center justify-center">
          <Sparkles className="w-3 h-3 text-purple-300 animate-spin" />
        </div>
        <span className="text-xs font-semibold text-purple-200">
          FinSight Intelligence Engine
        </span>
        <span className="text-[10px] text-purple-400 font-mono ml-auto flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          Backend Driven Execution
        </span>
      </div>

      {/* Real Execution Stages */}
      <div className="space-y-2">
        {defaultStages.map((stage, idx) => {
          const Icon = stage.icon;
          const backendStage = stageMap.get(stage.id);
          const isDone = !!backendStage && (idx < currentStageIndex || backendStage.status === 'completed');
          const isCurrent = !isDone && (idx === currentStageIndex || backendStage?.status === 'in_progress');
          const isPending = !isDone && !isCurrent;

          const label = backendStage?.label || stage.defaultLabel;

          return (
            <div
              key={stage.id}
              className={`flex items-center gap-2.5 text-xs transition-all duration-300 ${
                isDone
                  ? 'text-slate-400'
                  : isCurrent
                  ? 'text-purple-200 font-medium'
                  : 'text-slate-600'
              }`}
            >
              <div
                className={`w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 transition-colors ${
                  isDone
                    ? 'bg-emerald-500/20 text-emerald-400'
                    : isCurrent
                    ? 'bg-purple-500/30 text-purple-300 ring-2 ring-purple-500/40'
                    : 'bg-slate-800 text-slate-600'
                }`}
              >
                {isDone ? (
                  <Check className="w-2.5 h-2.5" />
                ) : isCurrent ? (
                  <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-ping" />
                ) : (
                  <span className="w-1 h-1 rounded-full bg-slate-600" />
                )}
              </div>

              <Icon className="w-3.5 h-3.5 opacity-80" />
              <span className="truncate">{label}</span>
            </div>
          );
        })}
      </div>
    </motion.div>
  );
};
