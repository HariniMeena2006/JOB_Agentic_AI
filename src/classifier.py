# classifier.py
import os
import re
import uuid
import json
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

PROMPT_FILE = "prompts/email_prompt.txt"

def load_prompt():
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read()

def clean_email(text):
    """Clean email text from HTML, images, links, excessive whitespace"""
    text = re.sub(r"<img[^>]+>", "", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text[:3000]  # Limit length to avoid API errors

def classify_email(email_text):
    """Classify email using GROQ + LLaMA 3.1"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("❌ GROQ_API_KEY not found in .env file!")

    client = Groq(api_key=api_key)
    system_prompt = load_prompt()

    # Clean email
    email_text = clean_email(email_text)

    # Full prompt with email
    full_prompt = f"""
{system_prompt}

EMAIL TO CLASSIFY:
{email_text}

You MUST return JSON ONLY. No explanation.
"""

    # Call the model
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        response_format={"type": "json_object"},  # ensures Python dict
        messages=[
            {"role": "system", "content": "You are an email classification engine."},
            {"role": "user", "content": full_prompt}
        ]
    )

    raw_result = response.choices[0].message.content

    # 🔹 Ensure result is a Python dict
    if isinstance(raw_result, str):
        result = json.loads(raw_result)
    else:
        result = raw_result

    # Add job_id if relevant but missing
    if result.get("is_relevant") and "job_id" not in result:
        result["job_id"] = str(uuid.uuid4())

    return result
