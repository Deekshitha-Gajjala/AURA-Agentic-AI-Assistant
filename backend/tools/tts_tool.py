import os
import re
import tempfile
import wave

from dotenv import load_dotenv
from groq import Groq


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is missing from the environment."
    )


# ============================================================
# GROQ CLIENT
# ============================================================

client = Groq(
    api_key=GROQ_API_KEY
)


# ============================================================
# ORPHEUS CONFIGURATION
# ============================================================

TTS_MODEL = "canopylabs/orpheus-v1-english"
TTS_VOICE = "troy"

# Groq Orpheus currently accepts a maximum of
# 200 characters per request.
MAX_CHARS_PER_REQUEST = 200


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(text: str) -> str:
    """
    Clean text before sending it to the TTS model.
    """

    if not isinstance(text, str):
        return ""

    text = text.strip()

    # Remove excessive whitespace
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text


# ============================================================
# TEXT CHUNKING
# ============================================================

def split_text(text: str, max_chars: int = MAX_CHARS_PER_REQUEST):
    """
    Split text into chunks that stay within the
    Orpheus request limit.

    Attempts to split at sentence/word boundaries.
    """

    text = clean_text(text)

    if not text:
        return []

    if len(text) <= max_chars:
        return [text]

    chunks = []

    # First split by sentences.
    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    current = ""

    for sentence in sentences:

        sentence = sentence.strip()

        if not sentence:
            continue

        # If the sentence fits into the current chunk
        if len(current) + len(sentence) + 1 <= max_chars:

            if current:
                current += " "

            current += sentence

            continue

        # Save the current chunk
        if current:
            chunks.append(current)
            current = ""

        # If the sentence itself is too large,
        # split it by words.
        if len(sentence) > max_chars:

            words = sentence.split()

            word_chunk = ""

            for word in words:

                if not word_chunk:
                    word_chunk = word

                elif (
                    len(word_chunk)
                    + len(word)
                    + 1
                    <= max_chars
                ):
                    word_chunk += " " + word

                else:
                    chunks.append(word_chunk)
                    word_chunk = word

            if word_chunk:
                current = word_chunk

        else:
            current = sentence

    if current:
        chunks.append(current)

    return chunks


# ============================================================
# GENERATE ONE WAV FILE
# ============================================================

def generate_wav_chunk(
    text: str,
    output_path: str
):
    """
    Generate one WAV file using Groq Orpheus.
    """

    response = client.audio.speech.create(
        model=TTS_MODEL,
        voice=TTS_VOICE,
        input=text,
        response_format="wav"
    )

    # Use Groq's official file-writing method.
    # This avoids manually constructing WAV headers.
    response.write_to_file(
        output_path
    )

    if not os.path.exists(output_path):
        raise RuntimeError(
            "Groq did not generate the expected audio file."
        )

    if os.path.getsize(output_path) == 0:
        raise RuntimeError(
            "Generated audio file is empty."
        )


# ============================================================
# COMBINE WAV FILES
# ============================================================

def combine_wav_files(
    input_files,
    output_path
):
    """
    Safely combine multiple WAV files.

    We intentionally construct the final WAV header
    using Python's wave module rather than manually
    calculating the WAV data size.
    """

    if not input_files:
        raise RuntimeError(
            "No audio chunks were generated."
        )

    # If there is only one chunk, simply move/copy it.
    if len(input_files) == 1:

        with open(
            input_files[0],
            "rb"
        ) as source:

            data = source.read()

        with open(
            output_path,
            "wb"
        ) as destination:

            destination.write(data)

        return

    first_params = None

    with wave.open(
        input_files[0],
        "rb"
    ) as first:

        first_params = first.getparams()

    # Create final WAV file.
    with wave.open(
        output_path,
        "wb"
    ) as output:

        output.setnchannels(
            first_params.nchannels
        )

        output.setsampwidth(
            first_params.sampwidth
        )

        output.setframerate(
            first_params.framerate
        )

        output.setcomptype(
            first_params.comptype,
            first_params.compname
        )

        for file_path in input_files:

            with wave.open(
                file_path,
                "rb"
            ) as source:

                params = source.getparams()

                # Make sure all chunks have compatible
                # audio properties.
                if (
                    params.nchannels
                    != first_params.nchannels
                    or
                    params.sampwidth
                    != first_params.sampwidth
                    or
                    params.framerate
                    != first_params.framerate
                    or
                    params.comptype
                    != first_params.comptype
                ):
                    raise RuntimeError(
                        "Generated audio chunks have "
                        "incompatible WAV formats."
                    )

                frames = source.readframes(
                    source.getnframes()
                )

                output.writeframesraw(
                    frames
                )


# ============================================================
# MAIN TEXT-TO-SPEECH FUNCTION
# ============================================================

def text_to_speech(
    text: str,
    output_path: str
):
    """
    Convert text into a WAV audio file.

    Supports short and long text.
    """

    text = clean_text(text)

    if not text:
        raise ValueError(
            "Text cannot be empty."
        )

    output_directory = os.path.dirname(
        os.path.abspath(output_path)
    )

    os.makedirs(
        output_directory,
        exist_ok=True
    )

    chunks = split_text(
        text
    )

    if not chunks:
        raise RuntimeError(
            "No valid text chunks were created."
        )

    temporary_files = []

    try:

        # ----------------------------------------------------
        # GENERATE EACH CHUNK
        # ----------------------------------------------------

        for index, chunk in enumerate(chunks):

            temp_file = tempfile.NamedTemporaryFile(
                suffix=f"_chunk_{index}.wav",
                delete=False
            )

            temp_path = temp_file.name

            temp_file.close()

            temporary_files.append(
                temp_path
            )

            print(
                f"TTS chunk {index + 1}/{len(chunks)} "
                f"({len(chunk)} characters)"
            )

            generate_wav_chunk(
                text=chunk,
                output_path=temp_path
            )

        # ----------------------------------------------------
        # COMBINE
        # ----------------------------------------------------

        combine_wav_files(
            input_files=temporary_files,
            output_path=output_path
        )

        # ----------------------------------------------------
        # FINAL VALIDATION
        # ----------------------------------------------------

        if not os.path.exists(
            output_path
        ):
            raise RuntimeError(
                "Final audio file was not created."
            )

        file_size = os.path.getsize(
            output_path
        )

        if file_size == 0:
            raise RuntimeError(
                "Final audio file is empty."
            )

        print(
            "TTS generated successfully:"
        )

        print(
            f"Output: {output_path}"
        )

        print(
            f"Size: {file_size} bytes"
        )

        return output_path

    except Exception as e:

        print(
            "TTS ERROR:",
            repr(e)
        )

        # Remove partially generated output
        if os.path.exists(
            output_path
        ):

            try:
                os.remove(
                    output_path
                )

            except Exception:
                pass

        raise RuntimeError(
            f"Text-to-speech failed: {str(e)}"
        ) from e

    finally:

        # ----------------------------------------------------
        # CLEAN TEMP FILES
        # ----------------------------------------------------

        for temp_file in temporary_files:

            try:

                if os.path.exists(
                    temp_file
                ):
                    os.remove(
                        temp_file
                    )

            except Exception:
                pass


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    test_output = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        "test_tts.wav"
    )

    print("=" * 60)
    print("AURA TTS TEST")
    print("=" * 60)

    text_to_speech(
        text=(
            "Hello, I am AURA. "
            "How can I help you today?"
        ),
        output_path=test_output
    )

    print("=" * 60)
    print("TTS TEST COMPLETE")
    print("=" * 60)