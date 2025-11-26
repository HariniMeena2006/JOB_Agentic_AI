import uuid
import json
import os
from groq import Groq
from dotenv import load_dotenv
import re

# Load env variables
load_dotenv()

PROMPT_FILE = "prompts/email_prompt.txt"

def load_prompt():
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read()

def clean_email(text):
    # Remove images, HTML noise, huge content
    text = re.sub(r"<img[^>]+>", "", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text[:3000]  # prevent 413 error

def classify_email(email_text):
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("❌ GROQ_API_KEY not found in .env file!")

    client = Groq(api_key=api_key)

    system_prompt = load_prompt()

    # Clean long emails
    email_text = clean_email(email_text)

    # Combine system prompt + email
    full_prompt = f"""
{system_prompt}

EMAIL TO CLASSIFY:
{email_text}

You MUST return JSON ONLY. No explanation.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        response_format={"type": "json_object"},  # 🔥 forces valid JSON
        messages=[
            {"role": "system", "content": "You are an email classification engine."},
            {"role": "user", "content": full_prompt}
        ]
    )

    json_text = response.choices[0].message.content

    # Safety parse (but it will always be JSON now)
    return json.loads(json_text)
