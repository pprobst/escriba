"""Gemini API service integration."""

import base64
from typing import AsyncGenerator, Dict, Optional, Any

import filetype
from google import genai
from google.genai import types

from app.core.config import settings, LANGUAGE_DICT
from app.core.logger import log
from app.services.prompt_templates import prompt_template_service


class GeminiService:
    """Service for interacting with Gemini API."""

    def __init__(self):
        """Initialize the Gemini client."""
        self.client = genai.Client(api_key=settings.google_api_key)

    async def stream_response(
        self,
        audio_base64: Optional[str] = None,
        model_id: str = settings.default_model,
        template_name: Optional[str] = None,
        template_vars: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream responses from Gemini API with multimodal input support.

        Args:
            audio_base64: Optional base64-encoded audio to send to the model
            model_id: The Gemini model identifier
            template_name: Optional Jinja2 template name to use for structuring the prompt
            template_vars: Optional variables to pass to the template

        Yields:
            Text chunks from the model response
        """
        log.info(f"Generating response with model: {model_id}")

        parts = []
        rendered_prompt = None

        # Render prompt from template if provided
        if template_name:
            # Replace language code with full name if present
            if (
                "language" in template_vars
                and template_vars["language"] in LANGUAGE_DICT
            ):
                template_vars["language"] = LANGUAGE_DICT[template_vars["language"]]
            if template_vars is None:
                template_vars = {}
            rendered_prompt = prompt_template_service.render_template(
                template_name, context=template_vars
            )
            log.info(f"Rendered prompt from template: {template_name}")
            log.info(f"Rendered prompt: {rendered_prompt}")

        # Add audio part if provided
        if audio_base64:
            try:
                log.info("Processing audio input")
                audio_data = base64.b64decode(audio_base64)

                # Detect MIME type using filetype
                kind = filetype.guess(audio_data)
                if kind is None:
                    error_msg = "Could not detect MIME type from audio data"
                    log.error(error_msg)
                    yield f"Error: {error_msg}"
                    return

                mime_type = kind.mime
                log.info(f"Detected MIME type: {mime_type}")

                parts.append(
                    types.Part.from_bytes(
                        mime_type=mime_type,
                        data=audio_data,
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
                model=model_id,
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


# Create service instance
gemini_service = GeminiService()
