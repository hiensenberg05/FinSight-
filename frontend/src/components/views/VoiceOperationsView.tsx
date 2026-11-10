import React, { useEffect } from 'react';
import { Activity, AudioLines, Clock3, RefreshCw, ShieldAlert } from 'lucide-react';
import { useVoice } from '../../voice/VoiceContext';
import { VoiceOperationsTrace } from '../../types';

const percentile = (traces: VoiceOperationsTrace[], pick: (trace: VoiceOperationsTrace) => number | null | undefined, p: number) => {
  const values = traces.map(pick).filter((value): value is number => typeof value === 'number' && Number.isFinite(value)).sort((a, b) => a - b);
  if (!values.length) return null;
  return values[Math.max(0, Math.ceil(p * values.length) - 1)];
};

const Metric: React.FC<{ label: string; value: number | null; unit?: string; count: number }> = ({ label, value, unit = 'ms', count }) => (
  <div className="rounded-xl border border-white/[0.08] bg-white/[0.025] p-4">
    <p className="text-xs text-[#A29DBE]">{label}</p>
    <p className="mt-2 text-2xl font-semibold tabular-nums text-white">{value === null ? '—' : `${Math.round(value)} ${unit}`}</p>
    <p className="mt-1 text-[11px] text-[#77728F]">{value === null ? 'No measurements yet' : `n = ${count} real trace${count === 1 ? '' : 's'}`}</p>
  </div>
);

export const VoiceOperationsView: React.FC = () => {
  const { voiceOperations, refreshVoiceOperations, isWsConnected } = useVoice();

  useEffect(() => {
    void refreshVoiceOperations();
    const timer = window.setInterval(() => void refreshVoiceOperations(), 8000);
    return () => window.clearInterval(timer);
  }, [refreshVoiceOperations]);

  const ttft = (trace: VoiceOperationsTrace) => trace.latencies.generation_ttft_ms;
  const tool = (trace: VoiceOperationsTrace) => trace.latencies.tool_ms;
  const tts = (trace: VoiceOperationsTrace) => trace.latencies.tts_first_audio_ms;
  const audible = (trace: VoiceOperationsTrace) => trace.end_to_first_audible_ms;
  const bargeIn = (trace: VoiceOperationsTrace) => trace.barge_in_latency_ms;
  const traceCount = (picker: (trace: VoiceOperationsTrace) => number | null | undefined) => voiceOperations.filter((trace) => typeof picker(trace) === 'number').length;
  const interrupted = voiceOperations.filter((trace) => typeof trace.interruption_success === 'boolean');
  const interruptionRate = interrupted.length ? Math.round(interrupted.filter((trace) => trace.interruption_success).length / interrupted.length * 100) : null;
  const latest = voiceOperations[0];
  const lastProvider = (key: string) => latest?.provider_status?.[key] || 'Not measured';

  return (
    <main className="mx-auto w-full max-w-[1380px] space-y-5 p-4 pb-10 sm:p-6" aria-labelledby="voice-ops-title">
      <header className="flex flex-wrap items-start justify-between gap-3 border-b border-white/[0.08] pb-4">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-violet-300">Developer diagnostics</p>
          <h1 id="voice-ops-title" className="mt-1 text-2xl font-semibold text-white">Voice Operations</h1>
          <p className="mt-1 max-w-2xl text-sm text-[#A29DBE]">Measurements are collected from completed voice turns. Missing values stay blank until a real trace reports them.</p>
        </div>
        <button onClick={() => void refreshVoiceOperations()} className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-white/10 px-3 text-sm text-slate-200 hover:bg-white/5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-violet-400">
          <RefreshCw className="h-4 w-4" /> Refresh traces
        </button>
      </header>

      <section aria-labelledby="provider-health-title">
        <div className="mb-3 flex items-center gap-2"><Activity className="h-4 w-4 text-cyan-300" /><h2 id="provider-health-title" className="text-sm font-semibold text-white">Provider and transport status</h2></div>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-xl border border-white/[0.08] p-4"><p className="text-xs text-[#A29DBE]">Voice gateway</p><p className="mt-2 text-sm font-semibold text-white">{isWsConnected ? 'WebSocket connected' : 'WebSocket disconnected'}</p></div>
          <div className="rounded-xl border border-white/[0.08] p-4"><p className="text-xs text-[#A29DBE]">Gnani STT</p><p className="mt-2 text-sm font-semibold text-white">{['gnani_stt', 'gnani_prisma_v3'].includes(String(lastProvider('stt'))) ? 'Prisma used on latest turn' : lastProvider('stt')}</p></div>
          <div className="rounded-xl border border-white/[0.08] p-4"><p className="text-xs text-[#A29DBE]">Gnani TTS</p><p className="mt-2 text-sm font-semibold text-white">{lastProvider('tts_status')}{lastProvider('tts_status') === 'connected' ? ' · audio returned' : ''}</p></div>
          <div className="rounded-xl border border-white/[0.08] p-4"><p className="text-xs text-[#A29DBE]">Reasoning</p><p className="mt-2 text-sm font-semibold text-white">{lastProvider('reasoning_status')}{latest?.provider_status?.reasoning_provider ? ` · ${latest.provider_status.reasoning_provider}` : ''}</p></div>
        </div>
        <p className="mt-2 text-xs text-[#77728F]">Audio transport: Sentence-boundary pipelined streaming via Gnani Timbre WebSocket with client-side acoustic VAD barge-in.</p>
      </section>

      <section aria-labelledby="latency-title">
        <div className="mb-3 flex items-center gap-2"><Clock3 className="h-4 w-4 text-violet-300" /><h2 id="latency-title" className="text-sm font-semibold text-white">Latency distribution</h2></div>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {[
            ['LLM first text', ttft], ['Tool execution', tool], ['TTS audio ready', tts], ['First audible response', audible], ['Barge-in cutoff', bargeIn],
          ].map(([label, picker]) => {
            const select = picker as (trace: VoiceOperationsTrace) => number | null | undefined;
            const count = traceCount(select);
            return <React.Fragment key={label as string}><Metric label={`${label as string} · P50`} value={percentile(voiceOperations, select, 0.5)} count={count} /><Metric label={`${label as string} · P95`} value={percentile(voiceOperations, select, 0.95)} count={count} /></React.Fragment>;
          })}
        </div>
      </section>

      <section className="grid gap-3 lg:grid-cols-[0.8fr_1.2fr]">
        <div className="rounded-xl border border-white/[0.08] p-4">
          <div className="flex items-center gap-2"><ShieldAlert className="h-4 w-4 text-amber-300" /><h2 className="text-sm font-semibold text-white">Interruption success</h2></div>
          <p className="mt-3 text-2xl font-semibold tabular-nums text-white">{interruptionRate === null ? '—' : `${interruptionRate}%`}</p>
          <p className="mt-1 text-xs text-[#77728F]">{interrupted.length ? `${interrupted.filter((trace) => trace.interruption_success).length} of ${interrupted.length} measured interruptions` : 'No interruption outcomes have been measured.'}</p>
        </div>
        <div className="rounded-xl border border-white/[0.08] p-4">
          <div className="mb-3 flex items-center gap-2"><AudioLines className="h-4 w-4 text-cyan-300" /><h2 className="text-sm font-semibold text-white">Recent voice-session traces</h2></div>
          {voiceOperations.length === 0 ? <p className="text-sm text-[#8E8AA5]">No completed turns recorded in this backend process yet.</p> : (
            <div className="max-h-96 space-y-2 overflow-y-auto">
              {voiceOperations.map((trace) => (
                <article key={trace.trace_id} className="rounded-lg bg-white/[0.025] p-3 text-xs">
                  <div className="flex flex-wrap items-center justify-between gap-2"><span className="font-mono text-violet-200">{trace.trace_id.slice(0, 12)}</span><time className="text-[#77728F]">{new Date(trace.recorded_at).toLocaleString()}</time></div>
                  <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[#A29DBE]">
                    <span>LLM first text: {trace.latencies.generation_ttft_ms == null ? '—' : `${trace.latencies.generation_ttft_ms} ms`}</span>
                    <span>Tool: {trace.latencies.tool_ms == null ? '—' : `${trace.latencies.tool_ms} ms`}</span>
                    <span>TTS ready: {trace.latencies.tts_first_audio_ms == null ? '—' : `${trace.latencies.tts_first_audio_ms} ms`}</span>
                    <span>Audible: {trace.end_to_first_audible_ms == null ? 'pending' : `${trace.end_to_first_audible_ms} ms`}</span>
                    <span>Barge-in: {trace.barge_in_latency_ms == null ? '—' : `${trace.barge_in_latency_ms} ms`}</span>
                    <span>Interrupted: {trace.interruption_success == null ? 'not measured' : trace.interruption_success ? 'yes' : 'no'}</span>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      </section>
    </main>
  );
};
