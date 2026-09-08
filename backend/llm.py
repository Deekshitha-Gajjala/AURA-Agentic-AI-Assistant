import os

from dotenv import load_dotenv
from groq import Groq


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

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
# MODEL CONFIGURATION
# ============================================================

# Main model:
# Used for complex reasoning, document answers,
# research synthesis, SQL explanations, etc.
MAIN_MODEL = "openai/gpt-oss-120b"

# Lightweight model:
# Used for routing, classification, and simpler tasks.
LIGHT_MODEL = "openai/gpt-oss-20b"


# ============================================================
# DEFAULT SETTINGS
# ============================================================

DEFAULT_TEMPERATURE = 0.3


# ============================================================
# MAIN LLM
# ============================================================

def ask_llm(
    prompt: str,
    model: str = MAIN_MODEL
) -> str:
    """
    Send a prompt to the configured Groq model.

    Args:
        prompt: User/system instruction sent to the model.
        model: Groq model name.

    Returns:
        Clean text response from the model.

    Raises:
        ValueError: For invalid input or empty response.
        RuntimeError: If the Groq request fails.
    """

    # --------------------------------------------------------
    # Validate prompt
    # --------------------------------------------------------

    if not isinstance(prompt, str):
        raise TypeError(
            "Prompt must be a string."
        )

    prompt = prompt.strip()

    if not prompt:
        raise ValueError(
            "Prompt cannot be empty."
        )

    # --------------------------------------------------------
    # Validate model
    # --------------------------------------------------------

    if not isinstance(model, str):
        raise TypeError(
            "Model name must be a string."
        )

    model = model.strip()

    if not model:
        raise ValueError(
            "Model name cannot be empty."
        )

    # --------------------------------------------------------
    # Groq request
    # --------------------------------------------------------

    try:

        response = client.chat.completions.create(

            model=model,

            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=DEFAULT_TEMPERATURE
        )

    except Exception as e:

        raise RuntimeError(
            "The AI service request failed."
        ) from e

    # --------------------------------------------------------
    # Validate response
    # --------------------------------------------------------

    if not response or not response.choices:

        raise RuntimeError(
            "The AI service returned an empty response."
        )

    message = response.choices[0].message

    if not message or not message.content:

        raise RuntimeError(
            "The AI service returned no usable content."
        )

    result = message.content.strip()

    if not result:

        raise RuntimeError(
            "The AI service returned an empty response."
        )

    return result


# ============================================================
# LIGHT LLM
# ============================================================

def ask_light_llm(
    prompt: str
) -> str:
    """
    Use the lightweight model for simpler tasks such as
    routing and classification.
    """

    return ask_llm(
        prompt=prompt,
        model=LIGHT_MODEL
    )


# ============================================================
# HEALTH CHECK
# ============================================================

def check_llm_configuration() -> dict:
    """
    Return the current LLM configuration without exposing
    the API key.
    """

    return {
        "provider": "Groq",
        "main_model": MAIN_MODEL,
        "light_model": LIGHT_MODEL,
        "api_key_configured": bool(GROQ_API_KEY)
    }


# ============================================================
# SCRIPT ENTRY POINT
# ============================================================

if __name__ == "__main__":

    config = check_llm_configuration()

    print("AURA LLM configuration:")
    print(f"Provider: {config['provider']}")
    print(f"Main model: {config['main_model']}")
    print(f"Light model: {config['light_model']}")
    print(
        f"API key configured: "
        f"{config['api_key_configured']}"
    )