from tools.pdf_tool import search_document
from llm import ask_llm


# ============================================================
# SEARCH PDF
# ============================================================

def search_pdf(
    question: str,
    filename: str,
    top_k: int = 5
):
    """
    Search for relevant content inside one specific PDF.
    """

    if not filename:
        return {
            "success": False,
            "message": "Please select a PDF first."
        }

    if not question or not question.strip():
        return {
            "success": False,
            "message": "Please enter a question."
        }

    # --------------------------------------------------------
    # Search the document
    # --------------------------------------------------------

    tool_result = search_document(
        query=question,
        filename=filename,
        top_k=top_k
    )

    # --------------------------------------------------------
    # Handle search failure
    # --------------------------------------------------------

    if not tool_result.get("success"):
        return {
            "success": False,
            "message": tool_result.get(
                "message",
                "I couldn't search this PDF."
            )
        }

    # --------------------------------------------------------
    # Extract ACTUAL results
    # --------------------------------------------------------

    results = tool_result.get(
        "results",
        []
    )

    if not results:
        return {
            "success": False,
            "message": (
                "I couldn't find relevant information "
                "in this PDF."
            )
        }

    return {
        "success": True,
        "filename": tool_result.get(
            "filename",
            filename
        ),
        "results": results
    }


# ============================================================
# ANSWER FROM PDF
# ============================================================

def answer_from_pdf(
    question: str,
    filename: str = None
):
    """
    Answer a user's question using only the
    relevant content retrieved from a PDF.
    """

    if not filename:
        return (
            "Please select the PDF you want me to search "
            "before asking a question about a document."
        )

    # --------------------------------------------------------
    # Search PDF
    # --------------------------------------------------------

    search_result = search_pdf(
        question=question,
        filename=filename,
        top_k=5
    )

    if not search_result["success"]:
        return search_result["message"]

    results = search_result["results"]

    # --------------------------------------------------------
    # Build context
    # --------------------------------------------------------

    context_parts = []

    for result in results:

        page = result.get(
            "page",
            "Unknown"
        )

        text = result.get(
            "text",
            ""
        ).strip()

        if not text:
            continue

        context_parts.append(
            f"[Page {page}]\n{text}"
        )

    if not context_parts:
        return (
            "I couldn't find readable information "
            "in the selected PDF."
        )

    context = "\n\n".join(
        context_parts
    )

    # --------------------------------------------------------
    # LLM PROMPT
    # --------------------------------------------------------

    prompt = f"""
You are AURA, a helpful document question-answering assistant.

The user is asking a question about a specific PDF.

USER QUESTION:
{question}

DOCUMENT:
{filename}

RELEVANT CONTENT FROM THE PDF:
{context}

Instructions:

1. Answer the user's question directly.
2. Use ONLY the information provided in the document content.
3. Do not invent information.
4. If the user asks what the PDF is about, give a clear 2-4 sentence overview.
5. If useful, follow the overview with 3-5 short bullet points.
6. Use simple, natural language.
7. Avoid unnecessary phrases such as:
   - "The PDF discusses..."
   - "Based on the provided context..."
   - "According to the retrieved information..."
8. Do not repeat the same idea multiple times.
9. Do not mention retrieval, embeddings, chunks, vector databases, or internal AI processes.
10. If the document content does not contain enough information to answer the question, clearly say so.
11. Do not make assumptions beyond the provided document content.
12. Do NOT add citations inside the main explanation. Sources will be added separately.

Give the clearest answer possible.
"""

    # --------------------------------------------------------
    # Generate answer
    # --------------------------------------------------------

    try:

        answer = ask_llm(
            prompt
        ).strip()

    except Exception as e:

        print(
            "PDF LLM ERROR:",
            repr(e)
        )

        return (
            "I found relevant information in the PDF, "
            "but I couldn't generate the answer right now."
        )

    # --------------------------------------------------------
    # Build source list
    # --------------------------------------------------------

    sources = []

    for result in results:

        page = result.get(
            "page",
            "Unknown"
        )

        source = (
            f"{filename} — Page {page}"
        )

        if source not in sources:
            sources.append(
                source
            )

    # Maximum five source references
    sources = sources[:5]

    # --------------------------------------------------------
    # Final answer
    # --------------------------------------------------------

    final_answer = answer

    if sources:

        final_answer += (
            "\n\n**Sources**\n"
        )

        for source in sources:

            final_answer += (
                f"- {source}\n"
            )

    return final_answer