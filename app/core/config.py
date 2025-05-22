"""Application configuration settings."""

import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

# Explicitly load .env file from project root
load_dotenv()


LANGUAGE_DICT = {
    "en": "English",
    "es": "Español",
    "pt": "Português",
    "fr": "Français",
    "de": "Deutsch",
}


class Settings(BaseSettings):
    """Application settings."""

    # API configuration
    app_title: str = "Escriba"
    app_description: str = "Audio Transcription Service"
    app_version: str = "1.0.0"

    # Google API settings
    google_api_key: str = os.environ.get("GOOGLE_API_KEY", "")
    default_model: str = "gemini-2.5-flash-preview-05-20"

    # Groq API settings
    groq_api_key: str = os.environ.get("GROQ_API_KEY", "")

    # Prompt template defaults
    default_template_name: str = "transcription.jinja2"
    default_language: str = ""
    default_context: str = "General"
    no_symbols: bool = (
        False  # If True, converts numbers and punctuation to words in transcription
    )
    priority_words: List[
        str
    ] = []  # Words to pay special attention to during transcription

    # Pydantic v2 configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=True,
        extra="ignore",
    )


# Create settings instance
settings = Settings()

# Validate settings
if not settings.google_api_key:
    raise RuntimeError("GOOGLE_API_KEY environment variable not set")

# Note: We are not validating GROQ_API_KEY here as it's optional for the app to run
# if only Gemini models are used. The service itself will raise an error if it's called
# without the key being set.
