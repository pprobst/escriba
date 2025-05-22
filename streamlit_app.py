import streamlit as st
import requests
import base64
from typing import Dict, Any, List

# Import LANGUAGE_DICT
from app.core.config import LANGUAGE_DICT

# Constants
API_URL = "http://localhost:8000/generate/"
SUPPORTED_AUDIO_TYPES = ["mp3", "wav", "m4a", "ogg"]
DEFAULT_MODEL = "gemini-2.5-flash-preview-05-20"
AVAILABLE_MODELS = [DEFAULT_MODEL, "whisper-large-v3-turbo"]
DEFAULT_INSTRUCTIONS = """Include medical terminology as spoken
Preserve technical medical terms exactly as spoken"""


def setup_page() -> None:
    """Configure the Streamlit page settings."""
    st.set_page_config(page_title="Escriba", page_icon="🎤", layout="wide")
    st.title("Escriba")
    st.markdown("Upload an audio file for transcription.")


def create_instructions_section() -> List[str]:
    """Create a section for instructions with text area.

    Returns:
        List of instruction strings
    """
    st.subheader("Custom Instructions")
    st.markdown("Enter each instruction on a new line:")

    # Text area for all instructions with default values pre-filled
    instructions_text = st.text_area(
        "Transcription Instructions",  # Proper label for accessibility
        value=DEFAULT_INSTRUCTIONS,
        height=150,
        label_visibility="collapsed",  # Still hide the label visually
    )

    # Process instructions (split by newline and filter out empty lines)
    instructions = []
    if instructions_text:
        for line in instructions_text.split("\n"):
            line = line.strip()
            if line:
                instructions.append(line)

    return instructions


def create_input_section() -> Dict[str, Any]:
    """Create and handle the input section of the app.

    Returns:
        Dict containing the input data (audio, model, language, context, instructions)
    """
    with st.container():
        audio_file = st.file_uploader(
            "Upload an audio file", type=SUPPORTED_AUDIO_TYPES
        )

        # Language selection
        # Use a reverse mapping for display names to codes
        language_options = {name: code for code, name in LANGUAGE_DICT.items()}
        selected_language_name = st.selectbox(
            "Select language", list(language_options.keys()), index=0
        )
        language_code = language_options[selected_language_name]

        # Context selection
        context = st.selectbox("Select context", ["Medical", "General"], index=0)

        # No symbols option
        no_symbols = st.checkbox(
            "Write numbers and punctuation as words",
            help="If checked, numbers like '23' will be written as 'twenty three' and punctuation like ',' as 'comma'",
        )

        # Priority words
        priority_words_input = st.text_input(
            "Priority words (comma-separated)",
            help="List of words to pay special attention to during transcription",
        )
        # Convert comma-separated string to list and strip whitespace
        priority_words = (
            [word.strip() for word in priority_words_input.split(",")]
            if priority_words_input
            else []
        )

        # Get instructions
        instructions = create_instructions_section()

        model_name = st.selectbox("Select a model", AVAILABLE_MODELS)

        return {
            "audio_file": audio_file,
            "model_name": model_name,
            "language": language_code,
            "context": context,
            "instructions": instructions,
            "no_symbols": no_symbols,
            "priority_words": priority_words,
        }


def prepare_request_data(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare the request data for the API call.

    Args:
        input_data: Dictionary containing the input data

    Returns:
        Dictionary with the prepared request data
    """
    data = {
        "model_name": input_data["model_name"],
        "template_name": "transcription.jinja2",
        "template_vars": {
            "language": input_data["language"],
            "context": input_data["context"],
            "no_symbols": input_data["no_symbols"],
        },
    }

    # Add priority words if provided
    if input_data["priority_words"]:
        data["template_vars"]["priority_words"] = input_data["priority_words"]

    # Add instructions if provided
    if input_data["instructions"]:
        data["template_vars"]["instructions"] = input_data["instructions"]

    if input_data["audio_file"]:
        bytes_data = input_data["audio_file"].getvalue()
        data["audio_base64"] = base64.b64encode(bytes_data).decode("utf-8")

    return data


def handle_api_response(
    response: requests.Response, response_container: st.empty
) -> None:
    """Handle the streaming API response.

    Args:
        response: The API response object
        response_container: Streamlit container for the response
    """
    full_response = ""
    for chunk in response.iter_content(chunk_size=1024):
        if chunk:
            chunk_text = chunk.decode("utf-8")
            full_response += chunk_text
            response_container.markdown(full_response)


def main() -> None:
    """Main application function."""
    setup_page()

    # Create main layout
    col1, col2 = st.columns([1, 1])

    # Input section
    with col1:
        input_data = create_input_section()
        submit_button = st.button("Submit")

    # Response section with modern styling
    with col2:
        st.subheader("API Response")
        # Create a container with custom styling for the response
        response_style = """
        <style>
        .response-container {
            background-color: #f0f2f6;
            border-radius: 5px;
            padding: 1rem;
            max-height: 600px;
            overflow-y: auto;
            margin-bottom: 1rem;
        }
        </style>
        """
        st.markdown(response_style, unsafe_allow_html=True)
        response_container = st.empty()
        spinner_container = st.empty()

    if submit_button:
        if input_data["audio_file"] is None:
            st.error("Please upload an audio file for transcription")
            return

        try:
            with spinner_container:
                with st.spinner("Processing..."):
                    data = prepare_request_data(input_data)
                    response = requests.post(API_URL, json=data, stream=True)

                    if response.status_code == 200:
                        handle_api_response(response, response_container)
                    else:
                        st.error(f"Error: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
        finally:
            spinner_container.empty()


if __name__ == "__main__":
    main()
