import { useState, useEffect, useRef, useCallback } from 'react';

interface UseVoiceOptions {
  /** Called once with each finalised phrase the caller speaks. */
  onFinalResult?: (text: string) => void;
}

interface UseVoiceReturn {
  isListening: boolean;
  isSpeaking: boolean;
  transcript: string;
  isSupported: boolean;
  error: string | null;
  startListening: () => void;
  stopListening: () => void;
  speak: (text: string, onEnd?: () => void) => void;
  stopSpeaking: () => void;
  resetTranscript: () => void;
}

const ERROR_MESSAGES: Record<string, string> = {
  'not-allowed': 'Microphone access was blocked. Allow the microphone for this site in the browser address bar, then try again.',
  'service-not-allowed': 'Speech recognition is blocked by the browser. Check the site permissions.',
  'audio-capture': 'No microphone was found. Connect one or use the typed fallback below.',
  network: 'Speech recognition needs an internet connection (Chrome sends audio to Google). Use the typed fallback below.',
};

function pickVoice(synth: SpeechSynthesis): SpeechSynthesisVoice | null {
  const voices = synth.getVoices();
  return (
    voices.find((v) => v.lang === 'en-IN') ||
    voices.find((v) => v.lang.replace('_', '-').startsWith('en-IN')) ||
    voices.find((v) => v.lang.startsWith('en-GB')) ||
    voices.find((v) => v.lang.startsWith('en')) ||
    null
  );
}

export function useVoice(options: UseVoiceOptions = {}): UseVoiceReturn {
  const [isListening, setIsListening] = useState<boolean>(false);
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [transcript, setTranscript] = useState<string>('');
  const [isSupported, setIsSupported] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const recognitionRef = useRef<any>(null);
  const synthRef = useRef<SpeechSynthesis | null>(null);
  // True while the caller wants the mic open; lets us auto-restart after Chrome's silence timeout.
  const wantListeningRef = useRef<boolean>(false);
  // Bumped by every speak()/stopSpeaking() so a cancelled utterance's late onend can't resume the mic.
  const speechTokenRef = useRef<number>(0);
  const resumeAfterSpeechRef = useRef<boolean>(false);
  const onFinalRef = useRef<UseVoiceOptions['onFinalResult']>(options.onFinalResult);
  onFinalRef.current = options.onFinalResult;

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setIsSupported(false);
      setError('Voice input needs Google Chrome or Microsoft Edge. Use the typed fallback below.');
    } else {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-IN'; // Indian English preferred for home loans
      recognition.maxAlternatives = 1;

      recognition.onstart = () => setIsListening(true);
      recognition.onend = () => {
        setIsListening(false);
        // Chrome ends sessions after a few seconds of silence; keep the call hot-mic until told to stop.
        if (wantListeningRef.current) {
          setTimeout(() => {
            if (!wantListeningRef.current) return;
            try {
              recognition.start();
            } catch (_) {
              /* already started */
            }
          }, 250);
        }
      };
      recognition.onerror = (e: any) => {
        if (e.error === 'no-speech' || e.error === 'aborted') return; // benign; onend restarts
        console.warn('Speech recognition error:', e.error);
        setError(ERROR_MESSAGES[e.error] || `Speech recognition error: ${e.error}`);
        if (e.error === 'not-allowed' || e.error === 'service-not-allowed' || e.error === 'audio-capture') {
          wantListeningRef.current = false;
        }
        setIsListening(false);
      };
      recognition.onresult = (event: any) => {
        let interim = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const result = event.results[i];
          const text: string = result[0].transcript;
          if (result.isFinal) {
            const finalText = text.trim();
            setTranscript('');
            if (finalText) onFinalRef.current?.(finalText);
          } else {
            interim += text;
          }
        }
        if (interim) setTranscript(interim);
      };

      recognitionRef.current = recognition;
    }

    if ('speechSynthesis' in window) {
      synthRef.current = window.speechSynthesis;
      // Chrome loads voices asynchronously; touching getVoices() primes the list.
      synthRef.current.getVoices();
    }

    return () => {
      wantListeningRef.current = false;
      try {
        recognitionRef.current?.abort();
      } catch (_) {
        /* ignore */
      }
      synthRef.current?.cancel();
    };
  }, []);

  const startListening = useCallback(() => {
    const recognition = recognitionRef.current;
    if (!recognition) return;
    setError(null);
    wantListeningRef.current = true;
    try {
      recognition.start();
    } catch (_) {
      /* already running */
    }
  }, []);

  const stopListening = useCallback(() => {
    wantListeningRef.current = false;
    resumeAfterSpeechRef.current = false;
    try {
      recognitionRef.current?.stop();
    } catch (_) {
      /* ignore */
    }
  }, []);

  const stopSpeaking = useCallback(() => {
    speechTokenRef.current += 1;
    resumeAfterSpeechRef.current = false;
    synthRef.current?.cancel();
    setIsSpeaking(false);
  }, []);

  const speak = useCallback((text: string, onEnd?: () => void) => {
    const synth = synthRef.current;
    if (!synth || !text) {
      onEnd?.();
      return;
    }

    // Strip markdown/code symbols so they are not read aloud (V2 Plain Speech)
    const cleanText = text.replace(/[*_#`~[\]]/g, '').replace(/\s+/g, ' ').trim();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = 'en-IN';
    const voice = pickVoice(synth);
    if (voice) utterance.voice = voice;
    utterance.rate = 0.95;
    utterance.pitch = 1.0;

    // The mic would otherwise hear the agent's own voice and answer itself: pause it while speaking.
    const resume = wantListeningRef.current || resumeAfterSpeechRef.current;
    resumeAfterSpeechRef.current = resume;
    if (resume) {
      wantListeningRef.current = false;
      try {
        recognitionRef.current?.abort();
      } catch (_) {
        /* ignore */
      }
    }

    const token = ++speechTokenRef.current;
    let finished = false;
    const finish = () => {
      if (finished) return;
      finished = true;
      if (token !== speechTokenRef.current) return; // superseded or cancelled
      setIsSpeaking(false);
      resumeAfterSpeechRef.current = false;
      if (resume) {
        wantListeningRef.current = true;
        try {
          recognitionRef.current?.start();
        } catch (_) {
          /* already running */
        }
      }
      onEnd?.();
    };
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = finish;
    utterance.onerror = finish;

    // Chrome drops a speak() issued in the same tick as cancel(); give it a beat.
    synth.cancel();
    setTimeout(() => synth.speak(utterance), 60);
  }, []);

  const resetTranscript = useCallback(() => setTranscript(''), []);

  return {
    isListening,
    isSpeaking,
    transcript,
    isSupported,
    error,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
    resetTranscript,
  };
}
