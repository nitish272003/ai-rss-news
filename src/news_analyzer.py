import os, json, requests, streamlit as st

SYSTEM_MSG = (
    "You are a specialised AI assistant designed to analyse technology "
    "news articles and turn them into structured, actionable insights."
)

PROMPT_TMPL = """# Technology News Analysis Prompt Template

## System Instructions
{system_msg}

## Required Output Format
Feed Title: [Your compelling 80-character headline]
Description: [Concise overview of main development]
Core Message: [Comprehensive summary covering all major points and implications. Remove citation brackets like [1], [2]…]
Key Tags: [keyword1, keyword2, keyword3, keyword4, keyword5]
Sector: [Primary technology sector]
Published Date: {published}

## Article to Analyse
{url}
"""

def build_prompt(url: str, published: str) -> str:
    """Return a fully-formatted prompt for the LLM."""
    return PROMPT_TMPL.format(system_msg=SYSTEM_MSG, published=published, url=url)


# --------------------------------------------------------------------------- #
#                           OpenRouter connection                             
# --------------------------------------------------------------------------- #
BASE_URL = st.secrets.get(
    "OPENROUTER_BASE_URL",
    os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions"),
)
MODEL    = st.secrets.get("OPENROUTER_MODEL", os.getenv("OPENROUTER_MODEL", "perplexity/sonar-pro"))
API_KEY  = st.secrets.get("OPENROUTER_API_KEY", os.getenv("OPENROUTER_API_KEY"))

HEADERS = {
    "Authorization": f"Bearer {API_KEY}" if API_KEY else "",
    "Content-Type": "application/json",
}

def call_openrouter_api(prompt: str, temperature: float = 0.4) -> dict:
    """Send the prompt to OpenRouter and return either the text or an error."""
    if not API_KEY:
        return {"ok": False, "error": "OPENROUTER_API_KEY missing in secrets / env-vars"}

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_MSG},
            {"role": "user",   "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": 1600,
    }

    try:
        resp = requests.post(BASE_URL, headers=HEADERS, json=payload, timeout=60)
        resp.raise_for_status()
    except Exception as e:
        return {"ok": False, "error": f"HTTP error: {e}"}

    # Safe JSON decode
    try:
        data = resp.json()
    except json.JSONDecodeError:
        snip = resp.text[:200]
        return {"ok": False, "error": f"Non-JSON response: “{snip} …”"}

    # Extract assistant message
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        return {"ok": False, "error": f"Malformed JSON structure: {e} — full JSON: {data}"}

    return {"ok": True, "response": content}