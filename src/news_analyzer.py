import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Constants from environment or default fallback
BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")
MODEL = os.getenv("OPENROUTER_MODEL", "perplexity/sonar-pro")
API_KEY = os.getenv("OPENROUTER_API_KEY")

# System instruction for AI
SYSTEM_INSTR = (
    "You are a specialized AI assistant designed to analyze technology "
    "news articles with precision and depth. Your role is to transform raw "
    "news content into structured, actionable insights that provide "
    "comprehensive understanding of technological developments, market "
    "movements, and industry trends."
)

# Prompt template
TEMPLATE = """# Technology News Analysis Prompt Template

## System Instructions
{system}

## Required Output Format
Feed Title: [Your compelling 80-character headline]
Description: [Concise overview of main development]
Core Message: [Comprehensive summary covering all major points, context, implications from the entire article and Remove citation brackets like [1], [2], [3] from text.]
Key Tags: [keyword1, keyword2, keyword3, keyword4, keyword5]
Sector: [Selected primary technology sector]
Published Date: {published}

## Article to Analyze:
{url}
"""

# Builds the prompt from URL and published date
def build_prompt(url: str, published: str) -> str:
    return TEMPLATE.format(system=SYSTEM_INSTR, published=published, url=url)

# Calls the OpenRouter API with prompt
def call_openrouter_api(prompt: str) -> dict:
    if not API_KEY:
        return {"ok": False, "error": "OPENROUTER_API_KEY is missing in .env file"}

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_INSTR},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
        "max_tokens": 1500
    }

    try:
        response = requests.post(BASE_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return {"ok": True, "response": data["choices"][0]["message"]["content"]}
    except Exception as e:
        return {"ok": False, "error": str(e)}