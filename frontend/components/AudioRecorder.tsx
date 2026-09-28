"use client";

import React, { useState, useRef, useEffect } from "react";
import { Mic, MicOff, Volume2, Globe, Sparkles, Loader2, AlertCircle } from "lucide-react";

export interface SupportedLanguage {
  code: string;
  label: string;
  nativeLabel: string;
}

export const SUPPORTED_LANGUAGES: SupportedLanguage[] = [
  { code: "unknown", label: "Auto-Detect", nativeLabel: "स्वतः पहचान" },
  { code: "hi-IN", label: "Hindi", nativeLabel: "हिन्दी" },
  { code: "ta-IN", label: "Tamil", nativeLabel: "தமிழ்" },
  { code: "te-IN", label: "Telugu", nativeLabel: "తెలుగు" },
  { code: "kn-IN", label: "Kannada", nativeLabel: "ಕನ್ನಡ" },
  { code: "mr-IN", label: "Marathi", nativeLabel: "मराठी" },
  { code: "bn-IN", label: "Bengali", nativeLabel: "বাংলা" },
  { code: "gu-IN", label: "Gujarati", nativeLabel: "ગુજરાતી" },
  { code: "pa-IN", label: "Punjabi", nativeLabel: "ਪੰਜਾਬੀ" },
  { code: "ml-IN", label: "Malayalam", nativeLabel: "മലയാളം" },
  { code: "od-IN", label: "Odia", nativeLabel: "ଓଡ଼ିଆ" },
  { code: "en-IN", label: "English", nativeLabel: "English" },
];

export interface TranscriptionResult {
  original_transcript: string;
  detected_language: string;
  translated_english: string;
  normalized_query: string;
  provider?: string;
}

interface AudioRecorderProps {
  apiBaseUrl?: string;
  onTranscriptionComplete: (result: TranscriptionResult) => void;
  selectedLanguage: string;
  onLanguageChange: (langCode: string) => void;
  disabled?: boolean;
}

export default function AudioRecorder({
  apiBaseUrl = "http://127.0.0.1:8000",
  onTranscriptionComplete,
  selectedLanguage,
  onLanguageChange,
  disabled = false
}: AudioRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [audioLevel, setAudioLevel] = useState<number[]>(new Array(7).fill(10));
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Clean up timer and media streams on unmount
  useEffect(() => {
    return () => {
      stopRecordingCleanup();
    };
  }, []);

  const stopRecordingCleanup = () => {
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
      timerIntervalRef.current = null;
    }
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== "closed") {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
  };

  const startVisualizer = (stream: MediaStream) => {
    try {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const ctx = new AudioCtx();
      audioContextRef.current = ctx;

      const analyser = ctx.createAnalyser();
      analyser.fftSize = 64;
      analyserRef.current = analyser;

      const source = ctx.createMediaStreamSource(stream);
      source.connect(analyser);

      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      const updateBars = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteFrequencyData(dataArray);

        // Sample 7 frequency bands for a smooth visualizer
        const bars: number[] = [];
        const step = Math.floor(bufferLength / 7) || 1;
        for (let i = 0; i < 7; i++) {
          const val = dataArray[i * step] || 0;
          // Scale from 0-255 to min 12% to max 100% height
          bars.push(Math.max(12, Math.min(100, Math.round((val / 255) * 100))));
        }
        setAudioLevel(bars);
        animationFrameRef.current = requestAnimationFrame(updateBars);
      };

      updateBars();
    } catch (e) {
      console.warn("Web Audio API visualization unavailable:", e);
    }
  };

  const startRecording = async () => {
    setErrorMessage(null);
    audioChunksRef.current = [];
    setRecordingSeconds(0);

    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("Microphone access is not supported in this browser environment.");
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });
      streamRef.current = stream;

      // Determine supported mimeType
      const mimeTypes = [
        "audio/webm;codecs=opus",
        "audio/webm",
        "audio/ogg;codecs=opus",
        "audio/mp4"
      ];
      let selectedMime = "";
      for (const m of mimeTypes) {
        if (MediaRecorder.isTypeSupported(m)) {
          selectedMime = m;
          break;
        }
      }

      const recorder = selectedMime
        ? new MediaRecorder(stream, { mimeType: selectedMime })
        : new MediaRecorder(stream);

      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        stopRecordingCleanup();
        setIsRecording(false);
        const finalBlob = new Blob(audioChunksRef.current, {
          type: recorder.mimeType || "audio/webm"
        });
        await handleAudioUpload(finalBlob);
      };

      recorder.start(250); // Emit chunk every 250ms
      setIsRecording(true);

      // Start live timer
      timerIntervalRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);

      // Start frequency visualizer
      startVisualizer(stream);
    } catch (err: unknown) {
      console.error("Microphone error:", err);
      const msg = err instanceof Error ? err.message : "Unable to access microphone.";
      setErrorMessage(msg);
      stopRecordingCleanup();
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop();
    }
  };

  const handleAudioUpload = async (audioBlob: Blob) => {
    setIsProcessing(true);
    setErrorMessage(null);

    try {
      const formData = new FormData();
      formData.append("file", audioBlob, "mic_input.webm");

      const langParam = selectedLanguage || "unknown";
      const endpoint = `${apiBaseUrl}/api/v1/multilingual/transcribe-and-translate?language_code=${encodeURIComponent(langParam)}`;

      const res = await fetch(endpoint, {
        method: "POST",
        body: formData
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Server returned error status ${res.status}`);
      }

      const data: TranscriptionResult = await res.json();
      onTranscriptionComplete(data);
    } catch (err: unknown) {
      console.error("Transcription upload error:", err);
      const msg = err instanceof Error ? err.message : "Audio processing failed.";
      setErrorMessage(msg);
    } finally {
      setIsProcessing(false);
    }
  };

  const formatTimer = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const remainder = secs % 60;
    return `${mins.toString().padStart(2, "0")}:${remainder.toString().padStart(2, "0")}`;
  };

  return (
    <div className="audio-recorder-widget" style={{ display: "flex", alignItems: "center", gap: 10 }}>
      {/* Language Selector Dropdown */}
      <div className="language-selector-wrapper" style={{ position: "relative" }}>
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          background: "rgba(15, 23, 42, 0.8)",
          border: "1px solid rgba(255, 255, 255, 0.12)",
          borderRadius: 12,
          padding: "6px 12px",
          color: "#94a3b8",
          fontSize: 13
        }}>
          <Globe size={14} color="#00f2fe" />
          <select
            value={selectedLanguage}
            onChange={(e) => onLanguageChange(e.target.value)}
            disabled={disabled || isRecording || isProcessing}
            style={{
              background: "transparent",
              border: "none",
              color: "#e2e8f0",
              fontSize: 13,
              fontFamily: "inherit",
              outline: "none",
              cursor: "pointer"
            }}
          >
            {SUPPORTED_LANGUAGES.map((lang) => (
              <option key={lang.code} value={lang.code} style={{ background: "#0d1424", color: "#f8fafc" }}>
                {lang.nativeLabel} ({lang.label})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Mic Recording Button & Live Wave Visualizer */}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        {!isRecording ? (
          <button
            type="button"
            className="mic-action-btn"
            onClick={startRecording}
            disabled={disabled || isProcessing}
            title="Click to speak in your regional Indian language (Sarvam AI Speech-to-Text)"
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              background: isProcessing
                ? "rgba(100, 116, 139, 0.2)"
                : "linear-gradient(135deg, rgba(0, 242, 254, 0.18) 0%, rgba(79, 172, 254, 0.22) 100%)",
              border: "1px solid rgba(0, 242, 254, 0.4)",
              color: "#00f2fe",
              padding: "8px 14px",
              borderRadius: 12,
              cursor: disabled || isProcessing ? "not-allowed" : "pointer",
              fontSize: 13,
              fontWeight: 600,
              transition: "all 0.2s ease",
              boxShadow: "0 0 12px rgba(0, 242, 254, 0.15)"
            }}
          >
            {isProcessing ? (
              <>
                <Loader2 className="animate-spin" size={16} />
                <span>Transcribing (Sarvam AI)...</span>
              </>
            ) : (
              <>
                <Mic size={16} />
                <span>Voice Ingest</span>
              </>
            )}
          </button>
        ) : (
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            background: "rgba(239, 68, 68, 0.12)",
            border: "1px solid rgba(239, 68, 68, 0.4)",
            borderRadius: 12,
            padding: "6px 14px"
          }}>
            {/* Pulsing Red Dot */}
            <div style={{
              width: 10,
              height: 10,
              borderRadius: "50%",
              backgroundColor: "#ef4444",
              boxShadow: "0 0 10px #ef4444",
              animation: "pulse 1s infinite alternate"
            }} />

            {/* Timer */}
            <span style={{
              fontSize: 13,
              fontWeight: 700,
              fontFamily: "var(--font-mono, monospace)",
              color: "#ef4444"
            }}>
              {formatTimer(recordingSeconds)}
            </span>

            {/* Live Audio Spectrum Bars */}
            <div style={{ display: "flex", alignItems: "center", gap: 3, height: 18, width: 42 }}>
              {audioLevel.map((lvl, idx) => (
                <div
                  key={idx}
                  style={{
                    flex: 1,
                    backgroundColor: "#00f2fe",
                    borderRadius: 2,
                    height: `${lvl}%`,
                    minHeight: 3,
                    transition: "height 0.08s ease"
                  }}
                />
              ))}
            </div>

            {/* Stop Recording Button */}
            <button
              type="button"
              onClick={stopRecording}
              style={{
                background: "#ef4444",
                border: "none",
                color: "#ffffff",
                padding: "4px 10px",
                borderRadius: 8,
                fontSize: 12,
                fontWeight: 700,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 4
              }}
            >
              <MicOff size={13} />
              <span>Stop</span>
            </button>
          </div>
        )}
      </div>

      {/* Error Notification */}
      {errorMessage && (
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          background: "rgba(239, 68, 68, 0.15)",
          border: "1px solid rgba(239, 68, 68, 0.3)",
          borderRadius: 8,
          padding: "4px 10px",
          color: "#fca5a5",
          fontSize: 12
        }}>
          <AlertCircle size={14} />
          <span>{errorMessage}</span>
        </div>
      )}
    </div>
  );
}
