# Manak-SpecEngine (मानक-इंजन)

> **Enterprise GovTech AI Recommendation & Compliance Verification Engine for Bureau of Indian Standards (BIS)**  
> Anchored in the Bureau of Indian Standards Act, 2016, General Financial Rules (GFR), 2017, and Statutory Quality Control Orders (QCOs).

[![Pytest Tests](https://img.shields.io/badge/Pytest-168%20Passed%20(100%25)-emerald?style=flat-square&logo=pytest)](file:///Users/rudrarajsingh/Desktop/antigravity/tests)
[![Next.js 16](https://img.shields.io/badge/Frontend-Next.js%2016%20Turbopack-blue?style=flat-square&logo=next.js)](file:///Users/rudrarajsingh/Desktop/antigravity/frontend)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20Python%203.11+-009688?style=flat-square&logo=fastapi)](file:///Users/rudrarajsingh/Desktop/antigravity/backend)
[![Sarvam AI](https://img.shields.io/badge/Multilingual%20Voice-Sarvam%20AI%20(10%2B%20Indic%20Languages)-orange?style=flat-square)](https://sarvam.ai)

---

## 🏛️ Executive Overview

**Manak-SpecEngine** is an AI-powered recommendation, compliance verification, and tender auditing platform designed for Indian public procurement entities (CPWD, GeM, Railways, NHAI, State PWDs, and Defence). 

It bridges the critical gap between unstructured procurement notices and statutory Indian Standards (BIS) by:
1. **Recommending Authoritative Indian Standards** grounded in physical engineering constraints (Exposure class, seismic zone, pressure class).
2. **Generating 5-Tier Standard BOMs (Bill of Standards)** to ensure tenders cite companion design codes, testing protocols, and lot sampling plans.
3. **Auditing Tenders for Legal & Statutory Traps** (detecting anti-competitive blast furnace restrictions, unqualified foreign standards under PPP-MII, and obsolete revisions).
4. **Providing Multilingual Regional Speech-to-Text & Text-to-Speech** via Sarvam AI across 10+ Indian languages.
5. **Verifying Live BIS Certification Marks Licenses (CM/L)** with authentic manufacturer registry data and checksum validation.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      Next.js 16 Web Dashboard (Port 3000)                       │
│  - Mode A: Smart Standard Finder + Clause Engineering Tables + Standard BOM     │
│  - Mode B: Tender Specification Auditor + File Upload (.pdf, .docx, .txt)       │
│            + Side-by-Side Visual Redline Diff Viewer                            │
│            + Official Gazette Corrigendum Notice (1-Click window.print())       │
│  - Mode C: Statutory QCO & CRS Registry (192 Orders across 30+ Ministries)     │
│  - Mode D: Interactive Knowledge Graph (Revision Timeline & Shortest Path)      │
│  - Top Nav: Live BIS CM/L License Verifier Modal + Daylight Theme Toggle        │
│  - Multilingual: Sarvam AI Voice-In & Voice-Back (bulbul:v3 Audio Playback)     │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ JSON HTTP REST API
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           FastAPI Backend (Port 8000)                           │
│  1. ConstraintSlotService: Extracts Environmental Exposure & Seismic Zones      │
│  2. HybridRetriever: BM25 + Sublinear TF-IDF + RRF (k=60) + QCO Boost           │
│  3. DomainReranker: Contrastive grade matching & hard-negative discrimination   │
│  4. StandardBOMService: Assembles 5-Tier Statutory Procurement Bundles          │
│  5. ScheduleOfRatesService: Grounds queries in CPWD DSR, MoRTH & GeM params     │
│  6. DisambiguationService: Shannon entropy detector & multi-option clarifier   │
│  7. LitigationRiskService: Computes Legal Defensibility Index (0–100)           │
│  8. ValueEngineeringService: 3-tier comparative matrix (cost, weight, lifecycle)│
│  9. SarvamAIService: Speech-to-Text (saaras:v3) & Text-to-Speech (bulbul:v3)    │
│ 10. GraphService: In-memory NetworkX & Neo4j (22,000+ nodes, 8,025 edges)       │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 The 7 Recommendation Intelligence Upgrades

1. **Multi-Attribute Constraint & Intent Slot-Filling Engine**: Extracts exposure classes (Mild, Moderate, Severe, Very Severe, Extreme per IS 456 Table 16), seismic zones (Zone II–V per IS 1893/13920), and corrosion contexts, dynamically boosting compliant grades (e.g. `IS 1786 Fe 500D CRS` and `IS 13920`).
2. **Autonomous Standard BOM (Bill of Standards)**: Cascades 5-tier statutory procurement bundles: Product Standard $\rightarrow$ Code of Practice $\rightarrow$ Testing Protocols $\rightarrow$ Lot Sampling Frequency $\rightarrow$ Marking & Tagging Standard.
3. **Domain Contrastive Reranking & Hard-Negative Discrimination**: Penalizes misleading material classes (e.g. concrete sewer pipes `IS 458` are penalized for drinking water queries and HDPE `IS 4984` is boosted).
4. **Schedule of Rates (CPWD / MoRTH / GeM) Grounding**: Directly links technical specifications to CPWD Delhi Schedule of Rates (DSR Subheads 3, 10, 18), MoRTH Sections 1000/1600, and GeM Golden Parameters.
5. **Entropy-Based Active Disambiguation Clarifier**: Detects vague, under-specified queries (e.g. *"pipe"*, *"cement"*, *"transformer"*) and presents a multi-choice decision tree.
6. **Tender Litigation & Pre-Bid Risk Analyzer**: Assesses tender clauses against Competition Act 2002, DPIIT PPP-MII, and Section 29 BIS Act, producing a **0–100 Legal Defensibility Score**.
7. **Multi-Tier Value Engineering Optimizer**: Generates a 3-tier comparative matrix (Minimum Statutory Compliant, Value Engineering Optimum with 15–20% steel weight savings, and Critical Infrastructure for 100+ year lifecycles).

---

## 🛠️ Quickstart

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- (Optional) `SARVAM_API_KEY` for live multilingual speech/translation

### 1. Clone & Configure
```bash
git clone https://github.com/YOUR_USERNAME/manak-specengine.git
cd manak-specengine

# Copy example environment configuration
cp .env.example .env
cp backend/.env.example backend/.env
```

### 2. Backend Setup
```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Run full test suite (168 tests)
pytest -v

# Start FastAPI dev server on port 8000
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup
```bash
cd frontend

# Install Node dependencies
npm install

# Start Next.js on port 3000
npm run dev
```

Visit **http://localhost:3000** in your browser.

---

## 🧪 Comprehensive Verification Suite

The repository contains a battle-tested master test suite with **168 automated tests (100% green)**:

```bash
pytest
# ======================= 168 passed in 12.55s =======================
```

| Test Suite | Focus Area | Status |
| :--- | :--- | :---: |
| `tests/test_phase1.py` | Canonical Schemas & Clause 2 Parser | **18 / 18** |
| `tests/test_phase2.py` | Knowledge Graph Topology & Traversals | **12 / 12** |
| `tests/test_phase3.py` | BM25 + Dense Semantic + QCO Boost | **10 / 10** |
| `tests/test_phase4.py` | Multilingual Translation & Clause Synthesizer | **7 / 7** |
| `tests/test_phase5.py` | Tender Auditor & Compliance Traps | **6 / 6** |
| `tests/test_phase6.py` | FastAPI Endpoints & Health Checks | **8 / 8** |
| `backend/tests/test_multilingual_sarvam.py` | Sarvam AI STT/TTS & Indic Routing | **87 / 87** |
| `tests/test_enterprise_improvements.py` | 7 Recommendation Intelligence Dimensions | **20 / 20** |
| **Total** | **All Automated Test Suites** | **168 / 168 (100%)** |

---

## 📡 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/recommend` | Recommends standards with constraints, BOM, rates, and litigation risk |
| `POST` | `/api/audit` | Audits tender text; returns redline diff and legal defensibility score |
| `POST` | `/api/audit/upload` | Ingests `.pdf`, `.docx`, or `.txt` tender documents for compliance audit |
| `GET` | `/api/clauses/{id}` | Returns metallurgical and engineering property tables |
| `GET` | `/api/cml/verify` | Verifies authentic BIS CM/L licenses with checksum validation |
| `GET` | `/api/bom/{id}` | Returns 5-tier Standard BOM (Bill of Standards) |
| `GET` | `/api/rates/ground` | Grounds query in CPWD DSR, MoRTH, and GeM schedules |
| `GET` | `/api/value-engineering/{id}` | Computes 3-tier comparative value engineering matrix |
| `POST` | `/api/litigation/analyze` | Evaluates tender clauses for litigation traps |
| `POST` | `/api/v1/multilingual/text-to-speech` | Generates base64 WAV audio via Sarvam AI `bulbul:v3` |
| `GET` | `/api/graph/path` | Computes shortest normative dependency bridge between standards |
| `GET` | `/api/graph/timeline/{id}` | Returns revision evolution milestones (1950–2026) |

---

## ⚖️ Legal & Statutory Grounding

- **Bureau of Indian Standards Act, 2016 (Section 16 & 29):** Empowers Central Government to notify mandatory Quality Control Orders (QCOs); mandates penal provisions for non-certified goods.
- **General Financial Rules (GFR), 2017 (Rule 144(i)):** Mandates that procurement technical specifications must promote competition and reference national standards (BIS) where available.
- **Public Procurement (Preference to Make in India) Order, 2017:** Prohibits unjustified foreign standard discrimination against conforming Indian Standards.
- **Competition Act, 2002:** Restricts arbitrary tender exclusions (e.g. blast furnace-only conditions without technical justification).

---

## 📄 License

Licensed under the Apache License, Version 2.0.
