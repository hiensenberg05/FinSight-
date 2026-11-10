import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { ChatMessage } from '../../types';
import { ArrowRight, Bot, User, ShieldCheck, ExternalLink } from 'lucide-react';
import { SpendingDonutChart } from './SpendingDonutChart';
import { ActionConfirmationCard } from './ActionConfirmationCard';
import { InteractiveSimulationCard } from './InteractiveSimulationCard';
import { useVoice } from '../../voice/VoiceContext';

interface AnimatedMessageProps {
  message: ChatMessage;
  onActionClick?: (action: string) => void;
}

export const AnimatedMessage: React.FC<AnimatedMessageProps> = ({
  message,
  onActionClick,
}) => {
  const shouldReduceMotion = useReducedMotion();
  const isUser = message.sender === 'user';
  const {
    openEvidenceDrawer,
    confirmActionProposal,
    cancelActionProposal,
    adjustSimulationSlider,
  } = useVoice();

  return (
    <motion.div
      initial={{
        opacity: 0,
        y: shouldReduceMotion ? 0 : 12,
        scale: shouldReduceMotion ? 1 : 0.98,
      }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.28, ease: 'easeOut' }}
      className={`flex flex-col w-full ${isUser ? 'items-end' : 'items-start'}`}
    >
      {/* Message Bubble Container */}
      <div
        className={`relative max-w-[86%] rounded-2xl px-4.5 py-3 text-xs sm:text-sm leading-relaxed transition-all ${
          isUser
            ? 'bg-gradient-to-r from-[#241747] to-[#1E163B] border border-purple-500/40 text-purple-100 rounded-tr-sm shadow-glow-purple border-t-purple-400/50'
            : 'bg-[#12182B] border border-slate-700/60 text-slate-200 rounded-tl-sm shadow-panel border-t-white/10 ring-1 ring-inset ring-white/[0.04]'
        }`}
      >
        {/* Subtle Sender Badge */}
        <div className="flex items-center gap-1.5 mb-1.5 opacity-60 text-[10px] uppercase font-bold tracking-wider">
          {isUser ? (
            <>
              <span>You</span>
              <User className="w-2.5 h-2.5" />
            </>
          ) : (
            <>
              <Bot className="w-2.5 h-2.5 text-purple-400" />
              <span className="text-purple-300">FinSight Assistant</span>
            </>
          )}
        </div>

        {/* Message Text */}
        <p className="whitespace-pre-wrap">{message.text}</p>

        {/* Verified Data Provenance Badge */}
        {!isUser && message.evidence && message.evidence.length > 0 && (
          <div className="mt-2.5 pt-2 border-t border-slate-800/80 flex items-center">
            <button
              onClick={() => openEvidenceDrawer(message.evidence)}
              className="inline-flex items-center gap-1.5 text-[11px] font-medium text-emerald-300 bg-emerald-500/15 hover:bg-emerald-500/25 border border-emerald-500/30 px-2.5 py-1 rounded-full transition-all cursor-pointer shadow-sm"
              title="Click to view underlying database transactions"
            >
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Verified from {message.evidence.length} transactions</span>
              <ExternalLink className="w-2.5 h-2.5 opacity-60 ml-0.5" />
            </button>
          </div>
        )}

        {/* Action Buttons (Inside Assistant Message) */}
        {message.quickActions && message.quickActions.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3 pt-2.5 border-t border-slate-700/50">
            {message.quickActions.map((action, idx) => (
              <button
                key={idx}
                onClick={() => onActionClick?.(action.action)}
                className={`text-xs px-3.5 py-1.5 rounded-full font-medium transition-all flex items-center gap-1.5 cursor-pointer ${
                  action.primary
                    ? 'bg-purple-600/35 hover:bg-purple-600/50 text-purple-200 border border-purple-400/40 shadow-sm'
                    : 'bg-slate-800/80 hover:bg-slate-800 text-slate-300 border border-slate-700/60'
                }`}
              >
                <span>{action.label}</span>
                {action.primary && <ArrowRight className="w-3 h-3 text-purple-300" />}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Action Operator Confirmation Card */}
      {message.actionProposal && (
        <div className="w-full max-w-[86%] mt-1">
          <ActionConfirmationCard
            proposal={message.actionProposal}
            onConfirm={confirmActionProposal}
            onCancel={cancelActionProposal}
          />
        </div>
      )}

      {/* Interactive What-If Simulation Card */}
      {message.simulationData && (
        <div className="w-full max-w-[86%] mt-1">
          <InteractiveSimulationCard
            initialData={message.simulationData}
            onSliderChange={adjustSimulationSlider}
          />
        </div>
      )}

      {/* In-Line Generative Financial Chart */}
      {message.chartData && !message.simulationData && (
        <motion.div
          initial={{ opacity: 0, scale: 0.96, y: 8 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.1 }}
          className="w-full max-w-[94%] mt-2.5"
        >
          <SpendingDonutChart
            data={message.chartData}
            title={message.chartTitle}
          />
        </motion.div>
      )}

      {/* Timestamp */}
      <span className="text-[10px] text-slate-500 mt-1 px-1.5 font-mono">
        {message.timestamp}
      </span>
    </motion.div>
  );
};
