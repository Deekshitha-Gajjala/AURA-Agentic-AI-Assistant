import os
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from groq import Groq


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# ============================================================
# CONFIGURATION
# ============================================================

MODEL = "openai/gpt-oss-120b"

# AURA is primarily being used in the Indian context.
TIMEZONE = "Asia/Kolkata"


# ============================================================
# GROQ CLIENT
# ============================================================

if not GROQ_API_KEY:

    raise ValueError(
        "GROQ_API_KEY is missing from .env"
    )

client = Groq(
    api_key=GROQ_API_KEY
)


# ============================================================
# GET CURRENT DATE
# ============================================================

def get_current_date() -> str:
    """
    Return the current date in AURA's configured timezone.
    """

    current_datetime = datetime.now(
        ZoneInfo(TIMEZONE)
    )

    return current_datetime.strftime(
        "%B %d, %Y"
    )


# ============================================================
# WEB SEARCH
# ============================================================

def web_search(query: str) -> str:
    """
    Search the web using Groq's browser search tool and
    generate a concise research-oriented answer.

    The function returns the LLM's final text response.
    """

    # --------------------------------------------------------
    # Validate query
    # --------------------------------------------------------

    if not query or not query.strip():

        return (
            "Please provide a question or topic "
            "to search for."
        )

    query = query.strip()

    # --------------------------------------------------------
    # Current date
    # --------------------------------------------------------

    current_date = get_current_date()

    print("\n==============================")
    print("AURA WEB SEARCH")
    print("QUERY:", query)
    print("DATE:", current_date)
    print("==============================")

    # --------------------------------------------------------
    # System instructions
    # --------------------------------------------------------

    system_prompt = f"""
You are AURA, an AI research and web intelligence assistant.

Today's date is {current_date}.

Your job is to answer the user's question using
current web information when web search is appropriate.

============================================================
CURRENT INFORMATION RULES
============================================================

1. Treat {current_date} as today's date.

2. When the user asks for:
   - latest
   - recent
   - current
   - today
   - this week
   - this month
   - newest
   - breaking
   - recent developments
   - recent news
   - current status

   prioritize the newest reliable information available
   through web search.

3. Never present old information as if it were current.

4. Pay attention to publication dates and event dates.

5. For latest/current questions, explicitly mention
   important dates when they help establish freshness.

6. Prefer primary sources and authoritative sources when
   they are available.

7. Use reputable secondary sources when primary sources
   are unavailable or insufficient.

8. If sources disagree, acknowledge the disagreement
   instead of silently choosing one.

9. If current information cannot be verified, clearly say so.

10. Never invent:
    - events
    - dates
    - statistics
    - companies
    - products
    - announcements
    - research papers
    - people
    - sources

============================================================
SOURCE QUALITY
============================================================

Prefer information from:

- Official government websites
- Official company websites
- Official documentation
- Research institutions
- Academic sources
- Established news organizations
- Direct announcements
- Original reports

Use secondary sources mainly for additional context.

============================================================
ANSWERING RULES
============================================================

- Give the direct answer first.
- Then provide the most important supporting information.
- Mention relevant dates.
- Keep the response concise but useful.
- Use headings when they improve readability.
- Use bullet points for multiple developments.
- Use a table only when it genuinely improves clarity.
- Distinguish current information from historical context.
- Do not create a large historical overview unless the user
  asks for one.
- Do not claim that information is current unless the web
  search supports that conclusion.
- Do not mention internal tool mechanics.
- Do not say that you "used a browser search" unless it is
  directly relevant to the user's question.

============================================================
RESEARCH BEHAVIOR
============================================================

For research questions:

1. Identify the main subject.
2. Search for relevant current information.
3. Prefer recent and authoritative sources.
4. Compare important information when necessary.
5. Remove obvious irrelevant information.
6. Produce a concise synthesis rather than simply listing
   search results.

For news/current-events questions:

- Focus on developments that are actually recent.
- Include dates.
- Separate confirmed facts from uncertainty.
- Avoid outdated background information unless needed
  for understanding the current event.

The final answer should be accurate, current, clear,
and useful to the user.
"""

    # --------------------------------------------------------
    # Perform web search
    # --------------------------------------------------------

    try:

        response = client.chat.completions.create(

            model=MODEL,

            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": query
                }
            ],

            tools=[
                {
                    "type": "browser_search"
                }
            ]
        )

        # ----------------------------------------------------
        # Extract response
        # ----------------------------------------------------

        if not response.choices:

            return (
                "I couldn't get a response from "
                "the web search."
            )

        message = response.choices[0].message

        answer = message.content

        if not answer:

            return (
                "I couldn't generate an answer from "
                "the available web information."
            )

        answer = answer.strip()

        if not answer:

            return (
                "I couldn't generate an answer from "
                "the available web information."
            )

        print(
            "WEB SEARCH COMPLETED"
        )

        return answer

    except Exception as e:

        print(
            "WEB SEARCH ERROR:",
            repr(e)
        )

        return (
            "I couldn't complete the web search right now. "
            "Please try again."
        )