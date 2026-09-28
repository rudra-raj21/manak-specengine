"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Search,
  ShieldAlert,
  FileCheck2,
  GitFork,
  BookOpen,
  Copy,
  Check,
  Building2,
  AlertTriangle,
  Scale,
  Sparkles,
  Globe2,
  RefreshCw,
  ExternalLink,
  ChevronRight,
  Sun,
  Moon,
  Volume2,
  VolumeX,
  UploadCloud,
  FileText,
  Printer,
  Share2,
  Layers,
  History,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  HelpCircle,
  PackageCheck,
  X
} from "lucide-react";
import GraphCanvas, { GraphData, GraphNode } from "./components/GraphCanvas";
import AudioRecorder, { TranscriptionResult } from "./components/AudioRecorder";

const API_BASE = "http://127.0.0.1:8000";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"finder" | "auditor" | "qcos" | "graph">("finder");

  // Dimension 5: Daylight High-Contrast Mode (Outdoor Site Inspection)
  const [isDaylight, setIsDaylight] = useState(false);

  // System Health
  const [healthData, setHealthData] = useState<{
    standards_indexed: number;
    qco_orders_active: number;
    graph_relationships: number;
    status: string;
  }>({
    standards_indexed: 21932,
    qco_orders_active: 192,
    graph_relationships: 8025,
    status: "healthy"
  });

  // Mode A: Standard Finder & Multilingual Voice State
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [recommendationResult, setRecommendationResult] = useState<any>(null);
  const [copiedClause, setCopiedClause] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState<string>("unknown");
  const [multilingualMetadata, setMultilingualMetadata] = useState<any>(null);

  // Dimension 2: Sarvam AI Voice-Back Text-to-Speech (bulbul:v3)
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);

  // Dimension 3: Clause-Level Specification Breakdown
  const [clauseData, setClauseData] = useState<any>(null);
  const [activeClauseTab, setActiveClauseTab] = useState<"mechanical" | "chemical" | "testing">("mechanical");
  const [isFetchingClause, setIsFetchingClause] = useState(false);

  // Dimension 3: BIS CM/L License Verifier Modal State
  const [showCmlModal, setShowCmlModal] = useState(false);
  const [cmlInput, setCmlInput] = useState("8400124");
  const [cmlResult, setCmlResult] = useState<any>(null);
  const [isVerifyingCml, setIsVerifyingCml] = useState(false);

  // Mode B: Tender Auditor State
  const [tenderText, setTenderText] = useState("");
  const [isAuditing, setIsAuditing] = useState(false);
  const [auditResult, setAuditResult] = useState<any>(null);
  const [copiedCorrigendum, setCopiedCorrigendum] = useState(false);
  const [activeAuditorSubtab, setActiveAuditorSubtab] = useState<"findings" | "diff" | "corrigendum">("findings");
  const [isUploadingFile, setIsUploadingFile] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Mode C: QCO Directory State
  const [qcosList, setQcosList] = useState<any[]>([]);
  const [qcoFilterMinistry, setQcoFilterMinistry] = useState<string>("All");
  const [qcoSearchTerm, setQcoSearchTerm] = useState<string>("");

  // Mode D: Graph Explorer State
  const [graphQuery, setGraphQuery] = useState("IS 2062");
  const [graphData, setGraphData] = useState<GraphData | null>(null);

  // Dimension 4: Temporal Version Evolution & Shortest Path Tracing
  const [timelineData, setTimelineData] = useState<any>(null);
  const [activeTimelineIndex, setActiveTimelineIndex] = useState(0);
  const [pathSource, setPathSource] = useState("IS 456");
  const [pathTarget, setPathTarget] = useState("IS 1786");
  const [pathResult, setPathResult] = useState<any>(null);
  const [isFindingPath, setIsFindingPath] = useState(false);
  const [clusterData, setClusterData] = useState<any>(null);

  // Sample Scenarios & Sharing
  const [sampleScenarios, setSampleScenarios] = useState<any>(null);
  const [copiedPermalink, setCopiedPermalink] = useState(false);

  // Initialize Daylight Mode & Core Data
  useEffect(() => {
    // Check saved daylight preference
    const savedTheme = localStorage.getItem("manak_theme");
    if (savedTheme === "daylight") {
      setIsDaylight(true);
      document.body.classList.add("daylight-theme");
    }

    fetch(`${API_BASE}/health`)
      .then(res => res.json())
      .then(data => setHealthData(data))
      .catch(() => console.log("Using local health metadata."));

    fetch(`${API_BASE}/api/samples`)
      .then(res => res.json())
      .then(data => setSampleScenarios(data))
      .catch(() => console.log("Using bundled samples."));

    fetch(`${API_BASE}/api/qcos`)
      .then(res => res.json())
      .then(data => setQcosList(data))
      .catch(() => console.log("Using cached QCOs."));

    fetch(`${API_BASE}/api/graph/clusters`)
      .then(res => res.json())
      .then(data => setClusterData(data))
      .catch(() => console.log("Clusters fetched"));

    // Execute initial search for IS 2062
    handleSearch("Supply of hot rolled structural steel plates and beams for bridges");
    loadGraphNeighborhood("IS_2062");
    loadTimeline("IS 2062");
  }, []);

  const toggleDaylight = () => {
    const next = !isDaylight;
    setIsDaylight(next);
    if (next) {
      document.body.classList.add("daylight-theme");
      localStorage.setItem("manak_theme", "daylight");
    } else {
      document.body.classList.remove("daylight-theme");
      localStorage.setItem("manak_theme", "dark");
    }
  };

  const handleSearch = async (searchQuery: string, langCode?: string, metaOverride?: any) => {
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    setQuery(searchQuery);

    const targetLang = langCode !== undefined ? langCode : selectedLanguage;

    try {
      const res = await fetch(`${API_BASE}/api/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: searchQuery,
          language_code: targetLang === "unknown" ? undefined : targetLang,
          top_k: 5,
          tender_type: "GeM"
        })
      });
      const data = await res.json();
      setRecommendationResult(data);
      if (data.language_metadata) {
        setMultilingualMetadata(data.language_metadata);
      } else if (metaOverride) {
        setMultilingualMetadata(metaOverride);
      }

      // Fetch clause breakdown for primary match
      if (data.primary_match?.is_number) {
        fetchClauseBreakdown(data.primary_match.is_number);
        loadTimeline(data.primary_match.is_number);
      }
    } catch (e) {
      console.error("Search API error:", e);
    } finally {
      setIsSearching(false);
    }
  };

  const fetchClauseBreakdown = async (stdNumber: string) => {
    setIsFetchingClause(true);
    try {
      const res = await fetch(`${API_BASE}/api/clauses/${encodeURIComponent(stdNumber)}`);
      const data = await res.json();
      setClauseData(data);
    } catch (e) {
      console.error("Error fetching clause details:", e);
    } finally {
      setIsFetchingClause(false);
    }
  };

  const loadTimeline = async (stdNumber: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/graph/timeline/${encodeURIComponent(stdNumber)}`);
      const data = await res.json();
      setTimelineData(data);
      if (data.milestones?.length > 0) {
        setActiveTimelineIndex(data.milestones.length - 1);
      }
    } catch (e) {
      console.error("Timeline error:", e);
    }
  };

  const findShortestNormativePath = async () => {
    if (!pathSource.trim() || !pathTarget.trim()) return;
    setIsFindingPath(true);
    try {
      const res = await fetch(`${API_BASE}/api/graph/path?source=${encodeURIComponent(pathSource)}&target=${encodeURIComponent(pathTarget)}`);
      const data = await res.json();
      setPathResult(data);
    } catch (e) {
      console.error("Path error:", e);
    } finally {
      setIsFindingPath(false);
    }
  };

  const handleTranscriptionComplete = (result: TranscriptionResult) => {
    setQuery(result.original_transcript);
    const meta = {
      original_query: result.original_transcript,
      detected_language: result.detected_language,
      translated_english: result.translated_english,
      normalized_query: result.normalized_query,
      provider: result.provider || "Sarvam AI (saarika:v2 + mayura:v1)"
    };
    setMultilingualMetadata(meta);
    handleSearch(result.original_transcript, result.detected_language, meta);
  };

  // Dimension 2: Voice-Back Audio Player (Sarvam AI bulbul:v3)
  const playSpeechAudio = async (textToSpeak: string, langCode: string = "hi-IN") => {
    if (isPlayingAudio && currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
      setIsPlayingAudio(false);
      return;
    }

    setIsPlayingAudio(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/multilingual/text-to-speech`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: textToSpeak,
          language_code: langCode,
          speaker: "aditya"
        })
      });

      const data = await res.json();
      if (data.audio_base64) {
        const audio = new Audio(`data:audio/wav;base64,${data.audio_base64}`);
        currentAudioRef.current = audio;
        audio.onended = () => {
          setIsPlayingAudio(false);
          currentAudioRef.current = null;
        };
        audio.onerror = () => {
          setIsPlayingAudio(false);
          currentAudioRef.current = null;
        };
        await audio.play();
      } else {
        setIsPlayingAudio(false);
      }
    } catch (e) {
      console.error("Voice playback error:", e);
      setIsPlayingAudio(false);
    }
  };

  // Dimension 3: BIS CM/L License Verifier
  const verifyCmlNumber = async (numToVerify?: string) => {
    const target = numToVerify || cmlInput;
    if (!target.trim()) return;
    setIsVerifyingCml(true);
    try {
      const res = await fetch(`${API_BASE}/api/cml/verify?cml_number=${encodeURIComponent(target)}`);
      const data = await res.json();
      setCmlResult(data);
    } catch (e) {
      console.error("CML verification error:", e);
    } finally {
      setIsVerifyingCml(false);
    }
  };

  // Dimension 1: File Upload Handler for Tender Documents (.pdf, .txt)
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploadingFile(true);
    setIsAuditing(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${API_BASE}/api/audit/upload`, {
        method: "POST",
        body: formData
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Upload audit failed");
      }

      const data = await res.json();
      setAuditResult(data);
      setTenderText(`[DOCUMENT UPLOADED: ${file.name}]\nFile Size: ${(file.size / 1024).toFixed(1)} KB\nAudited Clauses & Findings loaded successfully.`);
      setActiveAuditorSubtab("findings");
    } catch (err) {
      console.error("File audit error:", err);
      alert(err instanceof Error ? err.message : "Failed to parse tender file.");
    } finally {
      setIsUploadingFile(false);
      setIsAuditing(false);
    }
  };

  const handleAudit = async (textToAudit?: string) => {
    const raw = textToAudit !== undefined ? textToAudit : tenderText;
    if (!raw.trim()) return;
    setIsAuditing(true);

    try {
      const res = await fetch(`${API_BASE}/api/audit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          raw_text: raw,
          tender_id: "GEM/2026/AUDIT/01",
          tender_title: "Procurement Compliance Audit"
        })
      });
      const data = await res.json();
      setAuditResult(data);
    } catch (e) {
      console.error("Audit API error:", e);
    } finally {
      setIsAuditing(false);
    }
  };

  const loadGraphNeighborhood = async (nodeId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/graph/${nodeId}?max_nodes=35`);
      const data = await res.json();
      setGraphData(data);
    } catch (e) {
      console.error("Graph API error:", e);
    }
  };

  const copyToClipboard = (text: string, type: "clause" | "corrigendum") => {
    navigator.clipboard.writeText(text);
    if (type === "clause") {
      setCopiedClause(true);
      setTimeout(() => setCopiedClause(false), 2000);
    } else {
      setCopiedCorrigendum(true);
      setTimeout(() => setCopiedCorrigendum(false), 2000);
    }
  };

  const copyPermalink = () => {
    const url = window.location.href;
    navigator.clipboard.writeText(url);
    setCopiedPermalink(true);
    setTimeout(() => setCopiedPermalink(false), 2000);
  };

  const triggerPrintCorrigendum = () => {
    window.print();
  };

  const filteredQcos = qcosList.filter(q => {
    const matchMin = qcoFilterMinistry === "All" || (q.ministry_id && q.ministry_id.toLowerCase().includes(qcoFilterMinistry.toLowerCase()));
    const matchSearch = !qcoSearchTerm || (q.order_name && q.order_name.toLowerCase().includes(qcoSearchTerm.toLowerCase())) || (q.gazette_no && q.gazette_no.toLowerCase().includes(qcoSearchTerm.toLowerCase()));
    return matchMin && matchSearch;
  });

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header-glass">
        <div className="brand-wrapper">
          <div className="brand-emblem">IS</div>
          <div>
            <h1 className="brand-title">MANAK-SPECENGINE</h1>
            <p className="brand-sub">National Standards AI Recommendation & Compliance Verification Engine (BIS)</p>
          </div>
        </div>

        <div className="status-pills" style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div className="status-pill">
            <span className="status-dot-pulse"></span>
            Standards: <strong>{healthData.standards_indexed.toLocaleString()}</strong>
          </div>
          <div className="status-pill">
            QCO Orders: <strong>{healthData.qco_orders_active}</strong>
          </div>

          {/* Dimension 3: BIS CM/L License Verifier Modal Trigger */}
          <button
            onClick={() => {
              setShowCmlModal(true);
              verifyCmlNumber("8400124");
            }}
            className="copy-btn"
            style={{ background: "rgba(16, 185, 129, 0.15)", color: "#10b981", borderColor: "rgba(16, 185, 129, 0.3)" }}
            title="Verify 7-digit BIS Certification Marks License (CM/L)"
          >
            <ShieldCheck size={14} /> Verify BIS CM/L
          </button>

          {/* Dimension 5: Share Permalinks */}
          <button
            onClick={copyPermalink}
            className="copy-btn"
            title="Copy shareable inspection link"
          >
            {copiedPermalink ? <Check size={14} color="#10b981" /> : <Share2 size={14} />}
            {copiedPermalink ? "Link Copied!" : "Share"}
          </button>

          {/* Dimension 5: Daylight / Dark Theme Toggle */}
          <button
            onClick={toggleDaylight}
            className="copy-btn"
            title={isDaylight ? "Switch to Dark Cyber GovTech Mode" : "Switch to Daylight High-Contrast Mode (Outdoor Site Inspection)"}
            style={{ padding: "8px 10px" }}
          >
            {isDaylight ? <Moon size={15} color="#0284c7" /> : <Sun size={15} color="#f59e0b" />}
          </button>
        </div>
      </header>

      {/* Tabs */}
      <nav className="tab-bar">
        <button
          className={`tab-btn ${activeTab === "finder" ? "active" : ""}`}
          onClick={() => setActiveTab("finder")}
        >
          <Search size={16} /> Mode A: Smart Finder & Clause Synthesizer
        </button>
        <button
          className={`tab-btn ${activeTab === "auditor" ? "active" : ""}`}
          onClick={() => setActiveTab("auditor")}
        >
          <ShieldAlert size={16} /> Mode B: Tender Specification Auditor
        </button>
        <button
          className={`tab-btn ${activeTab === "qcos" ? "active" : ""}`}
          onClick={() => setActiveTab("qcos")}
        >
          <Scale size={16} /> Mode C: Statutory QCO Registry
        </button>
        <button
          className={`tab-btn ${activeTab === "graph" ? "active" : ""}`}
          onClick={() => setActiveTab("graph")}
        >
          <GitFork size={16} /> Mode D: Knowledge Graph Explorer
        </button>
      </nav>

      {/* ========================================================================= */}
      {/* MODE A: SMART STANDARD FINDER & TENDER CLAUSE SYNTHESIZER */}
      {/* ========================================================================= */}
      {activeTab === "finder" && (
        <div>
          {/* Search Box Card with Sarvam AI Voice & Multilingual Ingestion */}
          <div className="card-glass" style={{ marginBottom: 28 }}>
            <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 12, marginBottom: 16 }}>
              <div className="search-input-wrapper" style={{ flex: "1 1 540px" }}>
                <Search className="search-icon" size={22} />
                <input
                  type="text"
                  className="search-input"
                  placeholder="Speak into microphone or enter procurement specification in any Indian language / Hinglish..."
                  value={query}
                  onChange={e => setQuery(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && handleSearch(query)}
                />
                <button
                  className="search-btn"
                  onClick={() => handleSearch(query)}
                  disabled={isSearching}
                >
                  {isSearching ? <RefreshCw className="animate-spin" size={16} /> : <Sparkles size={16} />}
                  Synthesize Spec
                </button>
              </div>

              {/* Sarvam AI Multilingual Audio Recording & Language Selector */}
              <AudioRecorder
                onTranscriptionComplete={handleTranscriptionComplete}
                selectedLanguage={selectedLanguage}
                onLanguageChange={setSelectedLanguage}
                disabled={isSearching}
              />
            </div>

            {/* Multilingual Regional & GovTech Query Chips */}
            <div className="chips-row">
              <span className="chip-label">Multilingual Demo Ingest:</span>
              <button
                className="chip-btn"
                onClick={() => handleSearch("Supply of hot rolled structural steel plates Grade E250 and beams", "en-IN")}
              >
                Structural Steel (IS 2062)
              </button>
              <button
                className="chip-btn"
                onClick={() => handleSearch("छत ढलाई के लिए सीमेंट और सरिया", "hi-IN")}
                style={{ borderColor: "rgba(168, 85, 247, 0.5)", color: "#c084fc", background: "rgba(168, 85, 247, 0.08)" }}
              >
                <Globe2 size={12} style={{ display: "inline", marginRight: 4 }} />
                हिन्दी: छत ढलाई सरिया व सीमेंट (IS 1786/269)
              </button>
              <button
                className="chip-btn"
                onClick={() => handleSearch("பூமிக்கடியில் புதைக்கப்படும் குடிநீர் விநியோகத்திற்கான பிவிசி குழாய்கள்", "ta-IN")}
                style={{ borderColor: "rgba(0, 242, 254, 0.4)", color: "#00f2fe", background: "rgba(0, 242, 254, 0.08)" }}
              >
                <Globe2 size={12} style={{ display: "inline", marginRight: 4 }} />
                தமிழ்: குடிநீர் பிவிசி குழாய்கள் (IS 4985)
              </button>
              <button
                className="chip-btn"
                onClick={() => handleSearch("औद्योगिक सुरक्षा हेल्मेट पिवळा रंग", "mr-IN")}
                style={{ borderColor: "rgba(245, 158, 11, 0.4)", color: "#f59e0b", background: "rgba(245, 158, 11, 0.08)" }}
              >
                <Globe2 size={12} style={{ display: "inline", marginRight: 4 }} />
                मराठी: सुरक्षा हेल्मेट (IS 2925)
              </button>
              <button
                className="chip-btn"
                onClick={() => handleSearch("পিভিসি পাইপ পানীয় জলের জন্য", "bn-IN")}
                style={{ borderColor: "rgba(16, 185, 129, 0.4)", color: "#10b981", background: "rgba(16, 185, 129, 0.08)" }}
              >
                <Globe2 size={12} style={{ display: "inline", marginRight: 4 }} />
                বাংলা: পিভিসি পাইপ (IS 4985)
              </button>
              <button
                className="chip-btn"
                onClick={() => handleSearch("Commercial laptops with lithium batteries and AC power adapters", "en-IN")}
              >
                IT Laptops (IS 13252)
              </button>
            </div>
          </div>

          {/* DUAL-LANGUAGE QUERY CARD (Sarvam AI Ingestion) */}
          {multilingualMetadata && (multilingualMetadata.detected_language !== "en-IN" || multilingualMetadata.bypassed === false || multilingualMetadata.provider?.includes("Sarvam")) && (
            <div className="card-glass" style={{
              marginBottom: 24,
              borderLeft: "4px solid #a855f7",
              background: "linear-gradient(135deg, rgba(168, 85, 247, 0.08) 0%, rgba(14, 21, 37, 0.95) 100%)",
              boxShadow: "0 0 25px rgba(168, 85, 247, 0.15)"
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span className="badge" style={{ background: "rgba(168, 85, 247, 0.18)", color: "#c084fc", border: "1px solid rgba(168, 85, 247, 0.35)", fontWeight: 600 }}>
                    <Globe2 size={13} style={{ marginRight: 4 }} /> Sarvam AI Multilingual Voice & Text Pipeline
                  </span>
                  <span className="badge badge-cyan" style={{ fontSize: 11, fontWeight: 700 }}>
                    Language: {multilingualMetadata.detected_language || "hi-IN"}
                  </span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  {/* Dimension 2: Voice-Back Audio Button */}
                  <button
                    onClick={() => playSpeechAudio(
                      multilingualMetadata.original_query || multilingualMetadata.translated_english,
                      multilingualMetadata.detected_language || "hi-IN"
                    )}
                    className="copy-btn"
                    style={{ background: isPlayingAudio ? "rgba(239, 68, 68, 0.2)" : "rgba(168, 85, 247, 0.2)", color: isPlayingAudio ? "#f87171" : "#c084fc" }}
                    title="Listen to verification audio via Sarvam AI bulbul:v3"
                  >
                    {isPlayingAudio ? <VolumeX size={14} /> : <Volume2 size={14} />}
                    {isPlayingAudio ? "Stop Audio" : "Listen via Sarvam AI"}
                  </button>
                  <span style={{ fontSize: 12, color: "#94a3b8" }}>
                    Speech: <strong style={{ color: "#c084fc" }}>saarika:v2</strong> &bull; Translation: <strong style={{ color: "#38bdf8" }}>mayura:v1</strong> &bull; Voice: <strong style={{ color: "#10b981" }}>bulbul:v3</strong>
                  </span>
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                {/* 1. Regional Script / Heard Speech */}
                <div style={{ background: "rgba(11, 17, 31, 0.8)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: 12, padding: "14px 16px" }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: "#a855f7", marginBottom: 6, display: "flex", alignItems: "center", gap: 6 }}>
                    <span>🎙️ Heard (Voice / Regional Vernacular):</span>
                  </div>
                  <p style={{ fontSize: 16, color: "#f8fafc", fontWeight: 500, lineHeight: 1.5 }}>
                    &ldquo;{multilingualMetadata.original_query || query}&rdquo;
                  </p>
                </div>

                {/* 2. Translated English */}
                <div style={{ background: "rgba(11, 17, 31, 0.8)", border: "1px solid rgba(0, 242, 254, 0.25)", borderRadius: 12, padding: "14px 16px" }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: "#00f2fe", marginBottom: 6, display: "flex", alignItems: "center", gap: 6 }}>
                    <span>🌐 Translated via Sarvam AI (mayura:v1):</span>
                  </div>
                  <p style={{ fontSize: 16, color: "#38bdf8", fontWeight: 600, lineHeight: 1.5 }}>
                    &ldquo;{multilingualMetadata.translated_english}&rdquo;
                  </p>
                </div>
              </div>

              {/* 3. Normalized Procurement Specification */}
              {multilingualMetadata.normalized_query && (
                <div style={{ marginTop: 14, background: "rgba(16, 185, 129, 0.08)", border: "1px solid rgba(16, 185, 129, 0.25)", borderRadius: 10, padding: "10px 14px", fontSize: 13, color: "#a7f3d0", display: "flex", alignItems: "center", gap: 10 }}>
                  <span style={{ fontWeight: 700, color: "#10b981", whiteSpace: "nowrap" }}>📋 Normalized Spec & Target BIS Standards:</span>
                  <span style={{ color: "#f1f5f9" }}>{multilingualMetadata.normalized_query}</span>
                </div>
              )}
            </div>
          )}

          {/* Disambiguation Dialogue Banner */}
          {recommendationResult?.disambiguation?.is_ambiguous && (
            <div className="card-glass" style={{ marginBottom: 24, borderLeft: "4px solid var(--accent-gold)", background: "rgba(245, 158, 11, 0.05)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                <HelpCircle size={16} color="#fbbf24" />
                <span className="badge badge-gold" style={{ fontSize: 11 }}>Active Disambiguation Clarifier</span>
              </div>
              <div style={{ fontSize: 14, fontWeight: 600, color: "#ffffff", marginBottom: 12 }}>
                {recommendationResult.disambiguation.prompt}
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
                {recommendationResult.disambiguation.options?.map((opt: any, idx: number) => (
                  <button
                    key={idx}
                    className="tab-btn"
                    style={{ padding: "8px 14px", fontSize: 12, textAlign: "left", display: "flex", flexDirection: "column", gap: 2, cursor: "pointer" }}
                    onClick={() => handleSearch(`${opt.standard_number} ${opt.label}`)}
                  >
                    <span style={{ fontWeight: 700, color: "var(--accent-cyan)" }}>{opt.standard_number} &bull; {opt.label}</span>
                    <span style={{ fontSize: 11, color: "var(--text-muted)" }}>{opt.typical_grade}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Results Grid */}
          {recommendationResult && (
            <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 24 }}>
              {/* Left Column: Recommendation & Legal Clause */}
              <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
                {/* Primary Standard Card */}
                <div className="card-glass" style={{ borderLeft: "4px solid var(--accent-cyan)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                    <div>
                      <span className="badge badge-cyan" style={{ marginBottom: 8 }}>Primary Recommended Standard</span>
                      <h2 style={{ fontSize: 22, fontWeight: 700, color: "#ffffff" }}>
                        {recommendationResult.primary_match?.is_number}
                        {recommendationResult.primary_match?.year ? `:${recommendationResult.primary_match.year}` : ""}
                      </h2>
                    </div>
                    <span className="badge badge-emerald">
                      {recommendationResult.primary_match?.status || "ACTIVE"}
                    </span>
                  </div>

                  <p style={{ fontSize: 15, color: "#cbd5e1", lineHeight: 1.5, marginBottom: 14 }}>
                    {recommendationResult.primary_match?.title}
                  </p>

                  {/* Schedule of Rates Grounding */}
                  {recommendationResult.schedule_of_rates && (
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12, padding: "6px 12px", background: "rgba(56, 189, 248, 0.08)", border: "1px solid rgba(56, 189, 248, 0.2)", borderRadius: 6, fontSize: 12, color: "var(--accent-cyan)" }}>
                      <Building2 size={13} />
                      <span><strong>Schedule of Rates Grounded:</strong> {recommendationResult.schedule_of_rates.schedule} &bull; <em>{recommendationResult.schedule_of_rates.item_code}</em></span>
                    </div>
                  )}

                  {/* Extracted Engineering Constraints */}
                  {recommendationResult.extracted_constraints?.has_special_constraints && (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 14 }}>
                      {recommendationResult.extracted_constraints.exposure_class && (
                        <span className="badge badge-blue" style={{ fontSize: 11 }}>Exposure: {recommendationResult.extracted_constraints.exposure_class.toUpperCase()}</span>
                      )}
                      {recommendationResult.extracted_constraints.seismic_zone && (
                        <span className="badge badge-purple" style={{ fontSize: 11 }}>Seismic: {recommendationResult.extracted_constraints.seismic_zone.toUpperCase()}</span>
                      )}
                      {recommendationResult.extracted_constraints.requires_crs && (
                        <span className="badge badge-emerald" style={{ fontSize: 11 }}>CRS Mandated (IS 1786)</span>
                      )}
                      {recommendationResult.extracted_constraints.requires_ductility && (
                        <span className="badge badge-cyan" style={{ fontSize: 11 }}>Ductile Detailing (IS 13920)</span>
                      )}
                    </div>
                  )}

                  <div style={{ display: "flex", gap: 16, fontSize: 13, color: "var(--text-secondary)" }}>
                    <div>Committee: <strong style={{ color: "#ffffff" }}>{recommendationResult.primary_match?.committee || "CED 54"}</strong></div>
                    <div>Department: <strong style={{ color: "#ffffff" }}>{recommendationResult.primary_match?.department || "Civil"}</strong></div>
                  </div>
                </div>

                {/* Dimension 3: Granular Clause-Level Engineering Properties Tables */}
                {clauseData && (
                  <div className="card-glass" style={{ borderLeft: "4px solid var(--accent-emerald)" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
                      <div>
                        <span className="badge badge-emerald" style={{ marginBottom: 4 }}>
                          <Layers size={12} /> Granular Clause-Level Tolerances & Engineering Tables
                        </span>
                        <h3 style={{ fontSize: 16, fontWeight: 700, color: "#ffffff" }}>
                          {clauseData.current_revision}
                        </h3>
                      </div>
                      <div style={{ display: "flex", gap: 6 }}>
                        <button
                          className={`tab-btn ${activeClauseTab === "mechanical" ? "active" : ""}`}
                          style={{ padding: "6px 12px", fontSize: 12 }}
                          onClick={() => setActiveClauseTab("mechanical")}
                        >
                          Mechanical
                        </button>
                        <button
                          className={`tab-btn ${activeClauseTab === "chemical" ? "active" : ""}`}
                          style={{ padding: "6px 12px", fontSize: 12 }}
                          onClick={() => setActiveClauseTab("chemical")}
                        >
                          Chemical
                        </button>
                        <button
                          className={`tab-btn ${activeClauseTab === "testing" ? "active" : ""}`}
                          style={{ padding: "6px 12px", fontSize: 12 }}
                          onClick={() => setActiveClauseTab("testing")}
                        >
                          Testing Protocols
                        </button>
                      </div>
                    </div>

                    {/* Mechanical Table */}
                    {activeClauseTab === "mechanical" && clauseData.mechanical_properties && (
                      <div>
                        <div style={{ fontSize: 12, color: "#94a3b8", marginBottom: 6 }}>
                          Reference: <strong style={{ color: "#ffffff" }}>{clauseData.mechanical_properties.clause}</strong> &bull; {clauseData.mechanical_properties.table_title}
                        </div>
                        <div style={{ overflowX: "auto" }}>
                          <table className="clause-table">
                            <thead>
                              <tr>
                                {clauseData.mechanical_properties.columns?.map((c: string, idx: number) => (
                                  <th key={idx}>{c}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {clauseData.mechanical_properties.rows?.map((row: any, idx: number) => (
                                <tr key={idx}>
                                  {Object.values(row).map((val: any, vIdx: number) => (
                                    <td key={vIdx} style={{ fontWeight: vIdx === 0 ? 600 : 400 }}>
                                      {val}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    {/* Chemical Table */}
                    {activeClauseTab === "chemical" && clauseData.chemical_composition && (
                      <div>
                        <div style={{ fontSize: 12, color: "#94a3b8", marginBottom: 6 }}>
                          Reference: <strong style={{ color: "#ffffff" }}>{clauseData.chemical_composition.clause}</strong> &bull; {clauseData.chemical_composition.table_title}
                        </div>
                        <div style={{ overflowX: "auto" }}>
                          <table className="clause-table">
                            <thead>
                              <tr>
                                {clauseData.chemical_composition.columns?.map((c: string, idx: number) => (
                                  <th key={idx}>{c}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {clauseData.chemical_composition.rows?.map((row: any, idx: number) => (
                                <tr key={idx}>
                                  {Object.values(row).map((val: any, vIdx: number) => (
                                    <td key={vIdx} style={{ fontWeight: vIdx === 0 ? 600 : 400 }}>
                                      {val}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                        {clauseData.chemical_composition.procurement_note && (
                          <p style={{ marginTop: 8, fontSize: 12, color: "#38bdf8", fontStyle: "italic" }}>
                            💡 {clauseData.chemical_composition.procurement_note}
                          </p>
                        )}
                      </div>
                    )}

                    {/* Testing Protocols */}
                    {activeClauseTab === "testing" && (
                      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                        {clauseData.testing_protocols?.map((tp: any, idx: number) => (
                          <div key={idx} style={{ background: "rgba(255, 255, 255, 0.03)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: 10, padding: "10px 14px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                            <div>
                              <div style={{ fontWeight: 600, color: "#ffffff", fontSize: 13 }}>{tp.test_name}</div>
                              <div style={{ fontSize: 12, color: "#94a3b8" }}>{tp.clause} &bull; Standard: <strong style={{ color: "#38bdf8" }}>{tp.reference_standard}</strong></div>
                            </div>
                            <div style={{ fontSize: 12, color: "#10b981", background: "rgba(16, 185, 129, 0.1)", padding: "4px 8px", borderRadius: 6 }}>
                              {tp.criteria}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Standard BOM (5-Tier Statutory Procurement Bundle) */}
                {recommendationResult.standard_bom && (
                  <div className="card-glass" style={{ borderLeft: "4px solid var(--accent-cyan)" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
                      <div>
                        <span className="badge badge-cyan" style={{ marginBottom: 4 }}>
                          <PackageCheck size={12} /> Autonomous 5-Tier Standard BOM (Bill of Standards)
                        </span>
                        <h3 style={{ fontSize: 16, fontWeight: 700, color: "#ffffff" }}>
                          Statutory Procurement Bundle & Quality Assurance Plan
                        </h3>
                      </div>
                      <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Rule 144(i) GFR 2017</span>
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                      <div style={{ padding: "10px 14px", background: "rgba(56, 189, 248, 0.06)", borderRadius: 8, border: "1px solid rgba(56, 189, 248, 0.15)" }}>
                        <div style={{ fontSize: 11, fontWeight: 700, color: "var(--accent-cyan)", textTransform: "uppercase" }}>Tier 1: Product Standard & Grade</div>
                        <div style={{ fontSize: 13, fontWeight: 600, color: "#ffffff", marginTop: 2 }}>
                          {recommendationResult.standard_bom.tier_1_product?.standard} &mdash; <span style={{ color: "#38bdf8" }}>{recommendationResult.standard_bom.tier_1_product?.recommended_grade}</span>
                        </div>
                      </div>

                      <div style={{ padding: "10px 14px", background: "rgba(16, 185, 129, 0.06)", borderRadius: 8, border: "1px solid rgba(16, 185, 129, 0.15)" }}>
                        <div style={{ fontSize: 11, fontWeight: 700, color: "#10b981", textTransform: "uppercase" }}>Tier 2: Governing Codes of Practice</div>
                        <div style={{ fontSize: 12, color: "#cbd5e1", marginTop: 4 }}>
                          {recommendationResult.standard_bom.tier_2_code_of_practice?.map((c: any, i: number) => (
                            <div key={i} style={{ marginBottom: 2 }}>&bull; <strong>{c.standard}</strong>: {c.role} ({c.clause})</div>
                          ))}
                        </div>
                      </div>

                      <div style={{ padding: "10px 14px", background: "rgba(139, 92, 246, 0.06)", borderRadius: 8, border: "1px solid rgba(139, 92, 246, 0.15)" }}>
                        <div style={{ fontSize: 11, fontWeight: 700, color: "#a78bfa", textTransform: "uppercase" }}>Tier 3: Mandatory Testing Protocols</div>
                        <div style={{ fontSize: 12, color: "#cbd5e1", marginTop: 4 }}>
                          {recommendationResult.standard_bom.tier_3_testing_protocols?.map((t: any, i: number) => (
                            <div key={i} style={{ marginBottom: 2 }}>&bull; <strong>{t.standard}</strong>: {t.test}</div>
                          ))}
                        </div>
                      </div>

                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                        <div style={{ padding: "10px 14px", background: "rgba(245, 158, 11, 0.06)", borderRadius: 8, border: "1px solid rgba(245, 158, 11, 0.15)" }}>
                          <div style={{ fontSize: 11, fontWeight: 700, color: "#fbbf24", textTransform: "uppercase" }}>Tier 4: Sampling & Frequency</div>
                          <div style={{ fontSize: 12, color: "#cbd5e1", marginTop: 2 }}><strong>{recommendationResult.standard_bom.tier_4_sampling_and_inspection?.standard}</strong>: {recommendationResult.standard_bom.tier_4_sampling_and_inspection?.batch_frequency}</div>
                        </div>

                        <div style={{ padding: "10px 14px", background: "rgba(236, 72, 153, 0.06)", borderRadius: 8, border: "1px solid rgba(236, 72, 153, 0.15)" }}>
                          <div style={{ fontSize: 11, fontWeight: 700, color: "#f472b6", textTransform: "uppercase" }}>Tier 5: Marking & Tagging</div>
                          <div style={{ fontSize: 12, color: "#cbd5e1", marginTop: 2 }}>{recommendationResult.standard_bom.tier_5_marking_and_delivery?.marking_requirement}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Multi-Tier Value Engineering Matrix */}
                {recommendationResult.value_engineering && recommendationResult.value_engineering.length > 0 && (
                  <div className="card-glass" style={{ borderLeft: "4px solid var(--accent-purple)" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
                      <div>
                        <span className="badge badge-purple" style={{ marginBottom: 4 }}>
                          <Sparkles size={12} /> Fit-for-Purpose Value Engineering Matrix
                        </span>
                        <h3 style={{ fontSize: 16, fontWeight: 700, color: "#ffffff" }}>
                          Grade & Lifecycle Cost Optimization
                        </h3>
                      </div>
                      <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Prevent Over/Under Specification</span>
                    </div>

                    <div style={{ overflowX: "auto" }}>
                      <table className="clause-table">
                        <thead>
                          <tr>
                            <th>Tier & Grade</th>
                            <th>Cost Index</th>
                            <th>Weight Saving / Eff.</th>
                            <th>Durability</th>
                            <th>Recommended Application</th>
                          </tr>
                        </thead>
                        <tbody>
                          {recommendationResult.value_engineering.map((tier: any, idx: number) => (
                            <tr key={idx} style={{ background: tier.tier.includes("RECOMMENDED") ? "rgba(16, 185, 129, 0.08)" : undefined }}>
                              <td>
                                <div style={{ fontWeight: 700, color: tier.tier.includes("RECOMMENDED") ? "#10b981" : "#ffffff" }}>{tier.grade}</div>
                                <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{tier.tier}</div>
                              </td>
                              <td><span className="badge badge-blue">{tier.initial_cost_index}</span></td>
                              <td>{tier.structural_weight_saving}</td>
                              <td>{tier.lifecycle_durability}</td>
                              <td style={{ fontSize: 12, maxWidth: 220 }}>{tier.recommended_for}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Statutory QCO Mandate Card */}
                {recommendationResult.governing_qco && (
                  <div className="card-glass" style={{ borderLeft: "4px solid var(--accent-gold)" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                      <span className="badge badge-gold">
                        <Scale size={12} /> Statutory Quality Control Order (Section 16 BIS Act)
                      </span>
                      <span className="badge badge-gold">
                        {recommendationResult.governing_qco.mandatory_scheme || "Scheme-I"}
                      </span>
                    </div>

                    <h3 style={{ fontSize: 16, fontWeight: 700, color: "#ffffff", marginBottom: 6 }}>
                      {recommendationResult.governing_qco.order_name}
                    </h3>
                    <p style={{ fontSize: 13, color: "#94a3b8", marginBottom: 12 }}>
                      Issuing Authority: <strong style={{ color: "#ffffff" }}>{recommendationResult.governing_qco.ministry_id || recommendationResult.governing_qco.ministry}</strong>
                    </p>

                    <div style={{ background: "rgba(245, 158, 11, 0.08)", border: "1px solid rgba(245, 158, 11, 0.2)", borderRadius: 10, padding: "10px 14px", fontSize: 12, color: "#fbbf24", lineHeight: 1.4 }}>
                      <strong>Statutory Penal Warning:</strong> Supply without valid BIS Certification Mark constitutes a cognizable offense punishable under Section 29 of the Bureau of Indian Standards Act, 2016.
                    </div>
                  </div>
                )}

                {/* Ready-to-Paste Tender Clause */}
                <div className="card-glass">
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
                    <span className="badge badge-cyan">
                      <FileCheck2 size={12} /> Ready-to-Paste GeM / CPWD Tender Clause
                    </span>
                    <div style={{ display: "flex", gap: 10 }}>
                      <button
                        className="copy-btn"
                        onClick={() => playSpeechAudio(recommendationResult.synthesis?.tender_clause, "en-IN")}
                        style={{ color: "#38bdf8" }}
                      >
                        <Volume2 size={14} /> Voice-Back
                      </button>
                      <button
                        className="copy-btn"
                        onClick={() => copyToClipboard(recommendationResult.synthesis?.tender_clause, "clause")}
                      >
                        {copiedClause ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
                        {copiedClause ? "Copied to Clipboard!" : "Copy Tender Clause"}
                      </button>
                    </div>
                  </div>

                  {recommendationResult.litigation_risk && (
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                      <span className={`badge badge-${recommendationResult.litigation_risk.badge_color || "emerald"}`}>
                        <ShieldCheck size={12} /> Legal Defensibility Score: {recommendationResult.litigation_risk.defensibility_score}/100 ({recommendationResult.litigation_risk.risk_rating})
                      </span>
                    </div>
                  )}

                  <div className="legal-clause-box">
                    {recommendationResult.synthesis?.tender_clause}
                  </div>
                </div>
              </div>

              {/* Right Column: Knowledge Graph Canvas & Alternative Standards */}
              <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
                {/* 2-Hop Graph Canvas */}
                <div className="card-glass">
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
                    <h3 style={{ fontSize: 15, fontWeight: 700, color: "#ffffff", display: "flex", alignItems: "center", gap: 8 }}>
                      <GitFork size={16} color="var(--accent-cyan)" /> Standards Knowledge Graph Topology
                    </h3>
                    <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                      2-Hop Traversal ({recommendationResult.graph_visualization?.total_nodes || 0} Nodes)
                    </span>
                  </div>

                  <GraphCanvas
                    data={recommendationResult.graph_visualization || { nodes: [], links: [] }}
                    height={380}
                  />
                </div>

                {/* Candidate Standards List */}
                <div className="card-glass">
                  <h3 style={{ fontSize: 15, fontWeight: 700, color: "#ffffff", marginBottom: 14 }}>
                    Alternative & Related Standards
                  </h3>
                  <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                    {recommendationResult.candidate_standards?.map((cand: any, idx: number) => (
                      <div
                        key={idx}
                        style={{
                          background: "rgba(255, 255, 255, 0.02)",
                          border: "1px solid rgba(255, 255, 255, 0.06)",
                          borderRadius: 10,
                          padding: "10px 14px",
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          cursor: "pointer",
                          transition: "all 0.2s ease"
                        }}
                        onClick={() => handleSearch(cand.is_number)}
                      >
                        <div>
                          <div style={{ fontWeight: 600, fontSize: 13, color: "#ffffff" }}>
                            {cand.is_number}
                          </div>
                          <div style={{ fontSize: 12, color: "#94a3b8" }}>
                            {cand.title?.length > 45 ? cand.title.slice(0, 45) + "..." : cand.title}
                          </div>
                        </div>
                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                          {cand.is_mandatory_qco && (
                            <span className="badge badge-gold" style={{ fontSize: 9 }}>QCO</span>
                          )}
                          <ChevronRight size={16} color="#64748b" />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODE B: TENDER SPECIFICATION AUDITOR */}
      {/* ========================================================================= */}
      {activeTab === "auditor" && (
        <div>
          {/* Sample Scenarios Bar */}
          <div className="card-glass" style={{ marginBottom: 24 }}>
            <span className="chip-label" style={{ display: "block", marginBottom: 12 }}>
              1-Click Gold Standard Tender Samples (with Compliance Traps):
            </span>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              {sampleScenarios?.mode_b_audit_tender_traps?.map((sample: any, idx: number) => (
                <button
                  key={idx}
                  className="chip-btn"
                  style={{
                    borderColor: sample.qco_compliant ? "rgba(16, 185, 129, 0.3)" : "rgba(244, 63, 94, 0.4)",
                    color: sample.qco_compliant ? "#34d399" : "#fb7185"
                  }}
                  onClick={() => {
                    setTenderText(sample.raw_text);
                    handleAudit(sample.raw_text);
                  }}
                >
                  {sample.qco_compliant ? "✓ " : "⚠ "}
                  {sample.title?.split("(")[0]}
                </button>
              ))}
            </div>
          </div>

          {/* Dimension 1: Tender Ingestion (File Dropzone & Text Area) */}
          <div className="card-glass" style={{ marginBottom: 28 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: "#ffffff" }}>
                Input Tender Specification / Notice Inviting Tender (NIT)
              </h3>

              {/* Upload PDF/DOCX Button */}
              <div>
                <input
                  type="file"
                  ref={fileInputRef}
                  style={{ display: "none" }}
                  accept=".pdf,.txt,.docx"
                  onChange={handleFileUpload}
                />
                <button
                  className="copy-btn"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isUploadingFile}
                  style={{ background: "rgba(0, 242, 254, 0.15)", color: "#00f2fe", borderColor: "rgba(0, 242, 254, 0.3)" }}
                >
                  {isUploadingFile ? <RefreshCw className="animate-spin" size={14} /> : <UploadCloud size={14} />}
                  {isUploadingFile ? "Parsing PDF/Document..." : "Upload Tender File (.pdf / .txt)"}
                </button>
              </div>
            </div>

            <textarea
              style={{
                width: "100%",
                height: 150,
                background: "rgba(11, 17, 31, 0.9)",
                border: "1px solid rgba(255, 255, 255, 0.12)",
                borderRadius: 14,
                padding: 16,
                color: "#e2e8f0",
                fontSize: 13,
                fontFamily: "var(--font-mono)",
                outline: "none",
                marginBottom: 16
              }}
              placeholder="Paste raw tender specifications, clauses, or material requirements here, or click 'Upload Tender File' above..."
              value={tenderText}
              onChange={e => setTenderText(e.target.value)}
            />

            <button
              className="search-btn"
              style={{ position: "static", width: "100%", justifyContent: "center" }}
              onClick={() => handleAudit()}
              disabled={isAuditing}
            >
              {isAuditing ? <RefreshCw className="animate-spin" size={16} /> : <ShieldAlert size={16} />}
              Execute GovTech Compliance Audit & Generate Redline Matrix
            </button>
          </div>

          {/* Audit Results with 3 Sub-tabs */}
          {auditResult && (
            <div>
              {/* Score Gauge Card */}
              <div
                className="card-glass score-card"
                style={{
                  background:
                    auditResult.status_color === "green"
                      ? "rgba(16, 185, 129, 0.05)"
                      : auditResult.status_color === "yellow"
                      ? "rgba(245, 158, 11, 0.05)"
                      : "rgba(244, 63, 94, 0.08)",
                  border: `1px solid ${
                    auditResult.status_color === "green"
                      ? "rgba(16, 185, 129, 0.3)"
                      : auditResult.status_color === "yellow"
                      ? "rgba(245, 158, 11, 0.3)"
                      : "rgba(244, 63, 94, 0.4)"
                  }`,
                  marginBottom: 20
                }}
              >
                <div className={`score-circle ${auditResult.status_color}`}>
                  {auditResult.compliance_score}
                  <small>/100</small>
                </div>

                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 8 }}>
                    <span
                      className={`badge ${
                        auditResult.status_color === "green"
                          ? "badge-emerald"
                          : auditResult.status_color === "yellow"
                          ? "badge-gold"
                          : "badge-rose"
                      }`}
                    >
                      {auditResult.compliance_status}
                    </span>
                    {auditResult.qco_compliant ? (
                      <span className="badge badge-emerald">✓ Statutory QCO Compliant</span>
                    ) : (
                      <span className="badge badge-rose">⚠ Statutory QCO Violation</span>
                    )}
                    {auditResult.is_indic && (
                      <span className="badge badge-cyan">Indic Language: {auditResult.detected_language}</span>
                    )}
                  </div>

                  <h2 style={{ fontSize: 20, fontWeight: 700, color: "#ffffff", marginBottom: 6 }}>
                    {auditResult.tender_title}
                  </h2>
                  <p style={{ fontSize: 13, color: "#94a3b8" }}>
                    Standards Detected: <strong style={{ color: "#ffffff" }}>{auditResult.standards_referenced?.join(", ") || "None"}</strong> | Discovered Compliance Findings: <strong style={{ color: "#ffffff" }}>{auditResult.total_findings}</strong>
                  </p>
                </div>
              </div>

              {/* Sub-tabs Navigation */}
              <div style={{ display: "flex", gap: 10, marginBottom: 20 }}>
                <button
                  className={`tab-btn ${activeAuditorSubtab === "findings" ? "active" : ""}`}
                  onClick={() => setActiveAuditorSubtab("findings")}
                >
                  <ShieldAlert size={14} /> Compliance Audit Findings ({auditResult.total_findings})
                </button>
                <button
                  className={`tab-btn ${activeAuditorSubtab === "diff" ? "active" : ""}`}
                  onClick={() => setActiveAuditorSubtab("diff")}
                >
                  <FileText size={14} /> Side-by-Side Visual Redline Diff
                </button>
                <button
                  className={`tab-btn ${activeAuditorSubtab === "corrigendum" ? "active" : ""}`}
                  onClick={() => setActiveAuditorSubtab("corrigendum")}
                >
                  <Printer size={14} /> Official Gazette Corrigendum Notice
                </button>
              </div>

              {/* Subtab 1: Findings Table */}
              {activeAuditorSubtab === "findings" && (
                <div className="card-glass" style={{ marginBottom: 28 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 700, color: "#ffffff", marginBottom: 8 }}>
                    Discovered Issues & Redline Amendment Matrix
                  </h3>
                  <p style={{ fontSize: 13, color: "#94a3b8", marginBottom: 16 }}>
                    Itemized violations of Section 16/29 BIS Act 2016, mandatory Quality Control Orders, and Clause 2 testing protocols.
                  </p>

                  {auditResult.findings?.length === 0 ? (
                    <div style={{ padding: 24, textAlign: "center", color: "#10b981", fontSize: 14 }}>
                      ✓ No compliance violations or obsolete standards detected in this specification.
                    </div>
                  ) : (
                    <table className="findings-table">
                      <thead>
                        <tr>
                          <th>Severity</th>
                          <th>Issue Type</th>
                          <th>Existing Tender Snippet</th>
                          <th>Recommended Redline Amendment</th>
                          <th>Regulatory Basis</th>
                        </tr>
                      </thead>
                      <tbody>
                        {auditResult.findings?.map((f: any, idx: number) => (
                          <tr key={idx}>
                            <td>
                              <span
                                className={`badge ${
                                  f.severity === "CRITICAL"
                                    ? "badge-rose"
                                    : f.severity === "MAJOR"
                                    ? "badge-gold"
                                    : "badge-cyan"
                                }`}
                              >
                                {f.severity}
                              </span>
                            </td>
                            <td style={{ fontWeight: 600, color: "#ffffff", fontFamily: "var(--font-mono)", fontSize: 12 }}>
                              {f.issue_type}
                            </td>
                            <td style={{ color: "#fca5a5", fontStyle: "italic" }}>
                              &ldquo;{f.original_text_snippet}&rdquo;
                            </td>
                            <td style={{ color: "#86efac", fontWeight: 500 }}>
                              {f.recommended_amendment}
                            </td>
                            <td style={{ color: "#94a3b8", fontSize: 12 }}>
                              {f.regulatory_reference}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              )}

              {/* Subtab 2: Dimension 1 Visual Redline Diff Viewer */}
              {activeAuditorSubtab === "diff" && (
                <div className="card-glass" style={{ marginBottom: 28 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                    <div>
                      <h3 style={{ fontSize: 16, fontWeight: 700, color: "#ffffff" }}>
                        Interactive Side-by-Side Visual Redline Diff
                      </h3>
                      <p style={{ fontSize: 13, color: "#94a3b8" }}>
                        Direct side-by-side comparison of original tender text vs recommended regulatory amendments.
                      </p>
                    </div>
                  </div>

                  <div className="redline-diff-container">
                    {/* Left Pane: Original with Strikethroughs */}
                    <div className="diff-pane" style={{ borderLeft: "3px solid #ef4444" }}>
                      <div style={{ fontWeight: 700, color: "#f87171", marginBottom: 10, display: "flex", alignItems: "center", gap: 6 }}>
                        <span>ORIGINAL TENDER SPECIFICATION (WITH FLAGS)</span>
                      </div>
                      <div style={{ color: "#cbd5e1", whiteSpace: "pre-wrap" }}>
                        {auditResult.findings?.map((f: any, idx: number) => (
                          <div key={idx} style={{ marginBottom: 12, paddingBottom: 8, borderBottom: "1px dashed rgba(255,255,255,0.06)" }}>
                            <span className="diff-strike">{f.original_text_snippet}</span>
                            <div style={{ fontSize: 11, color: "#f87171", marginTop: 4 }}>
                              ↳ Reason: {f.issue_type} ({f.severity})
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Right Pane: Amended text with Green Insertions */}
                    <div className="diff-pane" style={{ borderLeft: "3px solid #10b981" }}>
                      <div style={{ fontWeight: 700, color: "#34d399", marginBottom: 10, display: "flex", alignItems: "center", gap: 6 }}>
                        <span>AMENDED & QCO-COMPLIANT PROVISION</span>
                      </div>
                      <div style={{ color: "#cbd5e1", whiteSpace: "pre-wrap" }}>
                        {auditResult.findings?.map((f: any, idx: number) => (
                          <div key={idx} style={{ marginBottom: 12, paddingBottom: 8, borderBottom: "1px dashed rgba(255,255,255,0.06)" }}>
                            <span className="diff-insert">+ {f.recommended_amendment}</span>
                            <div style={{ fontSize: 11, color: "#6ee7b7", marginTop: 4 }}>
                              ↳ Enforcing Rule: {f.regulatory_reference}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Subtab 3: Dimension 1 Official Gazette Corrigendum Notice (Printable) */}
              {activeAuditorSubtab === "corrigendum" && (
                <div style={{ marginBottom: 28 }}>
                  <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginBottom: 14 }}>
                    <button
                      className="copy-btn"
                      onClick={() => copyToClipboard(auditResult.official_corrigendum?.formatted_text || auditResult.corrigendum_notice, "corrigendum")}
                    >
                      {copiedCorrigendum ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
                      {copiedCorrigendum ? "Copied Corrigendum!" : "Copy Corrigendum Text"}
                    </button>
                    <button
                      className="search-btn"
                      style={{ position: "static", background: "linear-gradient(135deg, #10b981 0%, #059669 100%)" }}
                      onClick={triggerPrintCorrigendum}
                    >
                      <Printer size={16} /> 1-Click Print / Save PDF
                    </button>
                  </div>

                  {/* Gazette Styled Document */}
                  <div className="corrigendum-paper">
                    <div className="corrigendum-header">
                      <div style={{ fontSize: 18, fontWeight: 700, letterSpacing: 1 }}>GOVERNMENT OF INDIA</div>
                      <div style={{ fontSize: 14, fontWeight: 600, color: "#334155" }}>CENTRAL PUBLIC WORKS & PROCUREMENT DIRECTORATE</div>
                      <div style={{ fontSize: 16, fontWeight: 700, marginTop: 8, textDecoration: "underline" }}>OFFICIAL CORRIGENDUM & ADDENDUM NOTICE</div>
                      <div style={{ fontSize: 12, marginTop: 6, color: "#64748b" }}>
                        Corrigendum No: <strong>{auditResult.official_corrigendum?.corrigendum_no || "CORR/BIS/2026/01"}</strong> &bull; Date: {auditResult.official_corrigendum?.issuing_date || "Current"}
                      </div>
                    </div>

                    <div style={{ fontSize: 13, marginBottom: 16 }}>
                      <div>Tender / GeM Bid Reference: <strong>{auditResult.tender_id || "GEM/2026/B/DEFAULT"}</strong></div>
                      <div>Department / Issuing Authority: <strong>{auditResult.department || "Public Procurement Entity"}</strong></div>
                      <div>Work Nomenclature: <strong>{auditResult.tender_title}</strong></div>
                    </div>

                    <p style={{ fontSize: 13, textAlign: "justify", marginBottom: 14 }}>
                      In exercise of the powers conferred by Rule 144(i) of General Financial Rules (GFR), 2017 and mandatory Quality Control Orders promulgated under Section 16 of the Bureau of Indian Standards Act, 2016, the Competent Authority hereby notifies the following technical amendments to the bidding documents:
                    </p>

                    <table className="corrigendum-table">
                      <thead>
                        <tr>
                          <th style={{ width: "8%" }}>Item</th>
                          <th style={{ width: "22%" }}>Clause Reference</th>
                          <th style={{ width: "35%" }}>Existing Provision</th>
                          <th style={{ width: "35%" }}>Amended Provision (Read As)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {auditResult.official_corrigendum?.amendment_rows?.map((row: any, idx: number) => (
                          <tr key={idx}>
                            <td style={{ textAlign: "center", fontWeight: 700 }}>{row.sl_no}</td>
                            <td style={{ fontWeight: 600 }}>{row.clause_ref}</td>
                            <td style={{ color: "#991b1b" }}>{row.existing_provision}</td>
                            <td style={{ color: "#065f46", fontWeight: 600 }}>{row.amended_provision}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>

                    <div style={{ background: "#fef3c7", border: "1px solid #f59e0b", padding: "12px 16px", borderRadius: 8, fontSize: 12, color: "#92400e", marginBottom: 20 }}>
                      <strong>Statutory Penal Notice under Section 29, BIS Act, 2016:</strong> Any contractor, vendor or supplier found executing work or delivering materials without valid BIS Standard Mark (ISI mark / CRS) under notified QCOs shall be liable to criminal prosecution with imprisonment up to 2 years and minimum fine of ₹2,00,000.
                    </div>

                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginTop: 30, fontSize: 13 }}>
                      <div>
                        <div>Verified & Stamped by: <strong>Manak-SpecEngine GovTech AI</strong></div>
                        <div style={{ fontSize: 11, color: "#64748b" }}>Digital Audit Hash: SHA256-BIS-2026-COMPLIANT</div>
                      </div>
                      <div style={{ textAlign: "right" }}>
                        <div style={{ borderBottom: "1px solid #000", width: 200, marginBottom: 4 }}></div>
                        <div style={{ fontWeight: 700 }}>AUTHORIZED TENDER OFFICER</div>
                        <div style={{ fontSize: 11, color: "#475569" }}>Procurement Evaluation Committee</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Connected Subgraph */}
              {auditResult.graph_visualization?.nodes?.length > 0 && (
                <div className="card-glass">
                  <h3 style={{ fontSize: 15, fontWeight: 700, color: "#ffffff", marginBottom: 14 }}>
                    Audited Standards Connected Subgraph
                  </h3>
                  <GraphCanvas data={auditResult.graph_visualization} height={360} />
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODE C: STATUTORY QCO REGISTRY */}
      {/* ========================================================================= */}
      {activeTab === "qcos" && (
        <div>
          <div className="card-glass" style={{ marginBottom: 24, display: "flex", gap: 16, alignItems: "center" }}>
            <input
              type="text"
              className="search-input"
              style={{ padding: "12px 18px", fontSize: 14 }}
              placeholder="Search Quality Control Orders by product or gazette notification..."
              value={qcoSearchTerm}
              onChange={e => setQcoSearchTerm(e.target.value)}
            />
            <select
              style={{
                background: "rgba(11, 17, 31, 0.9)",
                border: "1px solid rgba(255, 255, 255, 0.12)",
                borderRadius: 12,
                color: "#ffffff",
                padding: "12px 18px",
                fontFamily: "var(--font-main)",
                outline: "none"
              }}
              value={qcoFilterMinistry}
              onChange={e => setQcoFilterMinistry(e.target.value)}
            >
              <option value="All">All Ministries</option>
              <option value="Steel">Ministry of Steel</option>
              <option value="Electronics">MeitY (Electronics & IT)</option>
              <option value="DPIIT">DPIIT (Commerce & Industry)</option>
              <option value="Renewable">MNRE (Solar & Renewable)</option>
              <option value="Chemicals">Chemicals & Petrochemicals</option>
            </select>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(380px, 1fr))", gap: 20 }}>
            {filteredQcos.map((qco, idx) => (
              <div key={idx} className="card-glass" style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
                    <span className="badge badge-gold">{qco.mandatory_scheme || "Scheme-I"}</span>
                    {qco.gazette_no && (
                      <span style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                        {qco.gazette_no}
                      </span>
                    )}
                  </div>
                  <h4 style={{ fontSize: 15, fontWeight: 700, color: "#ffffff", marginBottom: 6 }}>
                    {qco.order_name}
                  </h4>
                  <p style={{ fontSize: 12, color: "var(--accent-cyan)", marginBottom: 10 }}>
                    {qco.ministry_id || qco.ministry}
                  </p>
                  <p style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.4, marginBottom: 12 }}>
                    {qco.penal_clause ? qco.penal_clause.slice(0, 140) + "..." : "Mandatory conformity to BIS mark."}
                  </p>
                </div>

                <div style={{ fontSize: 11, color: "var(--text-muted)", borderTop: "1px solid rgba(255,255,255,0.05)", paddingTop: 10 }}>
                  Effective Date: <strong style={{ color: "#ffffff" }}>{qco.effective_date || "Active in Force"}</strong>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODE D: KNOWLEDGE GRAPH EXPLORER */}
      {/* ========================================================================= */}
      {activeTab === "graph" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          {/* Top Search & Filter Bar */}
          <div className="card-glass" style={{ display: "flex", gap: 16, alignItems: "center" }}>
            <input
              type="text"
              className="search-input"
              style={{ padding: "12px 18px", fontSize: 14 }}
              placeholder="Search standard identifier (e.g. IS 2062, IS 1786, IS 456, IS 13252)..."
              value={graphQuery}
              onChange={e => setGraphQuery(e.target.value)}
              onKeyDown={e => e.key === "Enter" && { loadGraphNeighborhood: loadGraphNeighborhood(graphQuery), loadTimeline: loadTimeline(graphQuery) }}
            />
            <button
              className="search-btn"
              style={{ position: "static" }}
              onClick={() => {
                loadGraphNeighborhood(graphQuery);
                loadTimeline(graphQuery);
              }}
            >
              Explore Graph
            </button>
          </div>

          {/* Dimension 4: Temporal Version Evolution Timeline Slider */}
          {timelineData && (
            <div className="card-glass" style={{ borderLeft: "4px solid var(--accent-blue)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                <div>
                  <span className="badge badge-cyan" style={{ marginBottom: 4 }}>
                    <History size={12} /> Temporal Evolution & Historical Revision Timeline
                  </span>
                  <h3 style={{ fontSize: 16, fontWeight: 700, color: "#ffffff" }}>
                    Chronological Evolution of {timelineData.standard_id}
                  </h3>
                </div>
                <span style={{ fontSize: 12, color: "#94a3b8" }}>
                  {timelineData.total_milestones} Historical Revisions & Gazette Orders
                </span>
              </div>

              {/* Timeline Track Slider */}
              <div className="timeline-track">
                {timelineData.milestones?.map((m: any, idx: number) => (
                  <div
                    key={idx}
                    className={`timeline-step ${activeTimelineIndex === idx ? "active" : ""}`}
                    onClick={() => setActiveTimelineIndex(idx)}
                  >
                    <div style={{ fontSize: 16, fontWeight: 700, color: activeTimelineIndex === idx ? "#00f2fe" : "#ffffff" }}>
                      {m.year}
                    </div>
                    <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 2 }}>
                      {m.revision}
                    </div>
                  </div>
                ))}
              </div>

              {/* Selected Milestone Detail */}
              {timelineData.milestones?.[activeTimelineIndex] && (
                <div style={{ background: "rgba(11, 17, 31, 0.8)", border: "1px solid rgba(0, 242, 254, 0.25)", borderRadius: 12, padding: "14px 18px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                    <div style={{ fontSize: 14, fontWeight: 700, color: "#00f2fe" }}>
                      Year {timelineData.milestones[activeTimelineIndex].year}: {timelineData.milestones[activeTimelineIndex].revision}
                    </div>
                    {activeTimelineIndex === timelineData.milestones.length - 1 && (
                      <span className="badge badge-emerald">Current Active Gazette Revision</span>
                    )}
                  </div>
                  <p style={{ fontSize: 13, color: "#e2e8f0", lineHeight: 1.5 }}>
                    {timelineData.milestones[activeTimelineIndex].event}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Dimension 4: Shortest Normative Reference Path Finder */}
          <div className="card-glass" style={{ borderLeft: "4px solid var(--accent-purple)" }}>
            <div style={{ marginBottom: 14 }}>
              <span className="badge" style={{ background: "rgba(168, 85, 247, 0.15)", color: "#c084fc", border: "1px solid rgba(168, 85, 247, 0.3)", marginBottom: 4 }}>
                <GitFork size={12} /> Normative Reference Path Finder
              </span>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: "#ffffff" }}>
                Trace Shortest Regulatory Dependency Bridge Between Two Standards
              </h3>
            </div>

            <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 14, flexWrap: "wrap" }}>
              <input
                type="text"
                className="search-input"
                style={{ flex: 1, padding: "10px 14px", fontSize: 13 }}
                placeholder="Source Standard (e.g. IS 456)"
                value={pathSource}
                onChange={e => setPathSource(e.target.value)}
              />
              <span style={{ color: "#94a3b8", fontWeight: 700 }}>➔</span>
              <input
                type="text"
                className="search-input"
                style={{ flex: 1, padding: "10px 14px", fontSize: 13 }}
                placeholder="Target Standard (e.g. IS 1786)"
                value={pathTarget}
                onChange={e => setPathTarget(e.target.value)}
              />
              <button
                className="search-btn"
                style={{ position: "static" }}
                onClick={findShortestNormativePath}
                disabled={isFindingPath}
              >
                {isFindingPath ? <RefreshCw className="animate-spin" size={14} /> : <Sparkles size={14} />}
                Trace Bridge
              </button>
            </div>

            {/* Path Result */}
            {pathResult && (
              <div style={{ background: "rgba(11, 17, 31, 0.85)", border: "1px solid rgba(168, 85, 247, 0.3)", borderRadius: 12, padding: "14px 18px" }}>
                {pathResult.connected ? (
                  <div>
                    <div style={{ fontSize: 13, color: "#c084fc", fontWeight: 600, marginBottom: 10 }}>
                      ✓ Shortest Normative Path ({pathResult.path_length} Hops):
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
                      {pathResult.steps?.map((step: any, idx: number) => (
                        <React.Fragment key={idx}>
                          <div style={{ background: "rgba(168, 85, 247, 0.2)", border: "1px solid rgba(168, 85, 247, 0.4)", borderRadius: 8, padding: "6px 12px", textAlign: "center" }}>
                            <div style={{ fontWeight: 700, color: "#ffffff", fontSize: 13 }}>{step.label}</div>
                            {step.title && <div style={{ fontSize: 10, color: "#94a3b8", maxWidth: 160 }}>{step.title.slice(0, 30)}...</div>}
                          </div>
                          {idx < pathResult.steps.length - 1 && (
                            <span style={{ fontSize: 12, color: "#00f2fe", fontWeight: 600 }}>
                              --[{pathResult.steps[idx + 1].relationship}]--➔
                            </span>
                          )}
                        </React.Fragment>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div style={{ color: "#fca5a5", fontSize: 13 }}>
                    {pathResult.message}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Interactive Topological Graph */}
          <div className="card-glass">
            <h3 style={{ fontSize: 16, fontWeight: 700, color: "#ffffff", marginBottom: 14 }}>
              Interactive 2-Hop Topological Graph ({graphData?.total_nodes || 0} Nodes, {graphData?.total_links || 0} Relationships)
            </h3>
            {graphData && <GraphCanvas data={graphData} height={520} />}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* DIMENSION 3: BIS CM/L LICENSE VERIFICATION MODAL                          */}
      {/* ========================================================================= */}
      {showCmlModal && (
        <div style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: "rgba(0, 0, 0, 0.75)",
          backdropFilter: "blur(8px)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 9999,
          padding: 20
        }}>
          <div className="card-glass" style={{
            maxWidth: 620,
            width: "100%",
            background: "#0d1424",
            border: "1px solid var(--border-accent)",
            boxShadow: "0 0 40px rgba(0, 242, 254, 0.25)"
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <ShieldCheck size={22} color="#10b981" />
                <h3 style={{ fontSize: 18, fontWeight: 700, color: "#ffffff" }}>
                  BIS Certification Marks License (CM/L) Verifier
                </h3>
              </div>
              <button
                onClick={() => setShowCmlModal(false)}
                style={{ background: "transparent", border: "none", color: "#94a3b8", cursor: "pointer" }}
              >
                <X size={20} />
              </button>
            </div>

            <p style={{ fontSize: 13, color: "#94a3b8", marginBottom: 16 }}>
              Verify manufacturer validity under Section 16 & 29 of the Bureau of Indian Standards Act, 2016.
            </p>

            {/* Input & Quick Chips */}
            <div style={{ display: "flex", gap: 10, marginBottom: 12 }}>
              <input
                type="text"
                className="search-input"
                style={{ padding: "10px 14px", fontSize: 14 }}
                placeholder="Enter 7-digit BIS License Number (e.g. 8400124)..."
                value={cmlInput}
                onChange={e => setCmlInput(e.target.value)}
                onKeyDown={e => e.key === "Enter" && verifyCmlNumber()}
              />
              <button
                className="search-btn"
                style={{ position: "static" }}
                onClick={() => verifyCmlNumber()}
                disabled={isVerifyingCml}
              >
                {isVerifyingCml ? <RefreshCw className="animate-spin" size={14} /> : <CheckCircle2 size={14} />}
                Verify
              </button>
            </div>

            <div style={{ display: "flex", gap: 8, marginBottom: 18, flexWrap: "wrap", fontSize: 11 }}>
              <span style={{ color: "#64748b" }}>Quick Verify:</span>
              <button className="chip-btn" onClick={() => { setCmlInput("8400124"); verifyCmlNumber("8400124"); }}>Tata Steel (8400124)</button>
              <button className="chip-btn" onClick={() => { setCmlInput("7821940"); verifyCmlNumber("7821940"); }}>SAIL Bhilai (7821940)</button>
              <button className="chip-btn" onClick={() => { setCmlInput("9123456"); verifyCmlNumber("9123456"); }}>Supreme Pipes (9123456)</button>
              <button className="chip-btn" onClick={() => { setCmlInput("2718281"); verifyCmlNumber("2718281"); }}>Karam Safety (2718281)</button>
            </div>

            {/* CML Verification Result Card */}
            {cmlResult && (
              <div style={{
                background: cmlResult.verified ? "rgba(16, 185, 129, 0.08)" : "rgba(239, 68, 68, 0.08)",
                border: `1px solid ${cmlResult.verified ? "rgba(16, 185, 129, 0.3)" : "rgba(239, 68, 68, 0.3)"}`,
                borderRadius: 12,
                padding: 16
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                  <span className={`badge ${cmlResult.verified ? "badge-emerald" : "badge-rose"}`} style={{ fontSize: 11, fontWeight: 700 }}>
                    {cmlResult.status}
                  </span>
                  <span style={{ fontSize: 12, color: "#94a3b8", fontFamily: "var(--font-mono)" }}>
                    {cmlResult.cml_number}
                  </span>
                </div>

                <h4 style={{ fontSize: 15, fontWeight: 700, color: "#ffffff", marginBottom: 6 }}>
                  {cmlResult.licensee_name}
                </h4>
                <p style={{ fontSize: 12, color: "#94a3b8", marginBottom: 10 }}>
                  Factory: {cmlResult.factory_address}
                </p>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, fontSize: 12, color: "#cbd5e1", borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: 10 }}>
                  <div>Endorsed Standard: <strong style={{ color: "#38bdf8" }}>{cmlResult.standard_number}</strong></div>
                  <div>Scheme: <strong style={{ color: "#f59e0b" }}>{cmlResult.scheme}</strong></div>
                  <div>Validity: <strong style={{ color: "#10b981" }}>Until {cmlResult.valid_upto}</strong></div>
                  <div>Surveillance: <strong style={{ color: "#ffffff" }}>{cmlResult.lab_test_status}</strong></div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
