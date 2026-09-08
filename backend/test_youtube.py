import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def route_query(query: str) -> str:

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",

        messages=[
            {
                "role": "system",
                "content": """
You are the routing brain of AURA, an AI research assistant.

Classify the user's query into exactly ONE of these categories:

WEB
YOUTUBE
PDF
SQL
OCR
GENERAL

WEB:
Questions requiring current or recent information from the internet.

Examples:
- Latest AI news
- What happened today?
- Latest developments in OpenAI
- Current stock price

YOUTUBE:
Questions specifically asking for information, videos, news,
explanations, tutorials, or content from YouTube.

Examples:
- Find YouTube videos about generative AI
- Search YouTube for latest AI news
- Explain this YouTube video
- Summarize this YouTube video
- Find tutorials on LangChain on YouTube
- What are people saying about AI on YouTube?

PDF:
Questions about documents uploaded by the user.

Examples:
- Explain my PDF
- Summarize the uploaded document
- What does page 5 say?

SQL:
Questions requiring structured database information.

Examples:
- How many customers do we have?
- What were total sales?
- Show employees from Bangalore

OCR:
Questions about text or information contained inside an uploaded image.

Examples:
- Read this image
- Extract text from this screenshot
- What does this document image say?

GENERAL:
Normal questions that do not require external tools.

Examples:
- What is machine learning?
- Explain Python
- What is an API?

IMPORTANT:
If the user explicitly mentions YouTube or asks to search/find/summarize
YouTube content, classify it as YOUTUBE.

Return ONLY the category name.
"""
            },
            {
                "role": "user",
                "content": query
            }
        ],

        temperature=0
    )

    return response.choices[0].message.content.strip().upper()