import streamlit as st
import requests

SYSTEM_INSTR = (
    "You are a specialized AI assistant designed to analyze technology "
    "news articles with precision and depth. Your role is to transform raw "
    "news content into structured, actionable insights that provide "
    "comprehensive understanding of technological developments, market "
    "movements, and industry trends."
)

TEMPLATE = """# Technology News Analysis

## Article Details
URL: {url}
Published: {published}

## Analysis Request
Please analyze this technology news article and provide:

1. **Feed Title**: Create a compelling 80-character headline
2. **Description**: Concise overview of the main development
3. **Core Message**: Comprehensive summary covering all major points and implications
4. **Key Tags**: 5 relevant keywords
5. **Sector**: Primary technology sector

Format your response as clear text, not JSON.
"""

def build_prompt(url: str, published: str) -> str:
    return TEMPLATE.format(published=published, url=url)

# Use Streamlit secrets instead of os.getenv
def call_openrouter_api(prompt: str) -> dict:
    try:
        # Get credentials from Streamlit secrets
        api_key = st.secrets["OPENROUTER_API_KEY"]
        base_url = st.secrets.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")
        model = st.secrets.get("OPENROUTER_MODEL", "perplexity/sonar-pro")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_INSTR},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 1500,
            "temperature": 0.3
        }
        
        response = requests.post(base_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        # Safe JSON parsing
        try:
            json_data = response.json()
            # Extract the actual content
            content = json_data['choices'][0]['message']['content']
            return {"ok": True, "response": content}
        except (KeyError, IndexError) as e:
            return {"ok": False, "error": f"Invalid API response structure: {str(e)}"}
        except ValueError as e:
            return {"ok": False, "error": f"JSON parsing failed: {str(e)}. Raw response: {response.text[:200]}"}
            
    except Exception as e:
        return {"ok": False, "error": f"API call failed: {str(e)}"}
