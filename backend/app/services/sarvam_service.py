"""
Sarvam AI Multilingual Voice & Text Ingestion Service for Manak-SpecEngine.
Integrates Sarvam AI Speech-to-Text (saarika:v2) and Text Translation (mayura:v1)
to enable voice-based and regional-language technical procurement search across Indian languages.
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, Optional
import httpx
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
load_dotenv(Path(__file__).resolve().parent.parent.parent.parent / ".env")

SARVAM_BASE_URL = "https://api.sarvam.ai"

# Supported Indian Language Codes mapped to Unicode script blocks
UNICODE_SCRIPT_TO_LANG = [
    (re.compile(r"[\u0900-\u097F]"), "hi-IN"),  # Devanagari (Hindi/Marathi)
    (re.compile(r"[\u0B80-\u0BFF]"), "ta-IN"),  # Tamil
    (re.compile(r"[\u0C00-\u0C7F]"), "te-IN"),  # Telugu
    (re.compile(r"[\u0C80-\u0CFF]"), "kn-IN"),  # Kannada
    (re.compile(r"[\u0980-\u09FF]"), "bn-IN"),  # Bengali
    (re.compile(r"[\u0A80-\u0AFF]"), "gu-IN"),  # Gujarati
    (re.compile(r"[\u0D00-\u0D7F]"), "ml-IN"),  # Malayalam
    (re.compile(r"[\u0A00-\u0A7F]"), "pa-IN"),  # Punjabi
    (re.compile(r"[\u0B00-\u0B7F]"), "od-IN"),  # Odia
]

# Procurement domain idiom enhancement dictionary
PROCUREMENT_IDIOM_MAP = {
    r"\b(?:sariya|rebar|steel rod|iron rod|chhat dhalai)\b": "high strength deformed steel bars for concrete reinforcement IS 1786 Fe 500D",
    r"\b(?:structural steel|steel plate|girder|beam section)\b": "hot rolled medium and high tensile structural steel IS 2062",
    r"\b(?:cement|cement bag|portland cement|opc)\b": "ordinary portland cement 43 53 grade IS 269 IS 8112 IS 12269",
    r"\b(?:pvc pipe|upvc pipe|cpvc pipe|plastic pipe)\b": "unplasticized polyvinyl chloride upvc pipes for potable water supplies IS 4985",
    r"\b(?:water pipe|drinking water pipe|nal ka pipe|potable water|pipe.*drinking water|pipe.*water supply)\b": "unplasticized pvc pipes for potable water supplies IS 4985 high density polyethylene hdpe pipes for water supply IS 4984",
    r"\b(?:transformer|11 kv|power distribution)\b": "outdoor distribution transformers 11kv IS 1180",
    r"\b(?:safety helmet|hard hat|suraksha helmet)\b": "industrial safety helmets IS 2925",
    r"\b(?:safety shoes|safety boots|protective footwear)\b": "personal protective equipment safety footwear IS 15298",
    r"\b(?:solar panel|solar plate|pv module|photovoltaic)\b": "crystalline silicon terrestrial photovoltaic pv modules IS 14286",
    r"\b(?:laptop|computer|power adapter)\b": "information technology equipment safety IS 13252",
    r"\b(?:fire extinguisher|fire safety|dry chemical powder)\b": "portable fire extinguishers IS 15683",
    r"\b(?:electric wire|copper wire|pvc cable)\b": "pvc insulated electric wires and cables IS 694"
}


class SarvamAIService:
    """
    High-performance client for Sarvam AI Speech-to-Text and Translation APIs.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: str = SARVAM_BASE_URL):
        self.api_key = api_key or os.getenv("SARVAM_API_KEY", "")
        self.base_url = base_url.rstrip("/")

    def detect_script_language(self, text: str) -> str:
        """Detects Indian regional language code from Unicode script block."""
        if not text:
            return "en-IN"
        for pattern, code in UNICODE_SCRIPT_TO_LANG:
            if pattern.search(text):
                return code
        return "en-IN"

    def is_primarily_english(self, text: str) -> bool:
        """Checks if the text is already standard English / alphanumeric."""
        if not text:
            return True
        non_ascii = [c for c in text if ord(c) > 127]
        # If less than 5% non-ascii, treat as English
        return len(non_ascii) / max(1, len(text)) < 0.05

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        filename: str = "audio.wav",
        language_code: Optional[str] = "unknown"
    ) -> Dict[str, Any]:
        """
        Transcribes speech audio into text using Sarvam AI saarika:v2 model.
        """
        if not audio_bytes:
            raise ValueError("Audio data is empty")

        if len(audio_bytes) > 10 * 1024 * 1024:
            raise ValueError("Audio file size exceeds maximum 10 MB limit")

        if not self.api_key:
            return {
                "transcript": "Audio transcription unavailable (missing SARVAM_API_KEY)",
                "language_code": language_code or "unknown",
                "error": "MISSING_API_KEY"
            }

        url = f"{self.base_url}/speech-to-text"
        headers = {
            "api-subscription-key": self.api_key
        }

        # Determine mime type
        ext = filename.split(".")[-1].lower() if "." in filename else "wav"
        mime_map = {
            "wav": "audio/wav",
            "mp3": "audio/mpeg",
            "webm": "audio/webm",
            "ogg": "audio/ogg",
            "m4a": "audio/mp4"
        }
        mime_type = mime_map.get(ext, "audio/wav")

        files = {
            "file": (filename, audio_bytes, mime_type)
        }
        data = {
            "model": "saarika:v2"
        }
        if language_code and language_code != "unknown":
            data["language_code"] = language_code

        async with httpx.AsyncClient(timeout=25.0) as client:
            try:
                response = await client.post(url, headers=headers, files=files, data=data)
                if response.status_code == 200:
                    res_json = response.json()
                    return {
                        "transcript": res_json.get("transcript", "").strip(),
                        "language_code": res_json.get("language_code", language_code or "hi-IN")
                    }
                else:
                    return {
                        "transcript": "",
                        "language_code": language_code or "unknown",
                        "error": f"Sarvam STT failed with status {response.status_code}: {response.text}"
                    }
            except Exception as e:
                return {
                    "transcript": "",
                    "language_code": language_code or "unknown",
                    "error": f"Sarvam STT request exception: {str(e)}"
                }

    async def translate_to_english(
        self,
        text: str,
        source_language_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Translates regional Indian text to formal English using Sarvam AI mayura:v1.
        Bypasses API if text is already standard English.
        """
        cleaned = text.strip()
        if not cleaned:
            return {
                "translated_text": "",
                "source_language_code": "en-IN",
                "bypassed": True
            }

        # Auto-detect script if not provided or unknown
        if not source_language_code or source_language_code in ("unknown", "auto"):
            detected_code = self.detect_script_language(cleaned)
        else:
            detected_code = source_language_code

        # If already English, bypass external call to minimize latency
        if detected_code == "en-IN" and self.is_primarily_english(cleaned):
            return {
                "translated_text": cleaned,
                "source_language_code": "en-IN",
                "bypassed": True
            }

        if not self.api_key:
            # Fallback to local heuristic translation
            return {
                "translated_text": cleaned,
                "source_language_code": detected_code,
                "bypassed": True,
                "warning": "SARVAM_API_KEY not configured"
            }

        url = f"{self.base_url}/translate"
        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "input": cleaned,
            "source_language_code": detected_code,
            "target_language_code": "en-IN",
            "speaker_gender": "Male",
            "mode": "formal",
            "model": "mayura:v1"
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    translated = data.get("translated_text", "").strip()
                    return {
                        "translated_text": translated,
                        "source_language_code": detected_code,
                        "bypassed": False
                    }
                else:
                    return {
                        "translated_text": cleaned,
                        "source_language_code": detected_code,
                        "bypassed": False,
                        "error": f"Sarvam Translate API status {response.status_code}: {response.text}"
                    }
            except Exception as e:
                return {
                    "translated_text": cleaned,
                    "source_language_code": detected_code,
                    "bypassed": False,
                    "error": f"Sarvam Translate API exception: {str(e)}"
                }

    def normalize_procurement_intent(self, translated_text: str) -> str:
        """
        Normalizes translated English into high-precision technical Indian Standards keywords.
        Maps colloquial procurement vernacular into exact BIS designations.
        """
        if not translated_text:
            return ""

        augmented_tokens = []
        text_lower = translated_text.lower()

        for pattern_str, domain_keywords in PROCUREMENT_IDIOM_MAP.items():
            if re.search(pattern_str, text_lower, re.I):
                augmented_tokens.append(domain_keywords)

        if augmented_tokens:
            return f"{translated_text} {' '.join(augmented_tokens)}"
        return translated_text

    async def process_multilingual_input(
        self,
        text: Optional[str] = None,
        audio_bytes: Optional[bytes] = None,
        filename: str = "audio.wav",
        language_code: Optional[str] = "unknown"
    ) -> Dict[str, Any]:
        """
        Full unified ingestion pipeline: Audio STT -> Translation -> Intent Normalization.
        """
        original_transcript = text or ""
        detected_language = language_code or "unknown"

        # 1. If audio provided, transcribe first
        if audio_bytes:
            stt_result = await self.transcribe_audio(
                audio_bytes=audio_bytes,
                filename=filename,
                language_code=language_code
            )
            original_transcript = stt_result.get("transcript", "")
            detected_language = stt_result.get("language_code", detected_language)

        # 2. Translate to English
        translation_result = await self.translate_to_english(
            text=original_transcript,
            source_language_code=detected_language
        )
        translated_english = translation_result.get("translated_text", original_transcript)
        final_lang = translation_result.get("source_language_code", detected_language)

        # 3. Intent Normalization
        normalized_query = self.normalize_procurement_intent(translated_english)

        return {
            "original_transcript": original_transcript,
            "detected_language": final_lang,
            "translated_english": translated_english,
            "normalized_query": normalized_query,
            "bypassed_translation": translation_result.get("bypassed", False)
        }

    async def text_to_speech(
        self,
        text: str,
        target_language_code: str = "hi-IN",
        speaker: str = "aditya"
    ) -> Dict[str, Any]:
        """
        Synthesizes text into natural spoken Indian language audio using Sarvam AI bulbul:v3 model.
        Returns base64 encoded audio string and format.
        """
        if not text:
            raise ValueError("Input text is empty")

        if not self.api_key:
            return {
                "audio_base64": "",
                "format": "wav",
                "error": "MISSING_API_KEY",
                "language_code": target_language_code
            }

        url = f"{self.base_url}/text-to-speech"
        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json"
        }
        # Keep input text concise (under 500 characters) for optimal TTS latency
        trimmed_text = text[:480].strip()
        payload = {
            "inputs": [trimmed_text],
            "target_language_code": target_language_code,
            "speaker": speaker,
            "model": "bulbul:v3"
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    audios = data.get("audios", [])
                    audio_b64 = audios[0] if audios else ""
                    return {
                        "audio_base64": audio_b64,
                        "format": "wav",
                        "language_code": target_language_code,
                        "speaker": speaker,
                        "model": "bulbul:v3"
                    }
                else:
                    return {
                        "audio_base64": "",
                        "format": "wav",
                        "error": f"Sarvam TTS failed with status {response.status_code}: {response.text}",
                        "language_code": target_language_code
                    }
            except Exception as e:
                return {
                    "audio_base64": "",
                    "format": "wav",
                    "error": f"Sarvam TTS exception: {str(e)}",
                    "language_code": target_language_code
                }


# Global singleton instance
_sarvam_service_instance: Optional[SarvamAIService] = None


def get_sarvam_service() -> SarvamAIService:
    """Returns singleton SarvamAIService instance."""
    global _sarvam_service_instance
    if _sarvam_service_instance is None:
        _sarvam_service_instance = SarvamAIService()
    return _sarvam_service_instance
