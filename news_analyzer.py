import os
import requests

SYSTEM_INSTR = (
    "You are a specialized AI assistant designed to analyze technology "
    "news articles with precision and depth. Your role is to transform raw "
    "news content into structured, actionable insights that provide "
    "comprehensive understanding of technological developments, market "
    "movements, and industry trends."
)

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

def build_prompt(url: str, published: str) -> str:
    return TEMPLATE.format(system=SYSTEM_INSTR, published=published, url=url)

# ---- OpenRouter ----------------------------------------------------------------
BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")
MODEL = os.getenv("OPENROUTER_MODEL", "perplexity/sonar-pro")
API_KEY = os.getenv("OPENROUTER_API_KEY")

def call_openrouter_api(prompt: str) -> dict:
    if API_KEY is None:
        return {"ok": False, "error": "OPENROUTER_API_KEY is missing in secrets.toml"}
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
    }
    try:
        resp = requests.post(BASE_URL, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        return {"ok": True, "response": resp.json()}
    except Exception as e:
        return {"ok": False, "error": str(e)}
# ---- End of OpenRouter ---------------------------------------------------------