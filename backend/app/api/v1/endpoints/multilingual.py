"""
Multilingual Voice & Text REST Endpoints for Manak-SpecEngine.
Integrates Sarvam AI Speech-to-Text and Translation endpoints.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from pydantic import BaseModel, Field

from backend.app.services.sarvam_service import get_sarvam_service, SarvamAIService

router = APIRouter(prefix="/multilingual", tags=["Multilingual Ingestion"])


class TranslateTextRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Source regional or English procurement text")
    source_language_code: Optional[str] = Field(
        default=None,
        description="Optional BCP-47 language code (e.g. 'hi-IN', 'ta-IN', 'te-IN', 'kn-IN', 'mr-IN', 'bn-IN', 'gu-IN')"
    )


class MultilingualResponse(BaseModel):
    original_text: str
    detected_language: str
    translated_english: str
    normalized_query: str
    bypassed_translation: bool = False
    provider: str = "Sarvam AI (mayura:v1)"


class AudioTranscribeResponse(BaseModel):
    original_transcript: str
    detected_language: str
    translated_english: str
    normalized_query: str
    provider: str = "Sarvam AI (saarika:v2 + mayura:v1)"


@router.post("/transcribe-and-translate", response_model=AudioTranscribeResponse)
async def transcribe_and_translate_audio(
    file: UploadFile = File(..., description="Speech audio file (.wav, .mp3, .webm, .ogg, .m4a)"),
    language_code: Optional[str] = Query(default="unknown", description="Optional language code or 'unknown' for auto-detect")
) -> AudioTranscribeResponse:
    """
    Ingests voice speech audio in any Indian language, transcribes it via Sarvam AI saarika:v2,
    and translates it to formal English procurement specifications via mayura:v1.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Audio file must have a valid filename")

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Uploaded audio file is empty")

    sarvam_svc = get_sarvam_service()
    result = await sarvam_svc.process_multilingual_input(
        audio_bytes=audio_bytes,
        filename=file.filename,
        language_code=language_code
    )

    if not result.get("original_transcript") and "error" in result:
        raise HTTPException(status_code=502, detail=result.get("error"))

    return AudioTranscribeResponse(
        original_transcript=result["original_transcript"],
        detected_language=result["detected_language"],
        translated_english=result["translated_english"],
        normalized_query=result["normalized_query"]
    )


class TextToSpeechRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to synthesize to speech")
    language_code: Optional[str] = Field(default="hi-IN", description="Target language code e.g. hi-IN, en-IN, ta-IN, bn-IN, mr-IN")
    speaker: Optional[str] = Field(default="aditya", description="Speaker name e.g. aditya, ritu, priya")


class TextToSpeechResponse(BaseModel):
    audio_base64: str
    format: str = "wav"
    language_code: str
    speaker: str
    provider: str = "Sarvam AI (bulbul:v3)"
    error: Optional[str] = None


@router.post("/translate-text", response_model=MultilingualResponse)
async def translate_text(req: TranslateTextRequest) -> MultilingualResponse:
    """
    Translates colloquial regional procurement text or Indian scripts into formal English technical search terms.
    """
    sarvam_svc = get_sarvam_service()
    result = await sarvam_svc.process_multilingual_input(
        text=req.text,
        language_code=req.source_language_code
    )

    return MultilingualResponse(
        original_text=result["original_transcript"],
        detected_language=result["detected_language"],
        translated_english=result["translated_english"],
        normalized_query=result["normalized_query"],
        bypassed_translation=result.get("bypassed_translation", False)
    )


@router.post("/text-to-speech", response_model=TextToSpeechResponse)
async def text_to_speech(req: TextToSpeechRequest) -> TextToSpeechResponse:
    """
    Synthesizes Indian procurement text, standard summaries, or QCO warnings into natural voice audio
    via Sarvam AI bulbul:v3 model.
    """
    sarvam_svc = get_sarvam_service()
    result = await sarvam_svc.text_to_speech(
        text=req.text,
        target_language_code=req.language_code or "hi-IN",
        speaker=req.speaker or "aditya"
    )

    return TextToSpeechResponse(
        audio_base64=result.get("audio_base64", ""),
        format=result.get("format", "wav"),
        language_code=result.get("language_code", req.language_code or "hi-IN"),
        speaker=result.get("speaker", req.speaker or "aditya"),
        error=result.get("error")
    )

