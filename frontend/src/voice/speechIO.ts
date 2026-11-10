/** Live microphone capture routed through the backend to Gnani Prisma v3. */

export interface SpeechIOConfig {
  language?: string;
  onInterimTranscript?: (text: string) => void;
  onFinalTranscript?: (text: string, providerLatencyMs?: number) => void;
  onAudioLevel?: (level: number) => void;
  onError?: (err: Error) => void;
  onSpeechEnd?: () => void;
  onBargeIn?: (interimText: string) => void;
}

const FRAME_SAMPLES = 512;
const FRAME_BYTES = FRAME_SAMPLES * 2;

function speechSocketUrl(language: string, sampleRate: number): string {
  const configured = import.meta.env.VITE_WS_URL as string | undefined;
  let base = configured;
  if (!base && typeof window !== 'undefined') {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    if (window.location.port === '5173') {
      base = `${protocol}://${window.location.hostname}:8000/ws/voice`;
    } else {
      base = `${protocol}://${window.location.host}/ws/voice`;
    }
  } else if (!base) {
    base = 'ws://localhost:8000/ws/voice';
  }
  const endpoint = base.replace(/\/$/, '').replace(/\/ws\/voice(?:\/stt)?$/, '/ws/voice/stt');
  const query = new URLSearchParams({ language, sample_rate: String(sampleRate) });
  return `${endpoint}?${query.toString()}`;
}

export class SpeechIOManager {
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private mediaStream: MediaStream | null = null;
  private source: MediaStreamAudioSourceNode | null = null;
  private processor: ScriptProcessorNode | null = null;
  private silentGain: GainNode | null = null;
  private socket: WebSocket | null = null;
  private frameTimer: number | null = null;
  private levelTimer: number | null = null;
  private closeTimer: number | null = null;
  private frames: ArrayBuffer[] = [];
  private frameBuffer: Uint8Array = new Uint8Array(FRAME_BYTES);
  private frameOffset = 0;
  private config: SpeechIOConfig;
  private isListening = false;
  private isSpeakingState = false;
  private bargeInThreshold = 0.040;
  private bargeInConsecutiveFrames = 0;
  private readonly requiredBargeInFrames = 2; // ~80ms sustained acoustic energy

  constructor(config: SpeechIOConfig) {
    this.config = config;
  }

  public getSpeakingState(): boolean {
    return this.isSpeakingState;
  }

  public setLanguage(language: string) {
    this.config.language = language;
  }

  public setSpeakingState(isSpeaking: boolean) {
    this.isSpeakingState = isSpeaking;
  }

  public async startListening(): Promise<boolean> {
    if (this.isListening) return true;

    // Reset frame queues & close previous turn's socket if still lingering
    this.frames = [];
    this.frameOffset = 0;
    if (this.socket) {
      try { this.socket.close(); } catch { /* ignore */ }
      this.socket = null;
    }

    try {
      // Re-use active mediaStream & audioContext if already acquired to avoid permission delays
      const hasActiveAudioTrack = this.mediaStream && this.mediaStream.getAudioTracks().some((t) => t.readyState === 'live');
      if (!hasActiveAudioTrack || !this.audioContext || this.audioContext.state === 'closed') {
        this.mediaStream = await navigator.mediaDevices.getUserMedia({
          audio: {
            channelCount: 1,
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
          },
        });
        const AudioContextClass = window.AudioContext || (window as Window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
        if (!AudioContextClass) throw new Error('This browser does not support microphone audio processing.');
        try {
          this.audioContext = new AudioContextClass({ sampleRate: 48000 });
        } catch {
          this.audioContext = new AudioContextClass();
        }
      }
      await this.audioContext.resume();

      const sampleRate = this.audioContext.sampleRate;
      if (sampleRate !== 44100 && sampleRate !== 48000) {
        throw new Error(`Gnani live speech requires a 44.1 or 48 kHz microphone stream; this browser supplied ${sampleRate} Hz.`);
      }

      const socket = new WebSocket(speechSocketUrl(this.config.language || 'auto', sampleRate));
      this.socket = socket;
      socket.binaryType = 'arraybuffer';
      const ready = await new Promise<boolean>((resolve, reject) => {
        const timeout = window.setTimeout(() => reject(new Error('Gnani Prisma did not connect in time.')), 10000);
        socket.onopen = () => undefined;
        socket.onmessage = (event) => {
          let message: any;
          try { message = JSON.parse(String(event.data)); } catch { return; }
          if (message.type === 'connected') {
            window.clearTimeout(timeout);
            resolve(true);
            return;
          }
          if (message.type === 'speech_start') {
            return;
          }
          if (message.type === 'processing') {
            this.config.onSpeechEnd?.();
            return;
          }
          if (message.type === 'transcript') {
            const text = String(message.text || '').trim();
            if (text) {
              this.finishCapture();
              this.config.onFinalTranscript?.(text, Number.isFinite(message.latency) ? Number(message.latency) : undefined);
            }
            return;
          }
          if (message.type === 'error') {
            window.clearTimeout(timeout);
            const error = new Error(String(message.message || 'Gnani Prisma could not transcribe this audio.'));
            if (!this.isListening) reject(error);
            else this.fail(error);
          }
        };
        socket.onerror = () => {
          window.clearTimeout(timeout);
          reject(new Error('Could not connect to Gnani Prisma. Check the network and try again.'));
        };
        socket.onclose = (event) => {
          window.clearTimeout(timeout);
          if (!this.isListening && event.code !== 1000 && event.code !== 1001) {
            reject(new Error('Gnani Prisma closed the live transcription connection.'));
          }
        };
      });
      if (!ready) throw new Error('Gnani Prisma is not ready.');

      this.startAudioCapture();
      this.isListening = true;
      return true;
    } catch (error) {
      this.stopCapture();
      const raw = error instanceof Error ? error.message : 'Microphone or Gnani Prisma could not be started.';
      const message = /NotAllowedError|PermissionDeniedError/i.test(raw)
        ? 'PermissionDenied: Allow microphone access, then try again.'
        : raw;
      this.config.onError?.(new Error(message));
      return false;
    }
  }

  public stopListening() {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ type: 'commit' }));
      this.stopCapture(false);
      this.closeTimer = window.setTimeout(() => this.stopCapture(), 1800);
      return;
    }
    this.stopCapture();
  }

  public cancelListening() {
    this.stopCapture();
  }

  public cancelSpeech() {
    this.isSpeakingState = false;
    this.bargeInConsecutiveFrames = 0;
  }

  private startAudioCapture() {
    if (!this.audioContext || !this.mediaStream || !this.socket) return;

    if (!this.source || !this.processor || !this.analyser) {
      this.source = this.audioContext.createMediaStreamSource(this.mediaStream);
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 256;
      this.analyser.smoothingTimeConstant = 0.35;
      this.processor = this.audioContext.createScriptProcessor(1024, 1, 1);
      this.silentGain = this.audioContext.createGain();
      this.silentGain.gain.value = 0;
      this.source.connect(this.analyser);
      this.source.connect(this.processor);
      this.processor.connect(this.silentGain);
      this.silentGain.connect(this.audioContext.destination);

      this.processor.onaudioprocess = (event) => {
        if (!this.isListening) return;
        const samples = event.inputBuffer.getChannelData(0);
        for (let i = 0; i < samples.length; i += 1) {
          const sample = Math.max(-1, Math.min(1, samples[i]));
          const value = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
          const view = new DataView(this.frameBuffer.buffer);
          view.setInt16(this.frameOffset, value, true);
          this.frameOffset += 2;
          if (this.frameOffset === FRAME_BYTES) {
            this.frames.push(this.frameBuffer.buffer as ArrayBuffer);
            this.frameBuffer = new Uint8Array(FRAME_BYTES);
            this.frameOffset = 0;
          }
        }
      };
    }

    if (this.frameTimer !== null) window.clearInterval(this.frameTimer);
    const frameIntervalMs = (FRAME_SAMPLES / this.audioContext.sampleRate) * 1000;
    this.frameTimer = window.setInterval(() => {
      if (this.socket?.readyState !== WebSocket.OPEN || this.frames.length === 0) return;
      this.socket.send(this.frames.shift() as ArrayBuffer);
    }, frameIntervalMs);

    if (this.levelTimer === null && this.analyser) {
      const timeData = new Uint8Array(this.analyser.frequencyBinCount);
      this.levelTimer = window.setInterval(() => {
        if (!this.analyser) return;
        this.analyser.getByteTimeDomainData(timeData);
        let squared = 0;
        for (const value of timeData) {
          const centered = (value - 128) / 128;
          squared += centered * centered;
        }
        const rms = Math.sqrt(squared / timeData.length);
        this.config.onAudioLevel?.(Math.min(1, rms * 4));

        // Instant Acoustic Barge-In detection during assistant speech
        if (this.isSpeakingState) {
          if (rms >= this.bargeInThreshold) {
            this.bargeInConsecutiveFrames += 1;
            if (this.bargeInConsecutiveFrames >= this.requiredBargeInFrames) {
              this.bargeInConsecutiveFrames = 0;
              this.isSpeakingState = false;
              this.config.onBargeIn?.('acoustic_energy');
            }
          } else {
            this.bargeInConsecutiveFrames = 0;
          }
        }
      }, 40);
    }
  }

  private finishCapture() {
    this.isListening = false;
    if (this.frameTimer !== null) window.clearInterval(this.frameTimer);
    if (this.closeTimer !== null) window.clearTimeout(this.closeTimer);
    this.frameTimer = null;
    this.closeTimer = null;
    this.frames = [];
    this.frameOffset = 0;
    if (this.socket) {
      if (this.socket.readyState === WebSocket.OPEN) {
        try { this.socket.send(JSON.stringify({ type: 'commit' })); } catch { /* ignore */ }
      }
      try { this.socket.close(); } catch { /* ignore */ }
      this.socket = null;
    }
    // Note: AudioContext, MediaStream, Analyser and levelTimer are preserved in standby
    // so acoustic energy is continuously analyzed for instant sub-60ms barge-in!
  }

  private fail(error: Error) {
    this.stopCapture();
    this.config.onError?.(error);
  }

  private stopCapture(closeSocket = true) {
    this.isListening = false;
    if (this.frameTimer !== null) window.clearInterval(this.frameTimer);
    if (this.levelTimer !== null) window.clearInterval(this.levelTimer);
    if (this.closeTimer !== null) window.clearTimeout(this.closeTimer);
    this.frameTimer = null;
    this.levelTimer = null;
    this.closeTimer = null;
    this.processor?.disconnect();
    this.source?.disconnect();
    this.analyser?.disconnect();
    this.silentGain?.disconnect();
    if (this.processor) this.processor.onaudioprocess = null;
    this.processor = null;
    this.source = null;
    this.analyser = null;
    this.silentGain = null;
    this.mediaStream?.getTracks().forEach((track) => track.stop());
    this.mediaStream = null;
    this.audioContext?.close().catch(() => undefined);
    this.audioContext = null;
    this.frames = [];
    this.frameOffset = 0;
    this.config.onAudioLevel?.(0);
    if (closeSocket && this.socket) {
      if (this.socket.readyState === WebSocket.OPEN) {
        try { this.socket.send(JSON.stringify({ type: 'close' })); } catch { /* socket may already be closing */ }
      }
      this.socket.close();
      this.socket = null;
    }
  }
}
