# LLM client calls to Groq's API

import os
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env", override=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def call_llm(prompt: str, temperature: float = 0.1) -> str:
    
    # Send a prompt to Groq and return the response text
    # we chose low temperature because we want consistent less creative output
    
    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY not set. Get one free at https://console.groq.com/keys "
            "and add it to your .env file."
        )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": 1024,
    }

    resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)

    if resp.status_code != 200:
        raise RuntimeError(f"Groq API error {resp.status_code}: {resp.text}")

    data = resp.json()
    return data["choices"][0]["message"]["content"]