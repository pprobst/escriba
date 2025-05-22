# escriba
Audio transcription API.

## Requirements
- Python >=3.11 
- uv
- Google (Gemini) API key

## Setup

1. Create a `.env` file with your Google API key:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   or 
   ```bash
   uv sync
   ```

3. Run the API server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. Access the API at http://localhost:8000

5. Run the Streamlit interface:
   ```bash
   streamlit run streamlit_app.py
   ```

## API Endpoints

- `POST /generate/`: Stream text from audio transcription. Supports both Gemini and Groq transcription models.
  ```json
  {
    "audio_base64": "Base64 encoded audio data",
    "model_name": "gemini-2.5-flash-preview-05-20",
    "template_name": "transcription.jinja2",
    "template_vars": {
      "language": "en",
      "context": "radiology",
      "previous_context": "two centimeter mass in the right lung",
      "instructions": [
        "Include medical terminology as spoken",
        "Preserve technical medical terms exactly as spoken"
      ]
    }
  }
  ```

- `GET /templates/`: List all available prompt templates

- `GET /`: API information endpoint

- `GET /docs`: OpenAPI docs

## Project Structure

```
.
├── app/                             # Main application package
│   ├── __init__.py                  # Package initialization
│   ├── main.py                      # Application entry point
│   ├── api/                         # API layer
│   │   ├── __init__.py
│   │   ├── endpoints.py             # API endpoint handlers
│   │   ├── models.py                # Request/response models
│   │   └── routes.py                # Route configuration
│   ├── core/                        # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py                # Application settings
│   │   └── logger.py                # Logging module
│   └── services/                    # External services
│       ├── __init__.py
│       ├── gemini.py                # Gemini API integration
│       ├── groq.py                  # Groq API integration
│       ├── prompt_templates.py      # Template handling
│       └── transcription_service.py # Transcription service
├── audio/                           # Directory for audio samples
├── datasets/                        # Test datasets for benchmarking
├── prompts/                         # Prompt templates
│   └── transcription.jinja2         # Transcription template
├── streamlit_app.py                 # Streamlit UI for testing
├── requirements.txt                 # Production dependencies
└── pyproject.toml                   # Project configuration
```
