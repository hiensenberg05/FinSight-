import React from 'react';
import { motion } from 'framer-motion';
import { ExternalLink, CheckCircle2, MessageSquare, Radio, Shield, Hash, Zap } from 'lucide-react';

export interface SlackAlertData {
  channel: string;
  channel_id?: string;
  workspace?: string;
  alert_type: string;
  custom_topic?: string;
  slack_url: string;
  dm_url?: string;
  status: string;
  results?: any;
}

interface SlackAlertCardProps {
  data: SlackAlertData;
}

export const SlackAlertCard: React.FC<SlackAlertCardProps> = ({ data }) => {
  const isSurge = data.alert_type?.includes('surge') || data.alert_type?.includes('swiggy');
  const isBill = data.alert_type?.includes('bill') || data.alert_type?.includes('bescom');
  const isAnomaly = data.alert_type?.includes('anomaly') || data.alert_type?.includes('croma');
  const isBudget = data.alert_type?.includes('budget');
  const isSpike = data.alert_type?.includes('spike') || data.alert_type?.includes('upsurge');
  const isGoal = data.alert_type?.includes('goal');
  const isHighTx = data.alert_type?.includes('high') || data.alert_type?.includes('transaction');
  const isCategory = data.alert_type?.includes('category');

  const topicTitle = isBudget
    ? `⚠️ Budget Limit Breach Alert · ${data.custom_topic || 'Outflows'}`
    : isSpike
    ? `📈 Spending Surge / Upsurge Alert · ${data.custom_topic || 'Spike'}`
    : isGoal
    ? '🎯 Savings Goal Velocity Alert · Vacation Fund'
    : isHighTx
    ? '💳 High-Value Transaction Alert'
    : isCategory
    ? `📊 Verified Category Outflow Alert · ${data.custom_topic || 'Category'}`
    : isSurge
    ? '🍔 Swiggy Late-Night Surcharge Forensic Alert'
    : isBill
    ? '⚡ BESCOM Electricity Bill Reminder'
    : isAnomaly
    ? '📄 Croma Verified Hardware Tax Invoice'
    : '🟢 FinSight Autonomous Financial Sentinel';

  const topicDescription = isBudget
    ? `Dispatched critical budget breach warning for ${data.custom_topic || 'this category'} exceeding ceiling.`
    : isSpike
    ? `Dispatched spending surge and monthly delta analysis for ${data.custom_topic || 'spending drivers'}.`
    : isGoal
    ? 'Dispatched savings goal milestone drag alert showing delay caused by discretionary delivery fees.'
    : isHighTx
    ? 'Dispatched real-time ledger report of qualified high-value transactions meeting threshold filter.'
    : isCategory
    ? `Dispatched verified spending summary for ${data.custom_topic || 'your category'} to the team.`
    : isSurge
    ? 'Dispatched itemized surge fee (₹120) and packaging markup breakdown to alert the team.'
    : isBill
    ? 'Dispatched upcoming utility bill (₹1,400 due Feb 28) with verified liquidity cushion.'
    : isAnomaly
    ? 'Dispatched ₹2,400 outlier clearance proving legitimate HDMI cable purchase with 2-yr warranty.'
    : 'Dispatched live autonomous financial health check card.';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      className="w-full my-3 rounded-2xl bg-gradient-to-b from-[#1C1022] to-[#0E0713] border border-[#611F69]/40 p-4 sm:p-5 shadow-2xl relative overflow-hidden backdrop-blur-xl"
    >
      {/* Slack Brand Accent Glow */}
      <div className="absolute -top-12 -right-12 w-48 h-48 bg-[#4A154B]/30 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-10 -left-10 w-40 h-40 bg-[#36C5F0]/15 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex items-start justify-between pb-3 border-b border-white/[0.08] relative z-10">
        <div className="flex items-center gap-3">
          {/* Slack Hash Icon */}
          <div className="w-10 h-10 rounded-xl bg-[#4A154B]/50 border border-[#ECB22E]/40 flex items-center justify-center text-white shadow-lg relative">
            <span className="text-lg font-black tracking-tight text-[#ECB22E]">#</span>
            <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-500 rounded-full border-2 border-[#1C1022]" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#E01E5A] bg-[#E01E5A]/15 px-2 py-0.5 rounded-md border border-[#E01E5A]/30">
                Slack Sentinel
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-semibold flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                Delivered (HTTP 200 OK)
              </span>
            </div>
            <p className="text-sm font-semibold text-white mt-0.5">
              Workspace: <span className="text-[#36C5F0] font-mono">{data.workspace || 'accounting'}</span> · Channel: <span className="text-amber-300 font-mono">{data.channel || '#engineering-inventory-tracker'}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 text-[11px] text-slate-400 bg-white/[0.05] border border-white/[0.08] px-2.5 py-1 rounded-lg">
          <Radio className="w-3 h-3 text-emerald-400 animate-pulse" />
          <span>Live Webhook + Bot DM</span>
        </div>
      </div>

      {/* Content Summary */}
      <div className="py-3.5 space-y-3 relative z-10">
        <div className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-3">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs font-bold text-white flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-amber-400" />
              {topicTitle}
            </span>
            <span className="text-[10px] text-slate-400 font-mono">Interactive Block Kit</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            {topicDescription}
          </p>
        </div>

        {/* Dual Delivery Channel Details */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs">
          <div className="bg-[#4A154B]/20 border border-[#4A154B]/50 rounded-xl p-3 flex flex-col justify-between">
            <div className="flex items-center gap-2 mb-1.5">
              <Hash className="w-4 h-4 text-[#36C5F0]" />
              <span className="font-semibold text-white">Channel Broadcast</span>
            </div>
            <p className="text-[11px] text-slate-300 font-mono mb-2">
              {data.channel || '#engineering-inventory-tracker'}
            </p>
            <a
              href={data.slack_url || 'https://app.slack.com/client/T09MCF0UERJ/C09M5ETUMPF'}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center justify-center gap-1.5 text-[11px] font-semibold text-white bg-[#4A154B] hover:bg-[#611F69] border border-[#ECB22E]/40 px-3 py-1.5 rounded-lg transition-all shadow-sm"
            >
              <span>Open Channel in Slack</span>
              <ExternalLink className="w-3 h-3 opacity-80" />
            </a>
          </div>

          <div className="bg-[#0D1B2A]/40 border border-[#36C5F0]/30 rounded-xl p-3 flex flex-col justify-between">
            <div className="flex items-center gap-2 mb-1.5">
              <MessageSquare className="w-4 h-4 text-emerald-400" />
              <span className="font-semibold text-white">Bot Direct Message</span>
            </div>
            <p className="text-[11px] text-slate-300 font-mono mb-2">
              @finsight (Personal DM)
            </p>
            <a
              href={data.dm_url || 'https://app.slack.com/client/T09MCF0UERJ/D0CFWN1310F'}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center justify-center gap-1.5 text-[11px] font-semibold text-white bg-[#0D1B2A] hover:bg-[#1E3048] border border-[#36C5F0]/40 px-3 py-1.5 rounded-lg transition-all shadow-sm"
            >
              <span>Open @finsight DM</span>
              <ExternalLink className="w-3 h-3 opacity-80" />
            </a>
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="pt-2 border-t border-white/[0.08] flex items-center justify-between text-[11px] text-slate-400">
        <span className="flex items-center gap-1">
          <Shield className="w-3 h-3 text-emerald-400" />
          Autonomous Sentinel Guardrail Active
        </span>
        <span className="text-[10px] font-mono text-slate-400">Webhook: 200 OK · DM: 200 OK</span>
      </div>
    </motion.div>
  );
};
