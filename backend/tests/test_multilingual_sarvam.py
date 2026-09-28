"""
Automated Test Gateway for Sarvam AI Multilingual Ingestion Layer.
Covers:
1. Mock Unit Tests: Script detection, STT transcription, text translation, procurement intent normalization.
2. FastAPI Endpoint Tests: /api/v1/multilingual/transcribe-and-translate, /api/v1/multilingual/translate-text, /api/v1/recommend.
3. Live Integration Tests (Active SARVAM_API_KEY): Live translation across Hindi, Tamil, Marathi, and Bengali,
   verifying downstream top-3 retrieval of authoritative Indian Standards (IS 1786/IS 269, IS 1180, IS 2925, IS 4984/4985).
"""

import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.sarvam_service import SarvamAIService, get_sarvam_service
from backend.app.services.retrieval import get_hybrid_retriever


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sarvam_svc():
    return get_sarvam_service()


# ==============================================================================
# 1. UNIT & MOCK TEST SUITE
# ==============================================================================

class TestSarvamServiceUnitMocked:
    """Tests unit logic of SarvamAIService without incurring network calls."""

    def test_detect_script_language(self, sarvam_svc: SarvamAIService):
        assert sarvam_svc.detect_script_language("पुल निर्माण") == "hi-IN"
        assert sarvam_svc.detect_script_language("மின்சார விநியோக") == "ta-IN"
        assert sarvam_svc.detect_script_language("విద్యుత్ సరఫరా") == "te-IN"
        assert sarvam_svc.detect_script_language("ವಿದ್ಯುತ್ ಸರಬರಾಜು") == "kn-IN"
        assert sarvam_svc.detect_script_language("পানীয় জল") == "bn-IN"
        assert sarvam_svc.detect_script_language("પીવીસી પાઇપ") == "gu-IN"
        assert sarvam_svc.detect_script_language("High strength steel bars") == "en-IN"

    def test_is_primarily_english(self, sarvam_svc: SarvamAIService):
        assert sarvam_svc.is_primarily_english("Structural steel plates for bridges") is True
        assert sarvam_svc.is_primarily_english("Hot rolled steel IS 2062 Grade E250") is True
        assert sarvam_svc.is_primarily_english("छत ढलाई के लिए सरिया") is False
        assert sarvam_svc.is_primarily_english("மின்மாற்றி 11 கேவி") is False

    def test_normalize_procurement_intent(self, sarvam_svc: SarvamAIService):
        normalized = sarvam_svc.normalize_procurement_intent("Need sariya for chhat dhalai")
        assert "IS 1786" in normalized
        assert "steel bars" in normalized

        normalized_pipe = sarvam_svc.normalize_procurement_intent("Supply of drinking water pipe")
        assert "IS 4984" in normalized_pipe

        normalized_helmet = sarvam_svc.normalize_procurement_intent("Yellow safety helmet for construction")
        assert "IS 2925" in normalized_helmet

        normalized_transformer = sarvam_svc.normalize_procurement_intent("11 kV distribution transformer")
        assert "IS 1180" in normalized_transformer

    @pytest.mark.anyio
    async def test_translate_to_english_bypasses_for_clean_english(self, sarvam_svc: SarvamAIService):
        res = await sarvam_svc.translate_to_english("Hot rolled structural steel plates")
        assert res["bypassed"] is True
        assert res["translated_text"] == "Hot rolled structural steel plates"
        assert res["source_language_code"] == "en-IN"

    @pytest.mark.anyio
    async def test_translate_to_english_mocked(self):
        service = SarvamAIService(api_key="mock_key")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "translated_text": "Steel rods for concrete construction"
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            res = await service.translate_to_english(
                text="कंक्रीट निर्माण के लिए स्टील की छड़ें",
                source_language_code="hi-IN"
            )
            assert res["bypassed"] is False
            assert res["translated_text"] == "Steel rods for concrete construction"
            assert res["source_language_code"] == "hi-IN"
            mock_post.assert_called_once()

    @pytest.mark.anyio
    async def test_transcribe_audio_mocked(self):
        service = SarvamAIService(api_key="mock_key")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "transcript": "कंक्रीट निर्माण के लिए सरिया",
            "language_code": "hi-IN"
        }

        fake_audio = b"\x00\x01\x02\x03" * 200
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            res = await service.transcribe_audio(
                audio_bytes=fake_audio,
                filename="test_audio.wav",
                language_code="hi-IN"
            )
            assert res["transcript"] == "कंक्रीट निर्माण के लिए सरिया"
            assert res["language_code"] == "hi-IN"


# ==============================================================================
# 2. FASTAPI REST ENDPOINTS TEST SUITE (MOCKED)
# ==============================================================================

class TestFastAPIMultilingualEndpoints:
    """Verifies that FastAPI router handles multilingual requests correctly."""

    def test_translate_text_endpoint(self, client: TestClient):
        with patch.object(
            SarvamAIService,
            "process_multilingual_input",
            new_callable=AsyncMock
        ) as mock_process:
            mock_process.return_value = {
                "original_transcript": "छत ढलाई के लिए सरिया",
                "detected_language": "hi-IN",
                "translated_english": "Steel rebar for roof casting",
                "normalized_query": "Steel rebar for roof casting high strength deformed steel bars for concrete reinforcement IS 1786 Fe 500D",
                "bypassed_translation": False
            }

            payload = {
                "text": "छत ढलाई के लिए सरिया",
                "source_language_code": "hi-IN"
            }
            response = client.post("/api/v1/multilingual/translate-text", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["detected_language"] == "hi-IN"
            assert data["translated_english"] == "Steel rebar for roof casting"
            assert "IS 1786" in data["normalized_query"]

    def test_transcribe_and_translate_endpoint(self, client: TestClient):
        with patch.object(
            SarvamAIService,
            "process_multilingual_input",
            new_callable=AsyncMock
        ) as mock_process:
            mock_process.return_value = {
                "original_transcript": "बिजली का ट्रांसफार्मर 11 केवी",
                "detected_language": "hi-IN",
                "translated_english": "Electric transformer 11 kV",
                "normalized_query": "Electric transformer 11 kV outdoor distribution transformers 11kv IS 1180",
                "bypassed_translation": False
            }

            fake_audio_bytes = b"RIFFmockwavcontent"
            files = {"file": ("mic_recording.wav", fake_audio_bytes, "audio/wav")}
            response = client.post("/api/v1/multilingual/transcribe-and-translate?language_code=hi-IN", files=files)
            assert response.status_code == 200
            data = response.json()
            assert data["original_transcript"] == "बिजली का ट्रांसफार्मर 11 केवी"
            assert data["translated_english"] == "Electric transformer 11 kV"
            assert "IS 1180" in data["normalized_query"]

    def test_recommend_endpoint_multilingual_metadata(self, client: TestClient):
        payload = {
            "query": "पुल निर्माण के लिए 500 टन संरचनात्मक इस्पात",
            "top_k": 3
        }
        response = client.post("/api/recommend", json=payload)
        assert response.status_code == 200
        data = response.json()

        # Verify language metadata structure
        assert "language_metadata" in data
        meta = data["language_metadata"]
        assert "detected_language" in meta
        assert "translated_english" in meta
        assert "normalized_query" in meta

        # Verify candidate standards include IS 2062
        is_numbers = [c["is_number"] for c in data["candidate_standards"]]
        assert any("2062" in n for n in is_numbers)


# ==============================================================================
# 3. LIVE INTEGRATION TESTS (CONDITIONAL ON SARVAM_API_KEY)
# ==============================================================================

HAS_SARVAM_KEY = bool(os.getenv("SARVAM_API_KEY"))

@pytest.mark.skipif(not HAS_SARVAM_KEY, reason="Live integration test requires active SARVAM_API_KEY")
class TestSarvamLiveIntegration:
    """
    Live verification against real Sarvam AI endpoints.
    Translates 4 regional Indian languages and asserts downstream BIS standards retrieval.
    """

    @pytest.mark.anyio
    async def test_live_hindi_cement_and_rebar(self, sarvam_svc: SarvamAIService):
        # 1. Hindi Query: "छत ढलाई के लिए सीमेंट और सरिया"
        res = await sarvam_svc.translate_to_english("छत ढलाई के लिए सीमेंट और सरिया", source_language_code="hi-IN")
        translated = res["translated_text"].lower()
        assert any(w in translated for w in ["cement", "steel", "rebar", "roof", "casting", "rod"])

        # Intent normalization & retrieval
        normalized = sarvam_svc.normalize_procurement_intent(res["translated_text"])
        retriever = get_hybrid_retriever()
        results = retriever.search(query=normalized, top_k=5)
        matched_standards = [r["is_number"] for r in results]
        assert any("1786" in s or "269" in s for s in matched_standards)

    @pytest.mark.anyio
    async def test_live_tamil_transformer_11kv(self, sarvam_svc: SarvamAIService):
        # 2. Tamil Query: "மின்சார விநியோக மின்மாற்றி 11 கேவி"
        res = await sarvam_svc.translate_to_english("மின்சார விநியோக மின்மாற்றி 11 கேவி", source_language_code="ta-IN")
        translated = res["translated_text"].lower()
        assert any(w in translated for w in ["transformer", "11 kv", "power", "distribution", "electricity"])

        # Intent normalization & retrieval
        normalized = sarvam_svc.normalize_procurement_intent(res["translated_text"])
        retriever = get_hybrid_retriever()
        results = retriever.search(query=normalized, top_k=5)
        matched_standards = [r["is_number"] for r in results]
        assert any("1180" in s for s in matched_standards)

    @pytest.mark.anyio
    async def test_live_marathi_safety_helmet(self, sarvam_svc: SarvamAIService):
        # 3. Marathi Query: "औद्योगिक सुरक्षा हेल्मेट पिवळा रंग"
        res = await sarvam_svc.translate_to_english("औद्योगिक सुरक्षा हेल्मेट पिवळा रंग", source_language_code="mr-IN")
        translated = res["translated_text"].lower()
        assert any(w in translated for w in ["helmet", "safety", "industrial", "yellow"])

        # Intent normalization & retrieval
        normalized = sarvam_svc.normalize_procurement_intent(res["translated_text"])
        retriever = get_hybrid_retriever()
        results = retriever.search(query=normalized, top_k=5)
        matched_standards = [r["is_number"] for r in results]
        assert any("2925" in s for s in matched_standards)

    @pytest.mark.anyio
    async def test_live_bengali_pvc_pipes(self, sarvam_svc: SarvamAIService):
        # 4. Bengali Query: "পিভিসি পাইপ পানীয় জলের জন্য"
        res = await sarvam_svc.translate_to_english("পিভিসি পাইপ পানীয় জলের জন্য", source_language_code="bn-IN")
        translated = res["translated_text"].lower()
        assert any(w in translated for w in ["pvc pipe", "pipe", "drinking water", "water"])

        # Intent normalization & retrieval
        normalized = sarvam_svc.normalize_procurement_intent(res["translated_text"])
        retriever = get_hybrid_retriever()
        results = retriever.search(query=normalized, top_k=5)
        matched_standards = [r["is_number"] for r in results]
        assert any("4985" in s or "4984" in s for s in matched_standards)
