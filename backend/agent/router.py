import os
import re

from dotenv import load_dotenv
from groq import Groq


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY is missing from .env"
    )


# ============================================================
# GROQ CLIENT
# ============================================================

client = Groq(
    api_key=GROQ_API_KEY
)


# ============================================================
# ROUTER MODEL
# ============================================================

# Use the lighter model because routing is a classification
# task and does not require the full 120B model.

ROUTER_MODEL = "openai/gpt-oss-20b"


# ============================================================
# VALID ROUTES
# ============================================================

VALID_ROUTES = {
    "WEB",
    "YOUTUBE",
    "PDF",
    "SQL",
    "OCR",
    "GENERAL"
}


# ============================================================
# ROUTER SYSTEM PROMPT
# ============================================================

ROUTER_PROMPT = """
You are the routing brain of AURA,
an AI research and intelligence assistant.

Your ONLY task is to classify the user's query
into EXACTLY ONE route.

VALID ROUTES:

WEB
YOUTUBE
PDF
SQL
OCR
GENERAL


============================================================
WEB
============================================================

Choose WEB when the user needs information from
the current internet or asks about information that
can change over time.

Use WEB for:

- Latest news
- Recent developments
- Current events
- Current company information
- Current product information
- Current prices
- Current status
- Today's information
- This week's information
- Recent announcements
- Real-time information
- Current research/news

Examples:

"What is the latest AI news?"
"What happened in technology today?"
"What are the recent developments in OpenAI?"
"What is the current price of Bitcoin?"
"What happened recently in AI?"
"What are the latest developments in robotics?"


============================================================
YOUTUBE
============================================================

Choose YOUTUBE when the user explicitly wants
YouTube or video content.

This route has HIGH PRIORITY when the user mentions:

- YouTube
- YouTube video
- YouTube videos
- video
- videos
- watch
- tutorial video

Examples:

"Find YouTube videos about RAG."
"Search YouTube for Python tutorials."
"Find videos explaining LangChain."
"Summarize this YouTube video."
"What does this YouTube video say?"
"Give me videos about Agentic AI."
"Find a video explaining neural networks."


IMPORTANT:

If the user explicitly mentions YouTube or asks
for a video, choose YOUTUBE even if the topic is
also current or recent.

For example:

"Find the latest AI news on YouTube."

→ YOUTUBE

NOT WEB.


============================================================
PDF
============================================================

Choose PDF when the user is asking about an uploaded
PDF or document.

Examples:

"Explain my PDF."
"Summarize the uploaded PDF."
"What does my document say?"
"What does the PDF say about transformers?"
"Find information in my uploaded document."
"What are the main points of this PDF?"
"Search my document for machine learning."


IMPORTANT:

Words such as:

- PDF
- document
- uploaded document
- uploaded PDF
- my document
- this document

strongly indicate PDF when the question is about
information contained inside that document.


============================================================
OCR
============================================================

Choose OCR when the user is asking about text
contained inside an uploaded image.

Examples:

"Read this image."
"Extract text from this image."
"What does this screenshot say?"
"Read the text in this image."
"Extract information from this document image."
"What does this screenshot contain?"
"Read this uploaded image."


IMPORTANT:

Choose OCR when the user is referring to an image,
screenshot, photograph, or scanned document and wants
to understand the text inside it.


============================================================
SQL
============================================================

Choose SQL when the user is asking for information
from AURA's structured database.

Examples:

"How many customers do we have?"
"How many employees are there?"
"Show all employees."
"What were the total sales?"
"Show customers from Bangalore."
"Give me the sales records."
"How many customers are in the database?"
"What is the average sales amount?"
"List the employees."


IMPORTANT:

Use SQL only when the question requires structured
database information.

Do NOT choose SQL merely because the question contains
words such as "data", "records", or "information".


============================================================
GENERAL
============================================================

Choose GENERAL when the question can be answered
without using:

- Current web information
- YouTube
- An uploaded PDF
- An uploaded image
- The SQL database


Examples:

"What is machine learning?"
"Explain Python."
"What is an API?"
"What is RAG?"
"Explain neural networks."
"What is generative AI?"
"How does backpropagation work?"
"Explain REST APIs."


============================================================
ROUTING PRIORITY
============================================================

When multiple categories appear possible, use these
rules to resolve the conflict:

1. Explicit YouTube/video request
   → YOUTUBE

2. Explicit uploaded image/screenshot request
   → OCR

3. Explicit uploaded PDF/document request
   → PDF

4. Explicit database/data-record request
   → SQL

5. Current/recent/latest internet information
   → WEB

6. Everything else
   → GENERAL


============================================================
IMPORTANT EXAMPLES
============================================================

"Latest AI news"

→ WEB


"Latest AI news on YouTube"

→ YOUTUBE


"Find a video explaining RAG"

→ YOUTUBE


"What is RAG?"

→ GENERAL


"What does my PDF say about RAG?"

→ PDF


"Read the text in this screenshot"

→ OCR


"How many customers are in the database?"

→ SQL


"What are the latest developments in AI?"

→ WEB


"Explain neural networks"

→ GENERAL


============================================================
OUTPUT RULE
============================================================

Return EXACTLY ONE of:

WEB
YOUTUBE
PDF
SQL
OCR
GENERAL

Do not return:

- explanations
- punctuation
- markdown
- multiple routes
- extra words
- reasoning

Your entire response must be exactly one valid route.
"""


# ============================================================
# CLEAN ROUTER OUTPUT
# ============================================================

def clean_route(
    route: str
) -> str:
    """
    Clean the LLM's routing response and extract a valid
    route when possible.
    """

    if not route:
        return "GENERAL"

    route = route.strip().upper()

    # --------------------------------------------------------
    # Exact valid response
    # --------------------------------------------------------

    if route in VALID_ROUTES:
        return route

    # --------------------------------------------------------
    # Sometimes an LLM may return:
    #
    # "WEB\n"
    # "WEB."
    # "WEB - because..."
    #
    # Extract a standalone valid route.
    # --------------------------------------------------------

    for valid_route in VALID_ROUTES:

        if re.search(
            rf"\b{valid_route}\b",
            route
        ):

            return valid_route

    return "GENERAL"


# ============================================================
# ROUTE QUERY
# ============================================================

def route_query(
    query: str
) -> str:
    """
    Classify a user query into one AURA route.

    Returns one of:

        WEB
        YOUTUBE
        PDF
        SQL
        OCR
        GENERAL
    """

    # --------------------------------------------------------
    # Validate query
    # --------------------------------------------------------

    if not query or not query.strip():

        return "GENERAL"

    query = query.strip()

    print("\n==============================")
    print("AURA ROUTER")
    print("QUERY:", query)
    print("==============================")


    try:

        # ----------------------------------------------------
        # Ask routing model
        # ----------------------------------------------------

        response = client.chat.completions.create(

            model=ROUTER_MODEL,

            messages=[
                {
                    "role": "system",
                    "content": ROUTER_PROMPT
                },
                {
                    "role": "user",
                    "content": query
                }
            ],

            temperature=0
        )

        # ----------------------------------------------------
        # Validate response
        # ----------------------------------------------------

        if not response.choices:

            print(
                "ROUTER ERROR: No response choices."
            )

            return "GENERAL"

        content = (
            response
            .choices[0]
            .message
            .content
        )

        route = clean_route(
            content
        )

        print(
            "ROUTE:",
            route
        )

        return route

    except Exception as e:

        print(
            "ROUTER ERROR:",
            repr(e)
        )

        # Safe fallback.
        # A general response is preferable to accidentally
        # triggering an external or sensitive tool.

        return "GENERAL"