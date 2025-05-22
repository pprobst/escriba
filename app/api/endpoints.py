"""API endpoints."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from fastapi import Request

from app.api.models import GenerationRequest, TemplateInfo
from app.core.logger import log
from app.core.config import settings
from app.services import (
    gemini_service,
    transcribe_audio_groq,
    prompt_template_service,
)

# Create router
router = APIRouter()


@router.post(
    "/generate/",
    summary="Generate text or transcribe audio",
)
async def generate_stream(request: GenerationRequest, req: Request):
    """Stream generated content from a Gemini model or transcribe audio using Groq.

    Args:
        request: The generation request object
        req: The FastAPI request object for connection state tracking

    Returns:
        A streaming response with generated content
    """
    # Check that at least one input type is provided
    if not request.audio_base64:
        log.warning("Empty request received")
        raise HTTPException(
            status_code=422,
            detail="Request must include audio data",
        )

    # Validate that audio data is provided when using the transcription template or a whisper model
    if (
        request.template_name == "transcription.jinja2"
        or "whisper" in request.model_name.lower()
    ) and not request.audio_base64:
        log.warning("Transcription template or Whisper model used without audio data")
        raise HTTPException(
            status_code=422,
            detail="Audio data is required for transcription or Whisper models",
        )

    log_message = f"Request received - Model: {request.model_name}"
    if request.audio_base64:
        log_message += ", Audio data included"
    if request.template_name:
        log_message += f", Template: {request.template_name}"

    log.info(log_message)

    # Apply default template_vars if not provided or add default values for missing fields
    template_vars = request.template_vars or {}

    # Set default language if not provided
    if "language" not in template_vars:
        template_vars["language"] = settings.default_language

    # Set default context if not provided
    if "context" not in template_vars:
        template_vars["context"] = settings.default_context

    async def generate():
        try:
            initial_prompt_for_groq = None
            # Construct initial_prompt for Groq specifically from context and previous_context, since the prompt length must be 896 characters or fewer.
            if (
                "whisper" in request.model_name.lower()
            ):  # Only construct this for Whisper/Groq
                prompt_parts = []
                if template_vars.get("context"):
                    prompt_parts.append(str(template_vars["context"]))
                if template_vars.get("previous_context"):
                    prompt_parts.append(str(template_vars["previous_context"]))

                if prompt_parts:
                    initial_prompt_for_groq = " ".join(prompt_parts)
                    log.info(
                        f"Constructed initial prompt for Groq from context/previous_context: {initial_prompt_for_groq[:200]}..."
                    )
                else:
                    log.info(
                        "No context or previous_context found for Groq initial prompt."
                    )

            if "whisper" in request.model_name.lower():
                if not request.audio_base64:
                    log.error(
                        "Whisper model called without audio data in generate function"
                    )
                    yield "Error: Audio data is required for Whisper models."
                    return

                log.info(
                    f"Transcribing audio with Groq Whisper model: {request.model_name}"
                )
                transcription = await transcribe_audio_groq(
                    audio_base64=request.audio_base64,
                    initial_prompt=initial_prompt_for_groq,  # Pass constructed prompt
                    language=template_vars.get("language"),
                )
                yield transcription
            else:
                # For Gemini, the stream_response method handles template rendering internally
                log.info(f"Generating text with Gemini model: {request.model_name}")
                stream = gemini_service.stream_response(
                    audio_base64=request.audio_base64,
                    model_id=request.model_name,
                    template_name=request.template_name,
                    template_vars=template_vars,
                )
                async for chunk in stream:
                    if await req.is_disconnected():
                        log.info("Client disconnected during streaming")
                        break
                    yield chunk
        except (
            HTTPException
        ) as http_exc:  # Re-raise HTTPExceptions to be handled by FastAPI
            raise http_exc
        except ValueError as ve:
            log.error(f"Value error during processing: {str(ve)}")
            yield f"Error: {str(ve)}"  # Stream the error message back
        except RuntimeError as re:
            log.error(f"Runtime error during processing: {str(re)}")
            yield f"Error: {str(re)}"  # Stream the error message back
        except Exception as e:
            log.error(f"Error during streaming/transcription: {str(e)}")
            yield "An unexpected error occurred."  # Generic error for unexpected issues

    return StreamingResponse(
        generate(),
        media_type="text/plain",
    )


@router.get("/templates/", summary="List available prompt templates")
async def list_templates():
    """List all available prompt templates.

    Returns:
        A list of template information
    """
    try:
        templates = prompt_template_service.list_templates()

        # Create template info objects
        template_info_list = []
        for template_name in templates:
            # Create a basic template info
            template_info = TemplateInfo(
                name=template_name,
                # In a more advanced implementation, you might extract descriptions
                # from template files or a separate metadata store
                description=f"Template: {template_name}",
            )
            template_info_list.append(template_info)

        return template_info_list
    except Exception as e:
        log.error(f"Error listing templates: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing templates: {str(e)}",
        )


@router.get("/", include_in_schema=False)
async def root():
    """API information endpoint."""
    log.debug("Root endpoint accessed")
    return {
        "message": "Transcriber API Service",
        "documentation": "/docs",
        "endpoints": {
            "generate": "/generate/",
            "templates": "/templates/",
        },
        "example_payload": {
            "text": "Your prompt here (optional)",
            "audio_base64": "Base64 encoded audio data (optional)",
            "model_name": "gemini-2.5-flash-preview-05-20",
            "template_name": "transcription.jinja2",
            "template_vars": {
                "language": "pt",
                "context": "Medical",
                "instructions": [
                    "Include medical terminology as spoken",
                    "Preserve technical medical terms exactly as spoken",
                ],
            },
        },
        "available_templates": {
            "transcription.jinja2": "Template for audio transcription with language, context, and instruction options (requires audio_base64)",
        },
    }
