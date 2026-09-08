import os

from tools.tts_tool import text_to_speech


# ============================================================
# OUTPUT DIRECTORY
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "uploads",
    "audio"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# TEST TEXT
# ============================================================

text = (
    "Hello Deekshitha. "
    "I am AURA, your AI research assistant."
)


# ============================================================
# OUTPUT FILE
# ============================================================

output_path = os.path.join(
    OUTPUT_DIR,
    "aura_test.wav"
)


# ============================================================
# GENERATE AUDIO
# ============================================================

result = text_to_speech(
    text=text,
    output_path=output_path
)


# ============================================================
# RESULT
# ============================================================

print("\n")
print("=" * 60)
print("TTS TEST COMPLETE")
print("=" * 60)

print(
    "Audio file:",
    result
)

print(
    "Exists:",
    os.path.exists(result)
)

print("=" * 60)