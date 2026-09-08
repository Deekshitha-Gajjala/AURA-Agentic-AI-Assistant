# ============================================================
# AURA - MAIN AGENT
# ============================================================

from agent.router import route_query

from tools.web_search import web_search
from tools.pdf_qa import answer_from_pdf
from tools.sql_tool import answer_from_sql
from tools.ocr_tool import answer_from_image

from tools.youtube_tool import (
    search_youtube,
    get_youtube_transcript
)

from llm import (
    ask_llm,
    ask_light_llm
)

from database.memory_db import (
    get_memory_context
)


# ============================================================
# SELECT BEST YOUTUBE VIDEO
# ============================================================

def select_best_youtube_video(
    query: str,
    videos: list
):

    if not videos:
        return None

    video_information = []

    for index, video in enumerate(
        videos
    ):

        video_information.append(
            f"""
VIDEO {index + 1}

Title:
{video.get("title", "")}

Channel:
{video.get("channel", "")}

Published:
{video.get("published_at", "")}

Description:
{video.get("description", "")}
"""
        )

    videos_text = "\n".join(
        video_information
    )

    prompt = f"""
You are the YouTube video selection
component of AURA.

The user asked:

{query}

Below are YouTube search results:

{videos_text}

Choose the SINGLE video that is most
relevant to the user's question.

Consider:

1. Relevance to the exact question.
2. Whether the title matches the topic.
3. Whether the description matches the topic.
4. Recency when the user asks for latest
   or recent information.
5. Prefer actual news/update videos when
   the user asks for news.
6. Prefer educational/tutorial videos when
   the user asks to learn.
7. Do not choose a video simply because
   it has a transcript.

Return ONLY the video number.

Example:

1
"""

    try:

        result = ask_light_llm(
            prompt
        ).strip()

        number = int(
            result
        )

        if 1 <= number <= len(videos):

            return videos[
                number - 1
            ]

    except Exception:

        pass

    # Safe fallback

    return videos[0]


# ============================================================
# ANSWER FROM YOUTUBE
# ============================================================

def answer_from_youtube(
    query: str
) -> str:

    print("\n")
    print("=" * 60)
    print("AURA YOUTUBE AGENT")
    print("=" * 60)

    print(
        "Searching YouTube for:",
        query
    )

    # --------------------------------------------------------
    # STEP 1: SEARCH YOUTUBE
    # --------------------------------------------------------

    search_result = search_youtube(
        query,
        max_results=10
    )

    if not search_result.get(
        "success"
    ):

        return (
            "I couldn't search YouTube right now. "
            + search_result.get(
                "message",
                ""
            )
        )

    videos = search_result.get(
        "videos",
        []
    )

    if not videos:

        return (
            "I couldn't find relevant "
            "YouTube videos."
        )

    print(
        "YouTube videos found:",
        len(videos)
    )

    # --------------------------------------------------------
    # STEP 2: SELECT BEST VIDEO
    # --------------------------------------------------------

    selected_video = (
        select_best_youtube_video(
            query,
            videos
        )
    )

    if not selected_video:

        return (
            "I couldn't select a relevant "
            "YouTube video."
        )

    print(
        "Selected video:",
        selected_video.get(
            "title",
            ""
        )
    )

    # --------------------------------------------------------
    # STEP 3: GET TRANSCRIPT
    # --------------------------------------------------------

    transcript_result = (
        get_youtube_transcript(
            selected_video["video_id"]
        )
    )

    # --------------------------------------------------------
    # NO TRANSCRIPT
    # --------------------------------------------------------

    if not transcript_result.get(
        "success"
    ):

        lines = []

        lines.append(
            "I found this relevant "
            "YouTube video, but a transcript "
            "was not available."
        )

        lines.append(
            f"\nTitle: "
            f"{selected_video['title']}"
        )

        lines.append(
            f"Channel: "
            f"{selected_video['channel']}"
        )

        lines.append(
            f"URL: "
            f"{selected_video['url']}"
        )

        lines.append(
            "\nOther relevant videos:"
        )

        for number, video in enumerate(
            videos[:5],
            start=1
        ):

            lines.append(
                f"\n{number}. "
                f"{video['title']}"
            )

            lines.append(
                f"Channel: "
                f"{video['channel']}"
            )

            lines.append(
                f"URL: "
                f"{video['url']}"
            )

        return "\n".join(
            lines
        )

    # --------------------------------------------------------
    # GET TRANSCRIPT
    # --------------------------------------------------------

    transcript = (
        transcript_result.get(
            "transcript",
            ""
        )
    )

    language = (
        transcript_result.get(
            "language",
            "Unknown"
        )
    )

    language_code = (
        transcript_result.get(
            "language_code",
            "unknown"
        )
    )

    if not transcript:

        return (
            "The YouTube video has a "
            "transcript, but I couldn't "
            "read its contents."
        )

    print(
        "Transcript characters:",
        len(transcript)
    )

    # --------------------------------------------------------
    # LIMIT TRANSCRIPT SIZE
    # --------------------------------------------------------

    MAX_TRANSCRIPT_CHARACTERS = 12000

    transcript_for_llm = (
        transcript[
            :MAX_TRANSCRIPT_CHARACTERS
        ]
    )

    was_truncated = (
        len(transcript)
        > MAX_TRANSCRIPT_CHARACTERS
    )

    # --------------------------------------------------------
    # STEP 4: FINAL AI ANSWER
    # --------------------------------------------------------

    prompt = f"""
You are AURA, an AI research assistant.

The user asked:

{query}

A relevant YouTube video was selected.

VIDEO TITLE:
{selected_video["title"]}

CHANNEL:
{selected_video["channel"]}

PUBLISHED:
{selected_video.get(
    "published_at",
    "Unknown"
)}

VIDEO URL:
{selected_video["url"]}

TRANSCRIPT LANGUAGE:
{language}

TRANSCRIPT LANGUAGE CODE:
{language_code}

VIDEO TRANSCRIPT:

{transcript_for_llm}

TASK:

Answer the user's question using
the YouTube transcript.

IMPORTANT RULES:

1. Use only information supported
   by the transcript.

2. Do not invent facts.

3. Clearly summarize the important
   information.

4. Keep the answer useful and easy
   to understand.

5. If the transcript does not contain
   enough information, say that clearly.

6. If the transcript discusses multiple
   topics, focus only on topics relevant
   to the user's question.

7. Do not mention internal AURA
   implementation details.

8. Do not claim information that is not
   supported by the transcript.

9. If the user asks for the latest news,
   clearly distinguish information stated
   in the video from your own knowledge.

At the end, provide:

YouTube Source:

Video title
Channel
URL
Transcript language
"""

    try:

        answer = ask_llm(
            prompt
        )

    except Exception as e:

        print(
            "YOUTUBE FINAL LLM ERROR:",
            repr(e)
        )

        return (
            "I found the YouTube video and "
            "transcript, but I couldn't "
            "generate the final answer right now. "
            f"Error: {str(e)}"
        )

    if not answer:

        answer = (
            "I couldn't generate an answer "
            "from the YouTube transcript."
        )

    # --------------------------------------------------------
    # ADD SOURCE
    # --------------------------------------------------------

    answer += (

        "\n\n"
        "YouTube Source:\n"

        f"{selected_video['title']}\n"

        f"Channel: "
        f"{selected_video['channel']}\n"

        f"URL: "
        f"{selected_video['url']}\n"

        f"Transcript language: "
        f"{language}"
    )

    if was_truncated:

        answer += (

            "\n\n"
            "Note: The video transcript was "
            "longer than the current processing "
            "limit, so the answer was generated "
            "from the first portion of the "
            "transcript."
        )

    print(
        "YouTube answer generated successfully."
    )

    print("=" * 60)

    return answer


# ============================================================
# MAIN AGENT
# ============================================================

def run_agent(
    query: str,
    image_path: str = None,
    user_id: int = None,
    document_filename: str = None
):
    """Route a user query to the appropriate AURA tool and return the answer."""

    if not isinstance(query, str) or not query.strip():
        return {
            "route": "GENERAL",
            "answer": "Please enter a question."
        }

    query = query.strip()

    print("\n")
    print("=" * 60)
    print("AURA AGENT STARTED")
    print("=" * 60)

    print(
        "User ID:",
        user_id
    )

    print(
        "Query:",
        query
    )

    print(
        "Selected document:",
        document_filename
    )

    # --------------------------------------------------------
    # LOAD MEMORY
    # --------------------------------------------------------

    memory = ""
    if user_id is not None:
        try:
            memory = get_memory_context(
                user_id=user_id,
                limit=5
            ) or ""
        except Exception as e:
            print("MEMORY ERROR:", repr(e))

    # --------------------------------------------------------
    # ROUTE QUERY
    # --------------------------------------------------------

    route = route_query(
        query
    )

    print(
        "Selected route:",
        route
    )

    # ========================================================
    # WEB
    # ========================================================

    if route == "WEB":

        print(
            "Running WEB tool..."
        )

        answer = web_search(
            query
        )

    # ========================================================
    # YOUTUBE
    # ========================================================

    elif route == "YOUTUBE":

        print(
            "Running YOUTUBE tool..."
        )

        answer = answer_from_youtube(
            query
        )

    # ========================================================
    # PDF
    # ========================================================

    elif route == "PDF":

        print(
            "Running PDF tool..."
        )

        # ----------------------------------------------------
        # IMPORTANT
        # ----------------------------------------------------
        # The PDF tool now searches only one
        # selected document.
        # ----------------------------------------------------

        if not document_filename:

            answer = (
                "Please select the PDF you want "
                "me to search before asking a "
                "question about a document."
            )

        else:

            print(
                "Searching PDF:",
                document_filename
            )

            answer = answer_from_pdf(
                query,
                document_filename
            )

    # ========================================================
    # SQL
    # ========================================================

    elif route == "SQL":

        print(
            "Running SQL tool..."
        )

        result = answer_from_sql(
            query,
            user_id=user_id
        )

        if isinstance(result, dict):
            answer = result.get("answer", "")
        else:
            answer = str(result) if result is not None else ""

    # ========================================================
    # OCR
    # ========================================================

    elif route == "OCR":

        print(
            "Running OCR tool..."
        )

        if not image_path:

            answer = (
                "Please upload an image "
                "so I can analyze it."
            )

        else:

            answer = answer_from_image(
                query,
                image_path
            )

    # ========================================================
    # GENERAL
    # ========================================================

    elif route == "GENERAL":

        print(
            "Running GENERAL LLM..."
        )

        if memory:

            prompt = f"""
You are AURA, an intelligent AI assistant.

You have access to this user's recent
conversation history.

RECENT CONVERSATION:

{memory}

CURRENT USER QUESTION:

{query}

Use the previous conversation only
when it helps understand the current
question.

RULES:

- Answer the current question directly.
- Use previous conversation for context
  when relevant.
- Do not mention that you are using memory.
- Do not repeat the entire conversation.
- Do not invent information.
- If the current question is unrelated
  to previous messages, answer it normally.
"""

            answer = ask_llm(
                prompt
            )

        else:

            answer = ask_llm(
                query
            )

    # ========================================================
    # FALLBACK
    # ========================================================

    else:

        print(
            "Unknown route. Using GENERAL."
        )

        route = "GENERAL"

        answer = ask_llm(
            query
        )

    # ========================================================
    # RETURN RESULT
    # ========================================================

    if not answer:
        answer = "AURA could not generate an answer."

    print(
        "AURA AGENT COMPLETE"
    )

    print(
        "Final route:",
        route
    )

    print("=" * 60)

    return {
        "route": route,
        "answer": answer
    }