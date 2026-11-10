import React, { useState } from 'react';
import { User, Shield, Key, Mic, Building2, CheckCircle2, Save, Play, Sparkles } from 'lucide-react';
import { PremiumCard } from '../common/PremiumCard';
import { useVoice, sampleVoicePrompts } from '../../voice/VoiceContext';

export const SettingsView: React.FC = () => {
  const { processQuery, isWsConnected, providerStatus, languageMode, setLanguageMode, voicePersona, setVoicePersona } = useVoice();
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="w-full max-w-[1380px] mx-auto space-y-4 pb-4">
      {/* Top Banner */}
      <PremiumCard className="p-5">
        <h2 className="text-[22px] font-extrabold text-metallic-silver tracking-tight">System & Account Settings</h2>
        <p className="text-[12.5px] text-[#8E8AA5] mt-0.5">Manage bank integrations, user profile & Gnani voice preferences</p>
      </PremiumCard>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Profile Card */}
        <PremiumCard className="p-5">
          <div className="flex items-center gap-2 mb-4">
            <User className="w-4 h-4 text-violet-400" />
            <h3 className="text-[15px] font-bold text-white">User Profile</h3>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-[#8E8AA5] block mb-1 font-medium">Full Name</label>
              <input type="text" defaultValue="Aarav Mehta" className="w-full glass-inset-tray border border-white/[0.08] focus:border-violet-500/50 rounded-xl px-3 py-2 text-white font-medium focus:outline-none shadow-inner" />
            </div>
            <div>
              <label className="text-[#8E8AA5] block mb-1 font-medium">Email Address</label>
              <input type="email" defaultValue="aarav.mehta@fintech.dev" className="w-full glass-inset-tray border border-white/[0.08] focus:border-violet-500/50 rounded-xl px-3 py-2 text-white font-medium focus:outline-none shadow-inner" />
            </div>
            <div>
              <label className="text-[#8E8AA5] block mb-1 font-medium">Primary Currency</label>
              <input type="text" defaultValue="INR (₹) - Indian Rupee" disabled className="w-full glass-inset-tray opacity-60 border border-white/[0.05] rounded-xl px-3 py-2 text-[#8E8AA5] cursor-not-allowed" />
            </div>
          </div>
        </PremiumCard>

        {/* Gnani AI Voice Settings */}
        <PremiumCard className="p-5">
          <div className="flex items-center gap-2 mb-4">
            <Mic className="w-4 h-4 text-violet-400" />
            <h3 className="text-[15px] font-bold text-white">Gnani AI Voice Configuration</h3>
            <span className={`text-[10.5px] px-2.5 py-0.5 rounded-full ml-auto font-bold ${isWsConnected ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30' : 'bg-amber-500/10 text-amber-300 border border-amber-500/25'}`}>{isWsConnected ? 'Gateway connected' : 'Gateway offline'}</span>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-[#8E8AA5] block mb-1 font-medium">Speech Recognition (STT Language)</label>
              <select
                value={languageMode === 'hi' || languageMode === 'hinglish' ? 'hi-IN' : languageMode === 'en' ? 'en-IN' : 'auto'}
                onChange={(e) => setLanguageMode(e.target.value === 'hi-IN' ? 'hi' : e.target.value === 'en-IN' ? 'en' : 'auto')}
                className="w-full glass-inset-tray border border-white/[0.08] focus:border-violet-500/50 rounded-xl px-3 py-2 text-white font-medium focus:outline-none shadow-inner cursor-pointer"
              >
                <option value="auto" className="bg-[#121020] text-white">Auto detect</option>
                <option value="en" className="bg-[#121020] text-white">English (India)</option>
                <option value="hi" className="bg-[#121020] text-white">Hindi</option>
                <option value="hinglish" className="bg-[#121020] text-white">Hinglish</option>
              </select>
            </div>

            <div>
              <label className="text-[#8E8AA5] block mb-1 font-medium">Timbre TTS Voice</label>
              <select
                value={voicePersona}
                onChange={(e) => setVoicePersona(e.target.value as 'Nalini' | 'Deepak')}
                className="w-full glass-inset-tray border border-white/[0.08] focus:border-violet-500/50 rounded-xl px-3 py-2 text-white font-medium focus:outline-none shadow-inner cursor-pointer"
              >
                <option value="Nalini" className="bg-[#121020] text-white">Female voice · matched to language</option>
                <option value="Deepak" className="bg-[#121020] text-white">Male voice · matched to language</option>
              </select>
            </div>

            <div>
              <label className="text-[#8E8AA5] block mb-1 font-medium">Last measured voice provider results</label>
              <div className="p-2.5 rounded-xl glass-card-3d border border-violet-500/30 text-violet-300 tabular-nums text-[11.5px] flex items-center justify-between font-semibold">
                <span>Prisma v3 · Timbre v2.5</span>
                <span className={providerStatus.tts_status === 'connected' ? 'text-emerald-300 font-bold' : 'text-amber-300 font-bold'}>● {providerStatus.tts_status || 'Not measured'}</span>
              </div>
              <p className="text-[11px] text-[#8E8AA5]">Live microphone audio is sent to Gnani Prisma through the backend proxy. The API key stays on the server.</p>
              <p className="text-[11px] text-[#8E8AA5]">Reasoning service on last turn: {providerStatus.reasoning || 'Not measured'}</p>
            </div>
          </div>
        </PremiumCard>
      </div>

      {/* Real prompt examples */}
      <PremiumCard className="p-5">
        <div className="flex items-center pb-3 border-b border-white/[0.06] mb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-violet-400" />
            <h3 className="text-[15px] font-bold text-white">Prompt examples</h3>
          </div>
        </div>

        <p className="text-[12.5px] text-[#8E8AA5] leading-relaxed mb-3">
          Each example is sent to the configured backend and uses its current financial data. No scripted transcript or latency is shown.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
          {sampleVoicePrompts.map((query, idx) => (
            <button
              key={idx}
              onClick={() => processQuery(query)}
              className="flex items-center justify-between p-3 rounded-xl glass-card-3d border border-white/[0.06] hover:border-violet-500/40 text-left transition-all group"
            >
              <span className="text-[12px] text-[#C8C5DC] group-hover:text-white truncate pr-2 font-medium">
                "{query}"
              </span>
              <Play className="w-3 h-3 text-violet-400 group-hover:text-violet-300 flex-shrink-0" />
            </button>
          ))}
        </div>
      </PremiumCard>

      <div className="flex justify-end pt-2">
        <button
          onClick={handleSave}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-b from-violet-600/40 via-violet-700/50 to-indigo-900/60 border-t border-white/[0.25] border-b border-black/50 text-white text-[12.5px] font-bold shadow-[0_2px_10px_rgba(0,0,0,0.5),0_0_12px_rgba(139,92,246,0.3)] hover:brightness-110 active:scale-95 transition-all"
        >
          {saved ? <CheckCircle2 className="w-4 h-4 text-emerald-300" /> : <Save className="w-4 h-4 text-violet-300" />}
          <span>{saved ? 'Preferences Saved!' : 'Save System Settings'}</span>
        </button>
      </div>
    </div>
  );
};
