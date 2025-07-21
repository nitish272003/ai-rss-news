
import streamlit as st

from config.rss_sources import rss_sources

class Config:
    class LLM:
        try:
            OPENROUTER_API_KEY = st.secrets["openrouter_api_key"]
        except KeyError:
            OPENROUTER_API_KEY = ""
            
        OPENROUTER_API_URL = "https://openrouter.ai/api/v1"
        OPENROUTER_MODEL = "perplexity/sonar"


__all__ = ["Config", "rss_sources"]