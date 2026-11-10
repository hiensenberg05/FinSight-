import React, { useRef, useEffect } from 'react';
import { AnimatePresence } from 'framer-motion';
import { ChatMessage, VoiceState } from '../../types';
import { AssistantAvatar } from '../voice/AssistantAvatar';
import { QuickActionChips } from './QuickActionChips';
import { AnimatedMessage } from './AnimatedMessage';
import { MessageComposer } from './MessageComposer';
import { AgentActivityIndicator } from '../voice/AgentActivityIndicator';
import { VoiceStateIndicator } from '../voice/VoiceStateIndicator';

interface ConversationalPanelProps {
  userName?: string;
  messages: ChatMessage[];
  voiceState: VoiceState;
  audioLevel?: number;
  errorMessage?: string | null;
  onSendMessage: (text: string) => void;
  onToggleVoice: () => void;
  onActionClick?: (action: string) => void;
}

export const ConversationalPanel: React.FC<ConversationalPanelProps> = ({
  userName = 'Aarav',
  messages,
  voiceState,
  audioLevel = 0,
  errorMessage,
  onSendMessage,
  onToggleVoice,
  onActionClick,
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll on new messages or state changes
  useEffect(() => {
    const scrollToBottom = () => {
      if (scrollRef.current) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      }
    };
    scrollToBottom();
    const timer = setTimeout(scrollToBottom, 80);
    return () => clearTimeout(timer);
  }, [messages, voiceState]);

  return (
    <div className="relative flex flex-col h-full min-h-0 bg-[#0E1322] border border-slate-800/80 border-t-white/10 rounded-2xl overflow-hidden shadow-panel ring-1 ring-inset ring-white/[0.04]">
      {/* Background Ambient Lighting (Purple/Violet Beam) */}
      <div className="absolute top-0 right-1/4 w-80 h-96 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Top Conversational Header with Assistant Avatar (Matching Reference Screenshot) */}
      <div className="relative px-5 pt-4 pb-2.5 border-b border-slate-800/70 bg-[#0E1322]/90 backdrop-blur-md z-10 flex-shrink-0">
        <div className="flex items-start justify-between gap-4">
          {/* Greeting Text */}
          <div className="flex-1 max-w-[68%]">
            <div className="flex items-center gap-2 mb-1">
              <VoiceStateIndicator state={voiceState} />
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              Hey, {userName}!
              <span className="inline-block text-purple-400 animate-pulse text-lg">✦</span>
            </h2>
            <p className="text-xs sm:text-sm text-slate-400 mt-0.5 leading-snug">
              How can I help you with your finances today?
            </p>
          </div>

          {/* Futuristic Metallic Assistant Avatar with Glowing Beam */}
          <div className="flex-shrink-0 -mt-2">
            <AssistantAvatar
              state={voiceState}
              audioLevel={audioLevel}
              onClick={onToggleVoice}
            />
          </div>
        </div>

        {/* Quick Action Chips */}
        <div className="mt-2.5">
          <QuickActionChips onSelectAction={(query) => onSendMessage(query)} />
        </div>
      </div>

      {/* Scrollable Conversation Stream */}
      <div
        ref={(el) => {
          scrollRef.current = el;
          if (el) el.scrollTop = el.scrollHeight;
        }}
        className="flex-1 min-h-0 overflow-y-auto px-5 py-3 space-y-3 scroll-smooth"
      >
        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <AnimatedMessage
              key={msg.id}
              message={msg}
              onActionClick={onActionClick}
            />
          ))}
        </AnimatePresence>

        {/* Multi-step Thinking / Tool Execution Indicator */}
        {voiceState === 'processing' && (
          <AgentActivityIndicator />
        )}
      </div>

      {/* Bottom Message Composer (Anchored) */}
      <div className="p-3.5 border-t border-slate-800/70 bg-[#0E1322]/95 backdrop-blur-md flex-shrink-0 z-10">
        <MessageComposer
          onSendMessage={onSendMessage}
          voiceState={voiceState}
          audioLevel={audioLevel}
          errorMessage={errorMessage}
          onToggleVoice={onToggleVoice}
        />
      </div>
    </div>
  );
};
