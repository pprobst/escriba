"""Transcription service implementations using strategy pattern."""

import abc
import base64
from typing import AsyncGenerator, Dict, Optional, Any

import filetype
import httpx
from google import genai
from google.genai import types

from app.core.config import settings, LANGUAGE_DICT
from app.core.logger import log
from app.services.prompt_templates import prompt_template_service


class TranscriptionService(abc.ABC):
    """Base class for transcription services."""

    @abc.abstractmethod
    async def transcribe(
        self,
        audio_base64: str,
        model_id: Optional[str] = None,
        template_name: Optional[str] = None,
        template_vars: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """Transcribe audio data.

        Args:
            audio_base64: Base64 encoded audio data
            model_id: The model identifier to use (if applicable)
            template_name: Optional template name for prompt formatting
            template_vars: Optional variables for the template

        Yields:
            Text chunks from the transcription
        """
        pass

    def _decode_audio(self, audio_base64: str):
        """Decode and validate base64 audio data.

        Args:
            audio_base64: Base64 encoded audio data

        Returns:
            Tuple of (audio_bytes, mime_type, file_extension)

        Raises:
            ValueError: If the audio data is invalid
        """
        try:
            audio_bytes = base64.b64decode(audio_base64)
            kind = filetype.guess(audio_bytes)
            if kind is None:
                log.error("Cannot determine file type of audio.")
                raise ValueError("Invalid audio file format.")

            return audio_bytes, kind.mime, kind.extension
        except Exception as decode_error:
            log.error(f"Failed to decode Base64 audio data: {decode_error}")
            raise ValueError("Invalid Base64-encoded audio data.") from decode_error


class GeminiTranscriptionService(TranscriptionService):
    """Gemini-based transcription service."""

    def __init__(self):
        """Initialize the Gemini client."""
        self.client = genai.Client(api_key=settings.google_api_key)

    async def transcribe(
        self,
        audio_base64: str,
        model_id: Optional[str] = None,
        template_name: Optional[str] = None,
        template_vars: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """Transcribe audio using Gemini API.

        Args:
            audio_base64: Base64 encoded audio data
            model_id: The Gemini model to use (defaults to settings.default_model)
            template_name: Optional template name for prompt formatting
            template_vars: Optional variables for the template

        Yields:
            Text chunks from the transcription
        """
        log.info(
            f"Generating response with model: {model_id or settings.default_model}"
        )

        parts = []
        rendered_prompt = None

        # Render prompt from template if provided
        if template_name and template_vars:
            # Replace language code with full name if present
            if (
                "language" in template_vars
                and template_vars["language"] in LANGUAGE_DICT
            ):
                template_vars["language"] = LANGUAGE_DICT[template_vars["language"]]

            rendered_prompt = prompt_template_service.render_template(
                template_name, context=template_vars
            )
            log.info(f"Rendered prompt from template: {template_name}")
            log.info(f"Rendered prompt: {rendered_prompt}")

        # Add audio part
        try:
            log.info("Processing audio input")
            audio_bytes, mime_type, _ = self._decode_audio(audio_base64)
            log.info(f"Detected MIME type: {mime_type}")

            parts.append(
                types.Part.from_bytes(
                    mime_type=mime_type,
                    data=audio_bytes,
                )
            )
        except Exception as e:
            error_msg = f"Error processing audio data: {str(e)}"
            log.error(error_msg)
            yield f"Error: {error_msg}"
            return

        # Add text part if provided
        if rendered_prompt:
            parts.append(types.Part.from_text(text=rendered_prompt))

        # Need at least one part
        if not parts:
            error_msg = "No input provided (neither text nor audio)"
            log.error(error_msg)
            yield f"Error: {error_msg}"
            return

        contents = [
            types.Content(
                role="user",
                parts=parts,
            ),
        ]

        generation_config = types.GenerateContentConfig(
            temperature=0,
            thinking_config=types.ThinkingConfig(
                thinking_budget=0,
            ),
            response_mime_type="text/plain",
        )

        try:
            response_stream = self.client.models.generate_content_stream(
                model=model_id or settings.default_model,
                contents=contents,
                config=generation_config,
            )

            for chunk in response_stream:
                try:
                    if hasattr(chunk, "text") and chunk.text:
                        yield chunk.text
                except (ConnectionError, RuntimeError, BrokenPipeError, OSError) as e:
                    # Socket error occurred - log and stop streaming
                    log.info(f"Socket disconnected: {str(e)}")
                    break
        except Exception as e:
            error_msg = f"Error generating content: {str(e)}"
            log.error(error_msg)
            yield f"Error: {str(e)}"


class GroqTranscriptionService(TranscriptionService):
    """Groq-based transcription service."""

    async def transcribe(
        self,
        audio_base64: str,
        model_id: Optional[str] = None,
        template_name: Optional[str] = None,  # Ignored for Groq API
        template_vars: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """Transcribe audio using Groq API.

        Args:
            audio_base64: Base64 encoded audio data
            model_id: Optional model ID (defaults to whisper-large-v3)
            template_name: Optional template name (ignored for Groq API)
            template_vars: Optional variables including 'language' and context info

        Yields:
            The complete transcription as a single chunk
        """
        if not settings.groq_api_key:
            log.error("GROQ_API_KEY not configured.")
            yield "Error: GROQ API key is not configured."
            return

        # Get language if provided
        language = template_vars.get("language") if template_vars else None

        # Construct initial prompt from context and previous_context
        # We cannot use the full prompt content because `initial_prompt` has a limited number of characters
        initial_prompt = None
        if template_vars:
            prompt_parts = []
            if template_vars.get("context"):
                prompt_parts.append("Context: " + str(template_vars["context"]))
            if template_vars.get("previous_context"):
                prompt_parts.append(
                    "Previous context: " + str(template_vars["previous_context"])
                )
            if prompt_parts:
                initial_prompt = " ".join(prompt_parts)
                log.info(
                    f"Constructed initial prompt for Groq: {initial_prompt[:200]}..."
                )

        try:
            audio_bytes, mime_type, extension = self._decode_audio(audio_base64)
            filename = f"audio.{extension}"
        except ValueError as e:
            log.error(f"Audio decode error: {e}")
            yield f"Error: {str(e)}"
            return

        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
        }

        files = {
            "file": (filename, audio_bytes, mime_type),
        }

        data = {
            "model": model_id or "whisper-large-v3",
            "response_format": "text",
        }

        if initial_prompt:
            data["prompt"] = initial_prompt
            log.info(f"Using initial prompt for Groq transcription: {initial_prompt}")

        if language:
            data["language"] = language
            log.info(f"Using language for Groq transcription: {language}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers=headers,
                    files=files,
                    data=data,
                )
                response.raise_for_status()
                yield response.text
            except httpx.HTTPStatusError as e:
                log.error(
                    f"Groq API request failed with status {e.response.status_code}: {e.response.text}"
                )
                yield f"Error: Groq API error: {e.response.status_code} - {e.response.text}"
            except httpx.RequestError as e:
                log.error(f"Error during Groq API request: {e}")
                yield "Error: Failed to connect to Groq API."
            except Exception as ex:
                log.error(f"Unexpected error during Groq transcription: {ex}")
                yield "Error: Failed to process Groq transcription."


# Create service instances
gemini_transcription_service = GeminiTranscriptionService()
groq_transcription_service = GroqTranscriptionService()


def get_transcription_service(provider: str) -> TranscriptionService:
    """Get the appropriate transcription service based on provider name.

    Args:
        provider: The name of the provider or model

    Returns:
        A TranscriptionService instance
    """
    if "gemini" in provider.lower() or "google" in provider.lower():
        return gemini_transcription_service
    elif "whisper" in provider.lower() or "groq" in provider.lower():
        return groq_transcription_service
    else:
        # Default to Gemini
        log.warning(f"Unknown provider '{provider}', using Gemini as default")
        return gemini_transcription_service
