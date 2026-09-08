import os
from typing import Union

from pypdf import PdfReader

from llm import ask_llm


# ============================================================
# CONFIGURATION
# ============================================================

MIN_QUESTIONS = 1
MAX_QUESTIONS = 10
MAX_PDF_CHARACTERS = 18000


# ============================================================
# EXTRACT TEXT FROM PDF
# ============================================================

def extract_pdf_text(pdf_path: str) -> str:
    """
    Extract readable text from all pages of a PDF.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Extracted and cleaned PDF text.

    Raises:
        FileNotFoundError: If the PDF does not exist.
        ValueError: If the PDF cannot be read.
    """

    if not pdf_path:
        raise ValueError("PDF path is required.")

    if not isinstance(pdf_path, str):
        raise TypeError("PDF path must be a string.")

    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(
            f"PDF file not found: {pdf_path}"
        )

    try:
        reader = PdfReader(pdf_path)

        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:
                raise ValueError(
                    "This PDF is password-protected and cannot be read."
                )

        pages = []

        for page in reader.pages:
            try:
                text = page.extract_text()
            except Exception:
                continue

            if text:
                text = text.strip()

                if text:
                    pages.append(text)

        return "\n\n".join(pages).strip()

    except ValueError:
        raise

    except Exception as e:
        raise ValueError(
            f"Unable to read the PDF: {str(e)}"
        ) from e


# ============================================================
# VALIDATE QUESTION COUNT
# ============================================================

def _validate_question_count(
    number_of_questions: Union[int, str]
) -> int:
    """
    Validate and normalize the requested number of questions.
    """

    try:
        number_of_questions = int(number_of_questions)
    except (TypeError, ValueError):
        raise ValueError(
            "Number of questions must be a valid integer."
        )

    if not (
        MIN_QUESTIONS
        <= number_of_questions
        <= MAX_QUESTIONS
    ):
        raise ValueError(
            f"Number of questions must be between "
            f"{MIN_QUESTIONS} and {MAX_QUESTIONS}."
        )

    return number_of_questions


# ============================================================
# GENERATE QUIZ
# ============================================================

def generate_pdf_quiz(
    pdf_path: str,
    number_of_questions: int = 5
) -> str:
    """
    Generate a multiple-choice quiz from a PDF.

    The quiz is generated only from information extracted
    from the provided PDF.
    """

    # --------------------------------------------------------
    # Validate question count
    # --------------------------------------------------------

    try:
        number_of_questions = _validate_question_count(
            number_of_questions
        )
    except ValueError as e:
        return str(e)

    # --------------------------------------------------------
    # Extract PDF text
    # --------------------------------------------------------

    try:
        text = extract_pdf_text(pdf_path)

    except FileNotFoundError:
        return "I couldn't find the PDF file."

    except ValueError as e:
        return f"I couldn't read this PDF: {str(e)}"

    except Exception:
        return "I couldn't read this PDF."

    # --------------------------------------------------------
    # Empty PDF check
    # --------------------------------------------------------

    if not text:
        return (
            "I couldn't extract readable text "
            "from this PDF."
        )

    # --------------------------------------------------------
    # Limit text sent to the LLM
    # --------------------------------------------------------

    was_truncated = (
        len(text) > MAX_PDF_CHARACTERS
    )

    if was_truncated:
        text = text[:MAX_PDF_CHARACTERS]

    # --------------------------------------------------------
    # Create prompt
    # --------------------------------------------------------

    prompt = f"""
You are AURA, an AI document quiz generator.

Create a multiple-choice quiz using ONLY the
information contained in the provided PDF content.

PDF CONTENT:
{text}

Generate EXACTLY {number_of_questions} questions.

For every question use this exact structure:

Question 1:
<question>

A. <option A>
B. <option B>
C. <option C>
D. <option D>

Correct Answer:
<letter>

Explanation:
<short explanation>

Question 2:
<question>

A. <option A>
B. <option B>
C. <option C>
D. <option D>

Correct Answer:
<letter>

Explanation:
<short explanation>

Continue until EXACTLY
{number_of_questions} questions are generated.

IMPORTANT RULES:

1. Use ONLY information explicitly available in the PDF content.
2. Do not use outside knowledge.
3. Do not invent facts.
4. Every question must be answerable from the PDF.
5. Every question must have exactly four options.
6. Only one option should be correct.
7. The correct answer must be supported by the PDF.
8. Avoid duplicate or nearly identical questions.
9. Cover different parts of the document when possible.
10. Keep explanations short and clear.
11. Do not use markdown tables.
12. Do not include an introduction.
13. Do not include a conclusion.
14. Do not add extra questions.
15. Generate EXACTLY {number_of_questions} questions.
16. Follow the requested format exactly.
"""

    # --------------------------------------------------------
    # Generate quiz
    # --------------------------------------------------------

    try:
        quiz = ask_llm(prompt)

    except Exception:
        return (
            "I couldn't generate the quiz right now. "
            "Please try again."
        )

    # --------------------------------------------------------
    # Validate response
    # --------------------------------------------------------

    if not quiz or not quiz.strip():
        return (
            "I couldn't generate a quiz "
            "from this PDF."
        )

    quiz = quiz.strip()

    # --------------------------------------------------------
    # Large PDF notice
    # --------------------------------------------------------

    if was_truncated:
        quiz += (
            "\n\nNote: This PDF is larger than the "
            "current processing limit, so the quiz "
            "was generated from the first portion "
            "of the document."
        )

    return quiz


# ============================================================
# SCRIPT ENTRY POINT
# ============================================================

if __name__ == "__main__":
    print(
        "pdf_quiz.py provides the generate_pdf_quiz() "
        "function and is not intended to be run directly."
    )