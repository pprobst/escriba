"""API request and response models."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from app.core.config import settings


class GenerationRequest(BaseModel):
    """Model for text generation requests."""

    audio_base64: str = Field(description="Base64 encoded audio data")
    model_name: str = Field(
        default=settings.default_model, description="Gemini model to use"
    )
    template_name: Optional[str] = Field(
        default=settings.default_template_name,
        description="Jinja2 template name to structure the prompt",
    )
    template_vars: Optional[Dict[str, Any]] = Field(
        default=None, description="Variables to pass to the template"
    )


class TemplateInfo(BaseModel):
    """Information about a prompt template."""

    name: str
    description: Optional[str] = None
