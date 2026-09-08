import os
import base64
import traceback

import pytesseract
from PIL import Image, ImageOps, UnidentifiedImageError
from groq import Groq

from llm import ask_llm
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# TESSERACT CONFIGURATION
# ============================================================

TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]

for tesseract_path in TESSERACT_PATHS:
    if os.path.isfile(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        break

MAX_OCR_TEXT_LENGTH = 12000
MAX_IMAGE_FILE_SIZE_MB = 15
MAX_IMAGE_PIXELS = 25_000_000
ALLOWED_IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"
}

VISION_MODEL = "qwen/qwen3.6-27b"

client = Groq(api_key=os.getenv("GROQ_API_KEY")) if os.getenv("GROQ_API_KEY") else None


def validate_image_path(image_path: str) -> None:
    if not image_path:
        raise ValueError("Image path was not provided.")
    if not os.path.exists(image_path):
        raise FileNotFoundError("Image file not found.")
    if not os.path.isfile(image_path):
        raise ValueError("The provided image path is not a valid file.")

    extension = os.path.splitext(image_path)[1].lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError(
            "Unsupported image format. Please upload a JPG, JPEG, PNG, BMP, TIFF, or WEBP image."
        )

    file_size = os.path.getsize(image_path)
    if file_size <= 0:
        raise ValueError("The uploaded image file is empty.")

    max_bytes = MAX_IMAGE_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise ValueError(
            f"Image file is too large. Maximum size is {MAX_IMAGE_FILE_SIZE_MB} MB."
        )


def extract_text_from_image(image_path: str) -> str:
    try:
        validate_image_path(image_path)

        with Image.open(image_path) as image:
            image.verify()

        with Image.open(image_path) as image:
            width, height = image.size
            if width * height > MAX_IMAGE_PIXELS:
                return "The image resolution is too large for OCR. Please upload a smaller image."

            image.load()
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")

            gray_image = ImageOps.grayscale(image)
            gray_image = ImageOps.autocontrast(gray_image)
            text = pytesseract.image_to_string(gray_image, config="--psm 6").strip()

        if not text:
            return "No readable text was found in the image."

        if len(text) > MAX_OCR_TEXT_LENGTH:
            text = text[:MAX_OCR_TEXT_LENGTH] + "\n\n[OCR text truncated.]"

        return text

    except pytesseract.TesseractNotFoundError:
        return "OCR is not available because Tesseract is not installed or could not be found."
    except FileNotFoundError as e:
        return str(e)
    except (UnidentifiedImageError, OSError):
        return "The uploaded file could not be read as a valid image."
    except ValueError as e:
        return str(e)
    except Exception as e:
        return f"OCR failed: {str(e)}"


def _encode_image(image_path: str) -> str:
    validate_image_path(image_path)
    extension = os.path.splitext(image_path)[1].lower()
    mime = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".bmp": "image/bmp",
        ".tif": "image/tiff",
        ".tiff": "image/tiff",
        ".webp": "image/webp",
    }[extension]

    with open(image_path, "rb") as file:
        encoded = base64.b64encode(file.read()).decode("utf-8")

    return f"data:{mime};base64,{encoded}"


def _is_context_question(question: str) -> bool:
    q = question.lower().strip()
    context_terms = (
        "what is this picture",
        "what is this image",
        "what is the picture about",
        "what is the image about",
        "picture about",
        "image about",
        "context of this",
        "context of the picture",
        "context of the image",
        "what's happening",
        "what is happening",
        "describe this picture",
        "describe this image",
    )
    return any(term in q for term in context_terms)


def analyze_image_with_vision(
    question: str,
    image_path: str,
    extracted_text: str = ""
) -> str:
    if client is None:
        raise RuntimeError("GROQ_API_KEY is not configured.")

    image_data_url = _encode_image(image_path)
    context_mode = _is_context_question(question)

    if context_mode:
        instruction = """
The user wants the CONTEXT of the image, not an exhaustive visual inventory.
Respond in exactly 2 or 3 short sentences.
Sentence 1: say what the image is mainly about / what is happening.
Sentence 2: give the most important event, subject, or context.
Sentence 3: only if useful, mention a clearly visible or highly reliable year/date or other key detail.
Do not list every person, object, color, logo, background element, or piece of text.
If a year is not visible and cannot be identified with high confidence, do not invent one.
"""
    else:
        instruction = """
Answer the user's specific question directly in no more than 3 short sentences.
Only mention visual details that help answer the question.
Do not produce an exhaustive description of the image.
"""

    ocr_context = extracted_text if extracted_text and not extracted_text.startswith("No readable text") else "No useful OCR text was extracted."

    system_prompt = f"""
You are AURA's concise multimodal image assistant.
You can actually inspect the uploaded image.

{instruction}

Use the image as the primary source. OCR text is supplementary and may contain errors:
---
{ocr_context}
---

Do not invent facts. When something is uncertain, say so briefly.
Do not identify real people by name. Teams, sports events, organizations, places, objects, and public events may be described when clearly supported by the image.
"""

    response = client.chat.completions.create(
        model=VISION_MODEL,
        temperature=0.2,
        max_completion_tokens=350,
        reasoning_effort="none",
        reasoning_format="hidden",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question.strip()},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_data_url}
                    }
                ]
            }
        ]
    )

    answer = response.choices[0].message.content or ""
    answer = answer.strip()
    if not answer:
        raise RuntimeError("The vision model returned an empty response.")

    return answer


def answer_from_image(question: str, image_path: str) -> str:
    if not question or not question.strip():
        return "Please enter a question about the image."

    question = question.strip()
    extracted_text = extract_text_from_image(image_path)

    error_prefixes = (
        "Image path was not provided.",
        "Image file not found.",
        "The provided image path is not a valid file.",
        "Unsupported image format.",
        "The uploaded image file is empty.",
        "Image file is too large.",
        "The image resolution is too large for OCR.",
        "The uploaded file could not be read as a valid image.",
        "OCR failed:",
        "OCR is not available",
    )

    if extracted_text.startswith(error_prefixes):
        return extracted_text

    try:
        return analyze_image_with_vision(
            question=question,
            image_path=image_path,
            extracted_text=extracted_text
        )
    except Exception as vision_error:
        # If vision is temporarily unavailable, use OCR for text-specific questions.
        # This keeps the feature useful without pretending OCR can understand the whole scene.
        print("VISION ERROR:", vision_error)
        if extracted_text and not extracted_text.startswith("No readable text"):
            prompt = f"""
You are AURA. Answer this question using the OCR text below.
Keep the response to 2 or 3 short sentences. Do not list every extracted detail.
Question: {question}
OCR text:
{extracted_text}
"""
            try:
                answer = ask_llm(prompt)
                return answer.strip()
            except Exception:
                pass

        return "I could not analyze the image right now. Please try again."


if __name__ == "__main__":
    print("AURA OCR + Vision tool loaded successfully.")
    print(f"Vision model: {VISION_MODEL}")
    print(f"Maximum OCR text length: {MAX_OCR_TEXT_LENGTH}")
    print(f"Maximum image size: {MAX_IMAGE_FILE_SIZE_MB} MB")
