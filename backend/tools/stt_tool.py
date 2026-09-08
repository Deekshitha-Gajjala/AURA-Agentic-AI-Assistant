import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing from .env")

client = Groq(api_key=GROQ_API_KEY)


def transcribe_audio(audio_path: str) -> str:

    if not os.path.exists(audio_path):
        raise FileNotFoundError(
            f"Audio file not found: {audio_path}"
        )

    try:
        with open(audio_path, "rb") as audio_file:

            transcription = client.audio.transcriptions.create(
                file=(
                    os.path.basename(audio_path),
                    audio_file.read()
                ),
                model="whisper-large-v3-turbo",
                response_format="json"
            )

        text = transcription.text.strip()

        if not text:
            return "I couldn't understand the audio."

        return text

    except Exception as e:

        raise RuntimeError(
            f"Speech-to-text failed: {str(e)}"
        )