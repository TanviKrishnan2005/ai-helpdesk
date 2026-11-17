import os

import ollama
from dotenv import load_dotenv
from google import genai

load_dotenv()

AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").strip().lower()

GEMINI_MODEL = "gemini-3.5-flash"
OLLAMA_MODEL = "qwen2.5:3b"

gemini_client = None

if AI_PROVIDER == "gemini":
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured while AI_PROVIDER=gemini."
        )
    gemini_client = genai.Client(api_key=api_key)

elif AI_PROVIDER != "ollama":
    raise RuntimeError(
        f"Unsupported AI_PROVIDER '{AI_PROVIDER}'. Use 'ollama' or 'gemini'."
    )


def generate_ai_response(prompt: str) -> str:
    """Generate text using the provider selected by AI_PROVIDER."""

    if AI_PROVIDER == "ollama":
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
        return response["message"]["content"].strip()

    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )
    return (response.text or "").strip()
