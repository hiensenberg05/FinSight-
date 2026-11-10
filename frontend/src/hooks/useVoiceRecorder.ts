import { useState, useRef, useCallback, useEffect } from 'react';
import { VoiceState } from '../types';

interface UseVoiceRecorderProps {
  onTranscriptReady?: (transcript: string) => void;
  onAudioRecorded?: (audioBlob: Blob) => void;
  onStateChange?: (state: VoiceState) => void;
}

// Window interface augmentation for browser speech recognition
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionInstance extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: Event) => void) | null;
  onend: (() => void) | null;
}

type SpeechRecognitionConstructor = new () => SpeechRecognitionInstance;

export const useVoiceRecorder = ({
  onTranscriptReady,
  onAudioRecorded,
  onStateChange,
}: UseVoiceRecorderProps = {}) => {
  const [voiceState, setVoiceState] = useState<VoiceState>('idle');
  const [audioLevel, setAudioLevel] = useState<number>(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const mediaStreamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);

  const updateState = useCallback(
    (newState: VoiceState) => {
      setVoiceState(newState);
      onStateChange?.(newState);
    },
    [onStateChange]
  );

  // Monitor audio levels via real Web Audio API AnalyserNode
  const monitorAudioLevels = useCallback(() => {
    if (!analyserRef.current) return;

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(dataArray);

    let sum = 0;
    for (let i = 0; i < dataArray.length; i++) {
      sum += dataArray[i];
    }
    const average = sum / dataArray.length;
    // Normalize to 0.0 - 1.0 range
    setAudioLevel(Math.min(1, average / 64));

    animationFrameRef.current = requestAnimationFrame(monitorAudioLevels);
  }, []);

  // Cleanup audio tracks and animation frame
  const cleanupStream = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // Ignored
      }
      recognitionRef.current = null;
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try {
        mediaRecorderRef.current.stop();
      } catch {
        // Ignored
      }
      mediaRecorderRef.current = null;
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    setAudioLevel(0);
  }, []);

  // Start real recording
  const startRecording = useCallback(async () => {
    setErrorMessage(null);
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Microphone capture is not supported in this browser environment.');
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      mediaStreamRef.current = stream;

      // Real audio chunk recording via MediaRecorder
      audioChunksRef.current = [];
      const mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4';
      const recorder = new MediaRecorder(stream, { mimeType });
      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };
      recorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
        onAudioRecorded?.(audioBlob);
      };
      recorder.start(100);
      mediaRecorderRef.current = recorder;

      // Setup Web Audio API Analyser for real-time waveform reactivity
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const audioContext = new AudioCtx();
      audioContextRef.current = audioContext;

      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 64;
      analyser.smoothingTimeConstant = 0.8;
      source.connect(analyser);
      analyserRef.current = analyser;

      // Browser native SpeechRecognition
      // TODO: Connect live Gnani.ai ASR WebSocket streaming endpoint for low-latency Indic speech recognition
      const SpeechRecognition = (window as unknown as { SpeechRecognition?: SpeechRecognitionConstructor; webkitSpeechRecognition?: SpeechRecognitionConstructor }).SpeechRecognition ||
        (window as unknown as { SpeechRecognition?: SpeechRecognitionConstructor; webkitSpeechRecognition?: SpeechRecognitionConstructor }).webkitSpeechRecognition;

      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-IN'; // Indian English

        recognition.onresult = (event: SpeechRecognitionEvent) => {
          const transcript = event.results[0]?.[0]?.transcript;
          if (transcript) {
            onTranscriptReady?.(transcript);
          }
        };

        recognition.onerror = () => {
          // If native recognition encounters an issue, fallback handled gracefully
        };

        recognition.start();
        recognitionRef.current = recognition;
      }

      updateState('listening');
      monitorAudioLevels();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Microphone permission denied or unavailable';
      setErrorMessage(message);
      updateState('error');
      // Reset error back to idle after 3.5 seconds
      setTimeout(() => {
        updateState('idle');
        setErrorMessage(null);
      }, 3500);
    }
  }, [updateState, monitorAudioLevels, onAudioRecorded, onTranscriptReady]);

  // Stop recording and trigger processing
  const stopRecording = useCallback(() => {
    cleanupStream();
    updateState('processing');
  }, [cleanupStream, updateState]);

  // Toggle voice recording
  const toggleRecording = useCallback(() => {
    if (voiceState === 'listening') {
      stopRecording();
    } else if (voiceState === 'idle' || voiceState === 'error') {
      startRecording();
    }
  }, [voiceState, startRecording, stopRecording]);

  useEffect(() => {
    return () => {
      cleanupStream();
    };
  }, [cleanupStream]);

  return {
    voiceState,
    setVoiceState: updateState,
    audioLevel,
    errorMessage,
    startRecording,
    stopRecording,
    toggleRecording,
  };
};
