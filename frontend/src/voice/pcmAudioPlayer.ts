type PlaybackCallbacks = {
  onStarted: () => void;
  onFinished: () => void;
  onLevel: (level: number) => void;
};

/** Schedules Gnani's raw 16-bit PCM chunks as soon as each arrives. */
export class PcmAudioPlayer {
  private context: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private sources = new Set<AudioBufferSourceNode>();
  private nextStartAt = 0;
  private chunkQueue: Promise<void> = Promise.resolve();
  private ended = false;
  private started = false;
  private animationFrame = 0;
  private startTimer = 0;
  private generation = 0;
  private callbacks: PlaybackCallbacks = { onStarted: () => {}, onFinished: () => {}, onLevel: () => {} };

  unlock() {
    if (!this.context) {
      this.context = new AudioContext();
      this.analyser = this.context.createAnalyser();
      this.analyser.fftSize = 256;
      this.analyser.connect(this.context.destination);
    }
    void this.context.resume();
  }

  begin(callbacks: PlaybackCallbacks) {
    this.generation += 1;
    this.unlock();
    this.callbacks = callbacks;
    this.nextStartAt = this.context!.currentTime + 0.04;
    this.ended = false;
    this.started = false;
    this.sampleOutput();
  }

  enqueue(base64: string, sampleRate: number) {
    const generation = this.generation;
    this.chunkQueue = this.chunkQueue.then(async () => {
      if (generation !== this.generation || !this.context || !this.analyser || !base64) return;
      await this.context.resume();
      const binary = atob(base64);
      const sampleCount = Math.floor(binary.length / 2);
      if (!sampleCount) return;
      const buffer = this.context.createBuffer(1, sampleCount, sampleRate);
      const channel = buffer.getChannelData(0);
      for (let i = 0; i < sampleCount; i += 1) {
        let sample = binary.charCodeAt(i * 2) | (binary.charCodeAt(i * 2 + 1) << 8);
        if (sample > 32767) sample -= 65536;
        channel[i] = sample / 32768;
      }
      const source = this.context.createBufferSource();
      source.buffer = buffer;
      source.connect(this.analyser!);
      const startAt = Math.max(this.nextStartAt, this.context!.currentTime + 0.015);
      source.onended = () => {
        this.sources.delete(source);
        this.finishIfReady();
      };
      source.start(startAt);
      this.sources.add(source);
      this.nextStartAt = startAt + buffer.duration;
      if (!this.started) {
        this.started = true;
        this.startTimer = window.setTimeout(() => {
          if (generation === this.generation) this.callbacks.onStarted();
        }, Math.max(0, (startAt - this.context!.currentTime) * 1000));
      }
    }).catch(() => undefined);
  }

  finish() {
    this.ended = true;
    this.chunkQueue.then(() => this.finishIfReady());
  }

  isPlaying() {
    return this.sources.size > 0;
  }

  cancel() {
    this.generation += 1;
    this.ended = false;
    if (this.startTimer) window.clearTimeout(this.startTimer);
    this.startTimer = 0;
    for (const source of this.sources) {
      try { source.stop(); } catch { /* already stopped */ }
    }
    this.sources.clear();
    this.nextStartAt = this.context?.currentTime || 0;
    this.started = false;
    if (this.animationFrame) cancelAnimationFrame(this.animationFrame);
    this.animationFrame = 0;
    this.callbacks.onLevel(0);
  }

  private finishIfReady() {
    if (!this.ended || this.sources.size > 0) return;
    this.ended = false;
    if (this.animationFrame) cancelAnimationFrame(this.animationFrame);
    this.animationFrame = 0;
    this.callbacks.onLevel(0);
    this.callbacks.onFinished();
  }

  private sampleOutput() {
    if (!this.analyser) return;
    const samples = new Uint8Array(this.analyser.fftSize);
    const measure = () => {
      if (!this.analyser) return;
      this.analyser.getByteTimeDomainData(samples);
      let energy = 0;
      for (const sample of samples) {
        const centered = (sample - 128) / 128;
        energy += centered * centered;
      }
      this.callbacks.onLevel(Math.min(1, Math.sqrt(energy / samples.length) * 3.5));
      this.animationFrame = requestAnimationFrame(measure);
    };
    if (this.animationFrame) cancelAnimationFrame(this.animationFrame);
    this.animationFrame = requestAnimationFrame(measure);
  }
}
