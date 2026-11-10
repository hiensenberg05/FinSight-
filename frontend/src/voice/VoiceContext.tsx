import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import { SpeechIOManager } from './speechIO';
import { PcmAudioPlayer } from './pcmAudioPlayer';
import { parseIntent, IntentResult } from './intents';
import { formatINR } from '../utils/formatters';
import { ExecutionStage, EvidenceItem, ActionProposal, SimulationData, ProactiveAlert, VoiceOperationsTrace, PortalEvidenceData } from '../types';

export type VoiceState = 'idle' | 'listening' | 'thinking' | 'tool_execution' | 'speaking' | 'interrupted' | 'error';

export interface HistoryItem {
  id: string;
  userQuery: string;
  assistantResponse: string;
  timestamp: string;
  intent: string;
  toolUsed?: string;
  latencies?: LatencyBreakdown;
  evidence?: EvidenceItem[];
  metadata?: any;
  actionProposal?: ActionProposal;
  simulationData?: SimulationData;
  portalEvidence?: PortalEvidenceData;
  slackAlert?: {
    channel: string;
    channel_id?: string;
    workspace?: string;
    alert_type: string;
    slack_url: string;
    dm_url?: string;
    status: string;
    results?: any;
  };
  executionStages?: ExecutionStage[];
  chartData?: any[];
  chartTitle?: string;
  followUpQuestions?: string[];
}

export interface LatencyBreakdown {
  stt_ms?: number | null;
  intent_ms?: number;
  tool_ms?: number;
  generation_ttft_ms?: number;
  tts_first_audio_ms?: number;
  tts_ms?: number;
  total_turn_ms?: number;
}

export interface ActiveToolCall {
  tool: string;
  args: any;
  description?: string;
  status: 'calling' | 'computed';
  duration_ms?: number;
}

interface VoiceContextType {
  voiceState: VoiceState;
  interimTranscript: string;
  finalTranscript: string;
  audioLevel: number;
  audioLevelSource: 'microphone' | 'playback' | 'unavailable' | null;
  currentResponse: IntentResult | null;
  transcriptHistory: HistoryItem[];
  isMicOn: boolean;
  micPermissionDenied: boolean;
  textInputOpen: boolean;
  pendingTransfer: { payee: string; amount: number } | null;
  activeVoiceFilter: { category?: string; merchant?: string } | null;
  activePage: string;
  activeToolCall: ActiveToolCall | null;
  streamingText: string;
  latencies: LatencyBreakdown | null;
  latencyHistory: LatencyBreakdown[];
  voiceOperations: VoiceOperationsTrace[];
  refreshVoiceOperations: () => Promise<void>;
  activeTraceId: string | null;
  providerStatus: Record<string, string>;
  voiceError: string | null;
  isWsConnected: boolean;
  isContinuousMode: boolean;
  isMuted: boolean;
  isMicMuted: boolean;
  executionStages: ExecutionStage[];
  currentEvidence: EvidenceItem[];
  pendingAction: ActionProposal | null;
  activeSimulation: SimulationData | null;
  activePortalEvidence: PortalEvidenceData | null;
  dismissPortalEvidence: () => void;
  proactiveAlerts: ProactiveAlert[];
  isEvidenceDrawerOpen: boolean;
  activeEvidenceItems: EvidenceItem[];
  openEvidenceDrawer: (items?: EvidenceItem[]) => void;
  closeEvidenceDrawer: () => void;
  confirmActionProposal: (actionId: string) => Promise<boolean>;
  cancelActionProposal: (actionId: string) => Promise<boolean>;
  adjustSimulationSlider: (category: string, pct: number) => void;
  dismissProactiveAlert: (alertId: string) => void;
  toggleContinuousMode: () => void;
  toggleMute: () => void;
  toggleMicMute: () => void;
  setActivePage: (page: string) => void;
  clearVoiceFilter: () => void;
  isPlaybackPaused: boolean;
  togglePauseVoice: () => void;
  languageMode: 'auto' | 'en' | 'hi' | 'hinglish';
  setLanguageMode: (mode: 'auto' | 'en' | 'hi' | 'hinglish') => void;
  voicePersona: 'Nalini' | 'Deepak';
  setVoicePersona: (persona: 'Nalini' | 'Deepak') => void;
  detectedLanguage: string | null;
  startListening: () => void;
  stopListening: () => void;
  toggleListening: () => void;
  processQuery: (text: string) => void;
  interruptSpeaking: () => void;
  setTextInputOpen: (open: boolean) => void;
  confirmTransfer: () => void;
  cancelTransfer: () => void;
  dismissCard: () => void;
}

const VoiceContext = createContext<VoiceContextType | undefined>(undefined);

export const sampleVoicePrompts = [
  'Show my spending breakdown for this month',
  'How much did I spend on Food & Dining?',
  'Are there any anomalies in my spending?',
  'Compare my spending with last month',
  'What bills are due soon?',
];

const getEffectiveWsUrl = (): string => {
  if (import.meta.env.VITE_WS_URL) return import.meta.env.VITE_WS_URL;
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    if (window.location.port === '5173') {
      return `${protocol}//${window.location.hostname}:8000/ws/voice`;
    }
    return `${protocol}//${window.location.host}/ws/voice`;
  }
  return 'ws://localhost:8000/ws/voice';
};

const getEffectiveApiBase = (): string => {
  if (import.meta.env.VITE_API_BASE_URL) return import.meta.env.VITE_API_BASE_URL;
  if (typeof window !== 'undefined') {
    if (window.location.port === '5173') {
      return `http://${window.location.hostname}:8000/api/v1`;
    }
    return `${window.location.origin}/api/v1`;
  }
  return 'http://localhost:8000/api/v1';
};

const WS_URL = getEffectiveWsUrl();
const API_BASE = getEffectiveApiBase();

export const getOrCreateClientId = (): string => {
  try {
    let cid = localStorage.getItem('finsight_client_id');
    if (!cid) {
      cid = 'client_' + (typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(2, 12));
      localStorage.setItem('finsight_client_id', cid);
    }
    return cid;
  } catch (e) {
    return 'client_persistent_fallback';
  }
};

export const VoiceProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [voiceState, setVoiceState] = useState<VoiceState>('idle');
  const [interimTranscript, setInterimTranscript] = useState<string>('');
  const [finalTranscript, setFinalTranscript] = useState<string>('');
  const [audioLevel, setAudioLevel] = useState<number>(0);
  const [audioLevelSource, setAudioLevelSource] = useState<'microphone' | 'playback' | 'unavailable' | null>(null);
  const [currentResponse, setCurrentResponse] = useState<IntentResult | null>(null);
  const [transcriptHistory, setTranscriptHistory] = useState<HistoryItem[]>([]);
  const [micPermissionDenied, setMicPermissionDenied] = useState<boolean>(false);
  const [textInputOpen, setTextInputOpen] = useState<boolean>(false);
  const [pendingTransfer, setPendingTransfer] = useState<{ payee: string; amount: number } | null>(null);
  const [activeVoiceFilter, setActiveVoiceFilter] = useState<{ category?: string; merchant?: string } | null>(null);
  const [activePage, setActivePage] = useState<string>('ai-assistant');

  // New Agentic & WebSocket States
  const [activeToolCall, setActiveToolCall] = useState<ActiveToolCall | null>(null);
  const [streamingText, setStreamingText] = useState<string>('');
  const [latencies, setLatencies] = useState<LatencyBreakdown | null>(null);
  const [latencyHistory, setLatencyHistory] = useState<LatencyBreakdown[]>([]);
  const [voiceOperations, setVoiceOperations] = useState<VoiceOperationsTrace[]>([]);
  const [activeTraceId, setActiveTraceId] = useState<string | null>(null);
  const [providerStatus, setProviderStatus] = useState<Record<string, string>>({});
  const [isWsConnected, setIsWsConnected] = useState<boolean>(false);
  const [isContinuousMode, setIsContinuousMode] = useState<boolean>(false);
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [isMicMuted, setIsMicMuted] = useState<boolean>(false);

  // Operational System States
  const [executionStages, setExecutionStages] = useState<ExecutionStage[]>([]);
  const [currentEvidence, setCurrentEvidence] = useState<EvidenceItem[]>([]);
  const [pendingAction, setPendingAction] = useState<ActionProposal | null>(null);
  const [activeSimulation, setActiveSimulation] = useState<SimulationData | null>(null);
  const [activePortalEvidence, setActivePortalEvidence] = useState<PortalEvidenceData | null>(null);
  const [proactiveAlerts, setProactiveAlerts] = useState<ProactiveAlert[]>([]);
  const [isEvidenceDrawerOpen, setIsEvidenceDrawerOpen] = useState<boolean>(false);
  const [activeEvidenceItems, setActiveEvidenceItems] = useState<EvidenceItem[]>([]);
  const [isPlaybackPaused, setIsPlaybackPaused] = useState<boolean>(false);
  const [languageMode, setLanguageMode] = useState<'auto' | 'en' | 'hi' | 'hinglish'>('auto');
  const [voicePersona, setVoicePersona] = useState<'Nalini' | 'Deepak'>('Nalini');
  const [detectedLanguage, setDetectedLanguage] = useState<string | null>(null);
  const [voiceError, setVoiceError] = useState<string | null>(null);

  useEffect(() => {
    speechManagerRef.current?.setLanguage(languageMode);
  }, [languageMode]);

  const togglePauseVoice = () => {
    if (activeAudioElementRef.current) {
      if (activeAudioElementRef.current.paused) {
        activeAudioElementRef.current.play().catch(() => {});
        setIsPlaybackPaused(false);
        setVoiceState('speaking');
      } else {
        activeAudioElementRef.current.pause();
        setIsPlaybackPaused(true);
        setVoiceState('idle');
      }
    } else if (voiceState === 'speaking') {
      interruptSpeaking();
    }
  };

  const isContinuousModeRef = useRef<boolean>(false);
  const isMutedRef = useRef<boolean>(false);
  const isMicMutedRef = useRef<boolean>(false);
  const startListeningRef = useRef<() => void>(() => {});
  const speechManagerRef = useRef<SpeechIOManager | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const activeAudioElementRef = useRef<HTMLAudioElement | null>(null);
  const pcmPlayerRef = useRef<PcmAudioPlayer | null>(null);
  const playbackContextRef = useRef<AudioContext | null>(null);
  const playbackAnalyserRef = useRef<AnalyserNode | null>(null);
  const playbackFrameRef = useRef<number | null>(null);
  const requestIdRef = useRef<string>('');
  const requestStartedAtRef = useRef<number>(0);
  const listeningStartedAtRef = useRef<number>(0);
  const activeTraceRef = useRef<string | null>(null);
  const voiceStateRef = useRef<VoiceState>(voiceState);

  const getPcmPlayer = () => {
    if (!pcmPlayerRef.current) pcmPlayerRef.current = new PcmAudioPlayer();
    return pcmPlayerRef.current;
  };

  const refreshVoiceOperations = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/voice/operations?limit=50`);
      if (!response.ok) return;
      const payload = await response.json();
      setVoiceOperations(Array.isArray(payload.traces) ? payload.traces : []);
    } catch {
      // The diagnostics view stays empty when the operations endpoint is unavailable.
    }
  }, []);

  const reportPlaybackStarted = (provider: string, traceId = activeTraceRef.current) => {
    if (!traceId || !requestStartedAtRef.current) return;
    const elapsedMs = Math.max(0, performance.now() - requestStartedAtRef.current);
    wsRef.current?.readyState === WebSocket.OPEN && wsRef.current.send(JSON.stringify({
      type: 'playback.started', trace_id: traceId, elapsed_ms: Math.round(elapsedMs), provider,
    }));
    refreshVoiceOperations();
  };

  const stopPlaybackMeter = () => {
    if (playbackFrameRef.current !== null) cancelAnimationFrame(playbackFrameRef.current);
    playbackFrameRef.current = null;
    playbackAnalyserRef.current = null;
    if (playbackContextRef.current) void playbackContextRef.current.close();
    playbackContextRef.current = null;
    setAudioLevel(0);
    setAudioLevelSource(null);
  };

  const monitorPlaybackAmplitude = (audio: HTMLAudioElement) => {
    try {
      const context = new AudioContext();
      const analyser = context.createAnalyser();
      analyser.fftSize = 256;
      const source = context.createMediaElementSource(audio);
      source.connect(analyser);
      analyser.connect(context.destination);
      playbackContextRef.current = context;
      playbackAnalyserRef.current = analyser;
      const samples = new Uint8Array(analyser.fftSize);
      const measure = () => {
        if (!playbackAnalyserRef.current) return;
        playbackAnalyserRef.current.getByteTimeDomainData(samples);
        let energy = 0;
        for (const sample of samples) {
          const centered = (sample - 128) / 128;
          energy += centered * centered;
        }
        setAudioLevel(Math.min(1, Math.sqrt(energy / samples.length) * 3.5));
        setAudioLevelSource('playback');
        playbackFrameRef.current = requestAnimationFrame(measure);
      };
      void context.resume().then(measure);
    } catch {
      setAudioLevel(0);
      setAudioLevelSource('unavailable');
    }
  };

  const finalTranscriptRef = useRef<string>(finalTranscript);
  const pendingTransferRef = useRef<any>(pendingTransfer);
  const transcriptHistoryRef = useRef<HistoryItem[]>(transcriptHistory);

  useEffect(() => {
    finalTranscriptRef.current = finalTranscript;
  }, [finalTranscript]);

  useEffect(() => {
    voiceStateRef.current = voiceState;
  }, [voiceState]);

  useEffect(() => {
    pendingTransferRef.current = pendingTransfer;
  }, [pendingTransfer]);

  useEffect(() => {
    transcriptHistoryRef.current = transcriptHistory;
  }, [transcriptHistory]);

  const toggleContinuousMode = () => {
    const next = !isContinuousModeRef.current;
    isContinuousModeRef.current = next;
    setIsContinuousMode(next);
    if (next) {
      getPcmPlayer().unlock();
      startListeningRef.current?.();
      return;
    }

    speechManagerRef.current?.cancelListening();
    if (voiceState === 'speaking' || voiceState === 'thinking' || voiceState === 'tool_execution') {
      interruptSpeaking();
    }
    setInterimTranscript('');
    setAudioLevel(0);
    setAudioLevelSource(null);
    setVoiceState('idle');
  };

  const toggleMute = () => {
    setIsMuted((prev) => {
      const next = !prev;
      isMutedRef.current = next;
      if (next && activeAudioElementRef.current) {
        activeAudioElementRef.current.pause();
        activeAudioElementRef.current = null;
        stopPlaybackMeter();
      }
      return next;
    });
  };

  const toggleMicMute = () => {
    const next = !isMicMutedRef.current;
    isMicMutedRef.current = next;
    setIsMicMuted(next);
    if (next) {
      speechManagerRef.current?.cancelListening();
      setAudioLevel(0);
      setAudioLevelSource(null);
      setVoiceState('idle');
      return;
    }
    if (isContinuousModeRef.current) startListeningRef.current?.();
  };

  const resumeListeningIfContinuous = () => {
    setVoiceState('idle');
    voiceStateRef.current = 'idle';
    setAudioLevel(0);
    setAudioLevelSource(null);

    if (isContinuousModeRef.current) {
      setTimeout(() => {
        if (isContinuousModeRef.current && !isMicMutedRef.current) {
          startListeningRef.current?.();
        }
      }, 250);
    }
  };

  // Initialize Bi-Directional Voice WebSocket
  useEffect(() => {
    let reconnectTimer: any;

    const connectWs = () => {
      try {
        const clientId = getOrCreateClientId();
        const wsUrl = `${WS_URL}${WS_URL.includes('?') ? '&' : '?'}client_id=${encodeURIComponent(clientId)}`;
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          setIsWsConnected(true);
          refreshVoiceOperations();
        };

        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data);
            if (msg.request_id && msg.request_id !== requestIdRef.current) return;

            if (msg.type === 'session.ready') {
              console.log('[FinSight Voice WS] Connected to session:', msg.session_id);
            } else if (msg.type === 'execution_stage') {
              if (msg.trace_id) {
                activeTraceRef.current = msg.trace_id;
                setActiveTraceId(msg.trace_id);
              }
              setExecutionStages((prev) => {
                const existingIdx = prev.findIndex((s) => s.stage === msg.stage);
                if (existingIdx >= 0) {
                  const updated = [...prev];
                  updated[existingIdx] = msg;
                  return updated;
                }
                return [...prev, msg];
              });
              if (msg.stage === 'fetching_financial_data' && msg.status === 'in_progress') setVoiceState('tool_execution');
              else if (msg.status === 'in_progress') setVoiceState('thinking');
            } else if (msg.type === 'proactive_alert') {
              setProactiveAlerts((prev) => [msg, ...prev.filter((a) => a.alert_id !== msg.alert_id)]);
            } else if (msg.type === 'action_result') {
              if (msg.status === 'executed') {
                setPendingAction((prev) => (prev && prev.action_id === msg.action_id ? { ...prev, status: 'executed' as const } : prev));
              } else if (msg.status === 'cancelled') {
                setPendingAction((prev) => (prev && prev.action_id === msg.action_id ? { ...prev, status: 'cancelled' as const } : prev));
              }
            } else if (msg.type === 'simulation_update') {
              setActiveSimulation(msg.data);
            } else if (msg.type === 'tool_calling') {
              setActiveToolCall({
                tool: msg.tool,
                args: msg.args,
                description: msg.description,
                status: 'calling',
              });
            } else if (msg.type === 'tool_result') {
              setActiveToolCall((prev) =>
                prev ? { ...prev, status: 'computed', duration_ms: msg.duration_ms } : null
              );
            } else if (msg.type === 'text_stream_start') {
              setStreamingText('');
            } else if (msg.type === 'text_token') {
              setStreamingText((prev) => prev + msg.token);
            } else if (msg.type === 'audio.stream.start') {
              getPcmPlayer().cancel();
              getPcmPlayer().begin({
                onStarted: () => {
                  speechManagerRef.current?.setSpeakingState(true);
                  setVoiceState('speaking');
                  reportPlaybackStarted('gnani_timbre_websocket');
                },
                onFinished: () => {
                  speechManagerRef.current?.setSpeakingState(false);
                  if (voiceStateRef.current !== 'interrupted') resumeListeningIfContinuous();
                },
                onLevel: (level) => {
                  setAudioLevel(level);
                  setAudioLevelSource(level > 0.005 ? 'playback' : null);
                },
              });
            } else if (msg.type === 'audio.stream.chunk') {
              getPcmPlayer().enqueue(String(msg.audio || ''), Number(msg.sample_rate) || 48000);
            } else if (msg.type === 'audio.stream.end') {
              getPcmPlayer().finish();
              if (!msg.success) {
                speechManagerRef.current?.setSpeakingState(false);
                setVoiceState('error');
                setVoiceError('Gnani Timbre streaming could not finish this reply. The written response is still available.');
              }
            } else if (msg.type === 'turn_complete') {
              const spoken = msg.text || '';
              setStreamingText(spoken);

              if (msg.language_detected) {
                setDetectedLanguage(msg.language_detected);
              }

              if (msg.latencies) {
                setLatencies(msg.latencies);
                setLatencyHistory((prev) => [...prev.slice(-9), msg.latencies]);
              }
              activeTraceRef.current = msg.trace_id || null;
              setActiveTraceId(msg.trace_id || null);
              setProviderStatus(msg.provider_status || {});

              if (msg.evidence && msg.evidence.length > 0) {
                setCurrentEvidence(msg.evidence);
                setActiveEvidenceItems(msg.evidence);
              }
              if (msg.action_proposal) {
                setPendingAction(msg.action_proposal);
              }
              if (msg.simulation_data) {
                setActiveSimulation(msg.simulation_data);
              }
              if (msg.portal_evidence) {
                setActivePortalEvidence(msg.portal_evidence);
              }
              if (msg.execution_stages) {
                setExecutionStages(msg.execution_stages);
              }

              // Build rich UI intent response
              const userQueryText = finalTranscriptRef.current || spoken;
              const parsed = parseIntent(userQueryText, pendingTransferRef.current);
              parsed.spokenText = spoken;
              if (msg.chartData && msg.chartData.length > 0) {
                parsed.chartData = msg.chartData;
                parsed.chartTitle = msg.chartTitle;
              }
              if (msg.actionChips) {
                parsed.quickActions = msg.actionChips;
              }
              if (Array.isArray(msg.follow_up_questions)) {
                parsed.followUpChips = msg.follow_up_questions;
              }
              setCurrentResponse(parsed);

              // Update history
              const timeStr = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
              setTranscriptHistory((prev) => [
                {
                  id: `h-${Date.now()}`,
                  userQuery: userQueryText,
                  assistantResponse: spoken,
                  timestamp: timeStr,
                  intent: parsed.type,
                  toolUsed: msg.tool_metadata?.name,
                  latencies: msg.latencies,
                  evidence: msg.evidence,
                  metadata: msg.metadata,
                  actionProposal: msg.action_proposal,
                  simulationData: msg.simulation_data,
                  portalEvidence: msg.portal_evidence,
                  slackAlert: msg.slack_alert,
                  executionStages: msg.execution_stages,
                  chartData: msg.chartData,
                  chartTitle: msg.chartTitle,
                  followUpQuestions: msg.follow_up_questions,
                },
                ...prev.slice(0, 9),
              ]);

              // Play Gnani Timbre audio; do not silently substitute a different browser voice.
              if (isMutedRef.current) {
                // If muted, do not play audio aloud; immediately complete speaking turn
                resumeListeningIfContinuous();
              } else if (msg.audio_streamed) {
                // The reply has already reached the browser as scheduled PCM chunks.
              } else if (msg.audioBase64) {
                setVoiceState('speaking');
                voiceStateRef.current = 'speaking';
                speechManagerRef.current?.setSpeakingState(true);
                const audio = new Audio(`data:audio/wav;base64,${msg.audioBase64}`);
                activeAudioElementRef.current = audio;
                audio.onplay = () => {
                  if (requestIdRef.current === msg.request_id || !msg.request_id) {
                    reportPlaybackStarted('gnani_tts', msg.trace_id);
                    monitorPlaybackAmplitude(audio);
                  }
                };
                audio.onended = () => {
                  speechManagerRef.current?.setSpeakingState(false);
                  activeAudioElementRef.current = null;
                  stopPlaybackMeter();
                  if (requestIdRef.current === msg.request_id || !msg.request_id) resumeListeningIfContinuous();
                };
                audio.play().catch(() => {
                  stopPlaybackMeter();
                  resumeListeningIfContinuous();
                });
              } else {
                resumeListeningIfContinuous();
              }
              refreshVoiceOperations();
            } else if (msg.type === 'interrupted') {
              if (msg.request_id && msg.request_id === requestIdRef.current) setVoiceState('interrupted');
              setStreamingText('');
              setActiveToolCall(null);
            } else if (msg.type === 'assistant.error') {
              setVoiceState('error');
              setVoiceError('The backend could not complete this request. Try again or switch to text input.');
              setProviderStatus((prev) => ({ ...prev, gateway: 'error' }));
            }
          } catch (e) {
            console.error('[FinSight Voice WS] Message error:', e);
          }
        };

        ws.onclose = () => {
          setIsWsConnected(false);
          reconnectTimer = setTimeout(connectWs, 3000);
        };

        ws.onerror = () => {
          setIsWsConnected(false);
        };
      } catch (err) {
        console.warn('[FinSight Voice WS] Connection error:', err);
        reconnectTimer = setTimeout(connectWs, 3000);
      }
    };

    connectWs();

    return () => {
      clearTimeout(reconnectTimer);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Initialize SpeechIO manager for microphone capture
  useEffect(() => {
    speechManagerRef.current = new SpeechIOManager({
      language: languageMode === 'hi' ? 'hi-IN' : languageMode === 'hinglish' ? 'hi-IN,en-IN' : languageMode === 'auto' ? 'auto' : 'en-IN',
      onInterimTranscript: (text) => {
        setInterimTranscript(text);
      },
      onFinalTranscript: (text, providerLatencyMs) => {
        const clean = text.trim();
        if (!clean) return;

        // Live Voice-to-Voice: If assistant was speaking, execute real-time barge-in interruption!
        const isAudioActive = activeAudioElementRef.current !== null;
        const isSpeakingState = speechManagerRef.current?.getSpeakingState() === true;
        if (isAudioActive || isSpeakingState) {
          console.log('[FinSight Voice] Barge-in activated. Halting assistant speech for user query:', clean);
          getPcmPlayer().cancel();
          if (activeAudioElementRef.current) {
            activeAudioElementRef.current.pause();
            activeAudioElementRef.current = null;
          }
          speechManagerRef.current?.setSpeakingState(false);
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'turn.cancel' }));
          }
        }

        setInterimTranscript('');
        setFinalTranscript(clean);
        setVoiceState('thinking');
        handleExecuteQuery(clean, providerLatencyMs ?? null, 'gnani_prisma_v3');
      },
      onBargeIn: (triggerReason: string) => {
        console.log('[FinSight Voice] Instant acoustic barge-in detected:', triggerReason);
        interruptSpeaking();
        // Seamlessly begin listening for the user's ongoing speech
        setTimeout(() => {
          if (voiceStateRef.current !== 'listening') {
            startListening();
          }
        }, 30);
      },
      onAudioLevel: (level) => {
        if (voiceStateRef.current === 'listening') {
          setAudioLevel(level);
          setAudioLevelSource('microphone');
        }
      },
      onError: (err) => {
        console.warn('Speech manager notice:', err.message);
        if (err.message.includes('PermissionDenied')) {
          setMicPermissionDenied(true);
          setTextInputOpen(true);
        }
        setVoiceError(err.message.replace(/^PermissionDenied:\s*/, ''));
        setAudioLevel(0);
        setAudioLevelSource(null);
        setVoiceState('error');
      },
      onSpeechEnd: () => {
        setVoiceState((prev) => (prev === 'listening' ? 'thinking' : prev));
      },
    });

    return () => {
      speechManagerRef.current?.stopListening();
      speechManagerRef.current?.cancelSpeech();
    };
  }, [pendingTransfer]);

  // Keep SpeechIO language synced with active user preference
  useEffect(() => {
    const lang = languageMode === 'hi' ? 'hi-IN' : languageMode === 'hinglish' ? 'hi-IN,en-IN' : languageMode === 'auto' ? 'auto' : 'en-IN';
    speechManagerRef.current?.setLanguage(lang);
  }, [languageMode]);

  // Global Spacebar listener: Toggles listening when no input/textarea is focused
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === 'Space') {
        const activeTag = document.activeElement?.tagName.toLowerCase();
        const isEditable = (document.activeElement as HTMLElement)?.isContentEditable;
        if (activeTag === 'input' || activeTag === 'textarea' || isEditable) {
          return;
        }
        e.preventDefault();
        toggleListening();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [voiceState]);

  const startListening = async () => {
    startListeningRef.current = startListening;
    if (isMicMutedRef.current) {
      setVoiceError('Microphone is muted. Unmute it before speaking.');
      return;
    }
    if (voiceStateRef.current === 'speaking' || activeAudioElementRef.current !== null || getPcmPlayer().isPlaying()) {
      interruptSpeaking();
    }
    getPcmPlayer().unlock();

    setInterimTranscript('');
    setVoiceError(null);
    listeningStartedAtRef.current = performance.now();
    setAudioLevelSource('microphone');
    setVoiceState('listening');
    voiceStateRef.current = 'listening';

    await speechManagerRef.current?.startListening();
  };
  startListeningRef.current = startListening;

  const stopListening = () => {
    speechManagerRef.current?.stopListening();
    setAudioLevel(0);
    setAudioLevelSource(null);
    setVoiceState('idle');
    voiceStateRef.current = 'idle';
  };

  const toggleListening = () => {
    if (voiceState === 'listening') {
      stopListening();
    } else if (voiceState === 'speaking') {
      interruptSpeaking();
    } else {
      startListening();
    }
  };

  // Interruption Handling (Barge-In)
  const interruptSpeaking = (acousticLatencyMs = 40) => {
    // 1. Stop Gnani playback immediately.
    speechManagerRef.current?.setSpeakingState(false);
    let interruptedPlayback = getPcmPlayer().isPlaying();
    getPcmPlayer().cancel();
    if (activeAudioElementRef.current) {
      activeAudioElementRef.current.pause();
      activeAudioElementRef.current.currentTime = 0;
      activeAudioElementRef.current = null;
      interruptedPlayback = true;
    }
    stopPlaybackMeter();
    speechManagerRef.current?.cancelSpeech();

    // 2. Transmit cancel signal to backend WebSocket
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'turn.cancel', request_id: requestIdRef.current, trace_id: activeTraceRef.current }));
    }

    if (activeTraceRef.current && wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'interruption.result',
        trace_id: activeTraceRef.current,
        succeeded: interruptedPlayback,
        latency_ms: acousticLatencyMs,
      }));
    }
    setVoiceState('interrupted');
    setActiveToolCall(null);
  };

  const handleExecuteQuery = (text: string, sttLatencyMs: number | null = null, sttProvider = 'not_used') => {
    finalTranscriptRef.current = text;
    getPcmPlayer().unlock();
    setVoiceState('thinking');
    setAudioLevel(0);
    setAudioLevelSource(null);
    setVoiceError(null);
    setActiveToolCall(null);
    setStreamingText('');
    setExecutionStages([]);
    setPendingAction(null);
    getPcmPlayer().cancel();
    setCurrentEvidence([]);
    const requestId = crypto.randomUUID();
    requestIdRef.current = requestId;
    requestStartedAtRef.current = performance.now();
    activeTraceRef.current = null;
    setActiveTraceId(null);

    // If WebSocket is open, send to backend Voice Gateway
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const clientId = getOrCreateClientId();
      wsRef.current.send(JSON.stringify({
        type: 'query',
        request_id: requestId,
        client_id: clientId,
        session_id: clientId,
        query: text,
        language: languageMode,
        voice: voicePersona,
        history: transcriptHistoryRef.current.slice(0, 5),
        stt_ms: sttLatencyMs,
        stt_provider: sttProvider,
      }));
    } else if (wsRef.current && wsRef.current.readyState === WebSocket.CONNECTING) {
      setTimeout(() => handleExecuteQuery(text), 200);
      return;
    } else {
      setVoiceState('error');
      setVoiceError('Voice gateway is offline. Reconnect or switch to text mode and try again.');
    }
  };

  const openEvidenceDrawer = (items?: EvidenceItem[]) => {
    if (items && items.length > 0) {
      setActiveEvidenceItems(items);
    } else if (currentEvidence.length > 0) {
      setActiveEvidenceItems(currentEvidence);
    }
    setIsEvidenceDrawerOpen(true);
  };

  const closeEvidenceDrawer = () => {
    setIsEvidenceDrawerOpen(false);
  };

  const confirmActionProposal = async (actionId: string): Promise<boolean> => {
    try {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'action_confirm', action_id: actionId }));
      }
      const res = await fetch(`${API_BASE}/actions/${actionId}/confirm`, {
        method: 'POST',
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok && (data.success || data.status === 'executed')) {
        setPendingAction((prev) => (prev && prev.action_id === actionId ? { ...prev, status: 'executed' as const } : prev));
        return true;
      }
      return false;
    } catch {
      return false;
    }
  };

  const cancelActionProposal = async (actionId: string): Promise<boolean> => {
    try {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'action_cancel', action_id: actionId }));
      }
      const res = await fetch(`${API_BASE}/actions/${actionId}/cancel`, {
        method: 'POST',
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok && (data.success || data.status === 'cancelled')) {
        setPendingAction((prev) => (prev && prev.action_id === actionId ? { ...prev, status: 'cancelled' as const } : prev));
        return true;
      }
      return false;
    } catch {
      return false;
    }
  };

  const adjustSimulationSlider = (category: string, pct: number) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'simulate_slider',
        category,
        reduction_pct: pct,
        goal_name: 'Vacation Fund',
      }));
    }
  };

  const dismissProactiveAlert = (alertId: string) => {
    setProactiveAlerts((prev) => prev.filter((a) => a.alert_id !== alertId));
  };

  const processQuery = (text: string) => {
    if (!text.trim()) return;
    if (activeAudioElementRef.current) {
      interruptSpeaking();
    }
    setFinalTranscript(text);
    handleExecuteQuery(text);
  };

  const confirmTransfer = () => {
    if (pendingTransfer) {
      handleExecuteQuery('confirm');
    }
  };

  const cancelTransfer = () => {
    if (pendingTransfer) {
      handleExecuteQuery('cancel');
    }
  };

  const clearVoiceFilter = () => {
    setActiveVoiceFilter(null);
  };

  const dismissCard = () => {
    setCurrentResponse(null);
  };

  return (
    <VoiceContext.Provider
      value={{
        voiceState,
        interimTranscript,
        finalTranscript,
        audioLevel,
        audioLevelSource,
        currentResponse,
        transcriptHistory,
        isMicOn: voiceState === 'listening',
        micPermissionDenied,
        textInputOpen,
        pendingTransfer,
        activeVoiceFilter,
        activePage,
        activeToolCall,
        streamingText,
        latencies,
        latencyHistory,
        voiceOperations,
        refreshVoiceOperations,
        activeTraceId,
        providerStatus,
        voiceError,
        isWsConnected,
        isContinuousMode,
        isMuted,
        isMicMuted,
        toggleMute,
        toggleMicMute,
        isPlaybackPaused,
        togglePauseVoice,
        languageMode,
        setLanguageMode,
        voicePersona,
        setVoicePersona,
        detectedLanguage,
        executionStages,
        currentEvidence,
        pendingAction,
        activeSimulation,
        activePortalEvidence,
        dismissPortalEvidence: () => setActivePortalEvidence(null),
        proactiveAlerts,
        isEvidenceDrawerOpen,
        activeEvidenceItems,
        openEvidenceDrawer,
        closeEvidenceDrawer,
        confirmActionProposal,
        cancelActionProposal,
        adjustSimulationSlider,
        dismissProactiveAlert,
        toggleContinuousMode,
        setActivePage,
        clearVoiceFilter,
        startListening,
        stopListening,
        toggleListening,
        processQuery,
        interruptSpeaking,
        setTextInputOpen,
        confirmTransfer,
        cancelTransfer,
        dismissCard,
      }}
    >
      {children}
    </VoiceContext.Provider>
  );
};

export const useVoice = (): VoiceContextType => {
  const context = useContext(VoiceContext);
  if (!context) {
    throw new Error('useVoice must be used within a VoiceProvider');
  }
  return context;
};
