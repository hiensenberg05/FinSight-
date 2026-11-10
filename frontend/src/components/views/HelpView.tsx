import React from 'react';
import { HelpCircle, Mic, Terminal, Sparkles, CheckCircle2 } from 'lucide-react';

export const HelpView: React.FC = () => {
  const samplePrompts = [
    { query: "Why did I spend ₹8,000 more this month?", desc: "Flagship Hackathon Demo: Triggers period comparison tool, detects dining spike & unusual electronic purchase." },
    { query: "How much did I spend through UPI?", desc: "Calculates total UPI volume and ranks top merchants (Swiggy, Uber, Blinkit)." },
    { query: "Which merchant receives most of my money?", desc: "Ranks merchants by cumulative debit value." },
    { query: "Can I save ₹50,000 in six months?", desc: "Simulates savings targets against discretionary cash-flow." },
    { query: "What are my upcoming recurring payments?", desc: "Lists due subscriptions, broadband, and utility bills." },
    { query: "Find unusual transactions.", desc: "Executes Isolation Forest anomaly detector on transaction history." },
  ];

  return (
    <div className="h-full overflow-y-auto space-y-4 pr-1 scroll-smooth">
      {/* Top Banner */}
      <div className="bg-[#0E1322] border border-slate-700/60 border-t-white/10 rounded-2xl p-5 shadow-panel ring-1 ring-inset ring-white/[0.04]">
        <span className="text-[11px] font-bold text-purple-400 uppercase tracking-widest block mb-1">
          FinSight Documentation & Assistance
        </span>
        <h2 className="text-xl font-bold text-white tracking-tight">Help, FAQs & Voice Cheat Sheet</h2>
        <p className="text-xs text-slate-400 mt-0.5">Explore sample voice queries and architecture overview</p>
      </div>

      {/* Voice Prompts Showcase */}
      <div className="bg-[#0E1322] border border-slate-700/60 rounded-2xl p-5 shadow-panel">
        <h3 className="text-sm font-bold text-white mb-1 flex items-center gap-2">
          <Mic className="w-4 h-4 text-purple-400" />
          Recommended Voice Prompts for Live Demo
        </h3>
        <p className="text-xs text-slate-400 mb-4">You can speak these exact queries or type them into the assistant</p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {samplePrompts.map((p, idx) => (
            <div key={idx} className="p-3.5 rounded-xl bg-[#141A2D] border border-slate-700/60 hover:border-purple-500/40 transition-colors">
              <span className="text-xs font-bold text-purple-300 block mb-1">"{p.query}"</span>
              <p className="text-[11px] text-slate-400 leading-relaxed">{p.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Hackathon Architecture Card */}
      <div className="bg-[#0E1322] border border-slate-700/60 rounded-2xl p-5 shadow-panel">
        <h3 className="text-sm font-bold text-white mb-2 flex items-center gap-2">
          <Terminal className="w-4 h-4 text-cyan-400" />
          FinSight System Principles
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
            <h4 className="font-bold text-purple-300 mb-1">1. Zero Hallucinations</h4>
            <p className="text-[11px] text-slate-400">All numbers computed deterministically by Python/Pandas tools, never guessed by LLM.</p>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
            <h4 className="font-bold text-cyan-300 mb-1">2. Gnani Native Voice</h4>
            <p className="text-[11px] text-slate-400">Prisma STT for speech transcription and Timbre TTS for natural vocal response.</p>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800">
            <h4 className="font-bold text-emerald-300 mb-1">3. Privacy-First</h4>
            <p className="text-[11px] text-slate-400">Bank CSV statements remain securely on the user's backend, preserving banking secrecy.</p>
          </div>
        </div>
      </div>
    </div>
  );
};
