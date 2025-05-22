import base64
import httpx
import filetype
from typing import Optional

from app.core.config import settings
from app.core.logger import log


async def transcribe_audio_groq(
    audio_base64: str,
    initial_prompt: Optional[str] = None,
    language: Optional[str] = None,
) -> str:
    """
    Transcribes audio using the Groq API and Whisper model.

    Args:
        audio_base64: Base64 encoded audio data.
        initial_prompt: Optional initial prompt for the transcription.
        language: Optional language code for the transcription (e.g., "en", "es", "pt").

    Returns:
        The transcribed text.

    Raises:
        ValueError: If the audio data is invalid.
        RuntimeError: If the API call fails.
    """
    if not settings.groq_api_key:
        log.error("GROQ_API_KEY not configured.")
        raise ValueError("GROQ API key is not configured.")

    try:
        audio_bytes = base64.b64decode(audio_base64)
        kind = filetype.guess(audio_bytes)
        if kind is None:
            log.error("Cannot determine file type of audio.")
            raise ValueError("Invalid audio file format.")
        filename = f"audio.{kind.extension}"

    except Exception as decode_error:
        log.error(f"Failed to decode Base64 audio data: {decode_error}")
        raise ValueError("Invalid Base64-encoded audio data.") from decode_error

    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
    }

    files = {
        "file": (filename, audio_bytes, kind.mime),
    }

    data = {
        "model": "whisper-large-v3",  # Using a default model, can be parameterized later
        "response_format": "text",
        # language can be added as a parameter if needed
    }

    if initial_prompt:
        data["prompt"] = initial_prompt
        log.info(
            f"Using initial prompt for Groq transcription: {initial_prompt[:100]}..."
        )

    if language:
        data["language"] = language
        log.info(f"Using language for Groq transcription: {language}")

    async with httpx.AsyncClient(timeout=30.0) as client:  # Using a default timeout
        try:
            response = await client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers=headers,
                files=files,
                data=data,
            )
            response.raise_for_status()
            # The response is plain text when response_format is "text"
            return response.text
        except httpx.HTTPStatusError as e:
            log.error(
                f"Groq API request failed with status {e.response.status_code}: {e.response.text}"
            )
            raise RuntimeError(
                f"Groq API error: {e.response.status_code} - {e.response.text}"
            ) from e
        except httpx.RequestError as e:
            log.error(f"Error during Groq API request: {e}")
            raise RuntimeError("Failed to connect to Groq API.") from e
        except Exception as ex:
            log.error(f"Unexpected error during Groq transcription: {ex}")
            raise RuntimeError("Failed to process Groq transcription.") from ex
