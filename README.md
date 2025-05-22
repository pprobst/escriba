# escriba
Audio transcription API.

## Project Structure

```
.
├── app/                  # Main application package
│   ├── __init__.py       # Package initialization
│   ├── main.py           # Application entry point
│   ├── api/              # API layer
│   │   ├── __init__.py
│   │   ├── endpoints.py  # API endpoint handlers
│   │   ├── models.py     # Request/response models
│   │   └── routes.py     # Route configuration
│   ├── core/             # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py     # Application settings
│   │   └── logger.py     # Logging module
│   └── services/         # External services
│       ├── __init__.py
│       ├── gemini.py     # Gemini API integration
│       ├── groq.py       # Groq API integration
│       └── prompt_templates.py # Template handling
├── prompts/              # Prompt templates
│   ├── transcription.jinja2  # Transcription template
├── streamlit_app.py      # Streamlit UI
├── requirements.txt      # Production dependencies
└── pyproject.toml        # Project configuration
```

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

- `POST /generate/`: Stream text from Gemini models. Language should be provided as a valid language code (e.g., "en", "es", "pt").
  ```json
  {
    "audio_base64": "Base64 encoded audio data",
    "model_name": "gemini-2.5-flash-preview-05-20"
  }
  ```

- `GET /`: API information endpoint

## Examples

### Transcription

```bash
AUDIO_B64=$(base64 -w 0 audio.mp3)
curl -X POST "http://localhost:8000/generate/" \
  -H "Content-Type: application/json" \
  -d '{
    "audio_base64": "'$AUDIO_B64'", 
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
  }'
```
