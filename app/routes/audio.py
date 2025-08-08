from fastapi import APIRouter, File, UploadFile, HTTPException, status, Query
from fastapi.responses import JSONResponse
import os
import httpx


router = APIRouter(prefix="/audio", tags=["Audio"])


MAX_BYTES = 25 * 1024 * 1024  # 25 MB
ALLOWED_EXTENSIONS = {"mp3", "m4a", "webm", "wav"}


def _validate_extension(filename: str) -> bool:
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[-1].lower()
    return ext in ALLOWED_EXTENSIONS


@router.post("/transcribe")
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    language: str | None = Query(default=None, description="Language code, e.g., 'en'. Defaults to auto-detect")
):
    """Transcribe audio via OpenAI Whisper and return text."""
    if audio_file is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file uploaded")

    if not _validate_extension(audio_file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # Read file content and enforce size limit
    content = await audio_file.read()
    if len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    if len(content) > MAX_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large (max 25MB)")

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Whisper API key not configured")

    # Prepare multipart form-data for OpenAI Whisper
    files = {
        "file": (os.path.basename(audio_file.filename), content, audio_file.content_type or "application/octet-stream"),
    }
    data = {
        "model": "whisper-1",
    }
    if language:
        data["language"] = language

    headers = {
        "Authorization": f"Bearer {openai_api_key}",
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers=headers,
                files=files,
                data=data,
            )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Whisper API error: {resp.status_code}"
            )
        payload = resp.json()
        text = payload.get("text")
        if not isinstance(text, str):
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Invalid response from Whisper API")
        return JSONResponse(status_code=200, content={"transcription": text})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Whisper API failure: {str(e)}")


