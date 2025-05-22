"""External service integrations."""

from .prompt_templates import prompt_template_service
from .transcription_service import get_transcription_service

__all__ = [
    "prompt_template_service",
    "get_transcription_service",
]
