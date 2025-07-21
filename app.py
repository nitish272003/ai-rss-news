import streamlit as st
import pandas as pd
import math
from datetime import datetime
from urllib.parse import urlparse
import feedparser

# ---- Local helpers ----------------------------------------------------------
from rss_sources import rss_sources
from news_analyzer import build_prompt, call_openrouter_api

# ---- Utility ----------------------------------------------------------------
def fetch_rss(url: str, limit: int = 50) -> list[dict]:
    feed = feedparser.parse(url)
    entries = []
    for e in feed.entries[:limit]:
        # published → ISO-8601 fallback
        pub = getattr(e, "published", getattr(e, "updated", ""))
        try:
            pub_iso = datetime.strptime(
                pub, "%a, %d %b %Y %H:%M:%S %z"
            ).strftime("%Y-%m-%d %H:%M")
        except Exception:
            pub_iso = pub
        entries.append(
            {
                "title": e.get("title", "Untitled"),
                "link": e.get("link", ""),
                "summary": e.get("summary", "No summary available"),
                "published": pub_iso,
            }
        )
    return entries

def filter_by_keywords(entries, keywords):
    if not keywords:
        return entries
    kw = [k.lower() for k in keywords]
    out = []
    for art in entries:
        text = (art["title"] + " " + art["summary"]).lower()
        if any(k in text for k in kw):
            out.append(art)
    return out

# ---- Streamlit UI -----------------------------------------------------------
st.set_page_config("📰 Tech-News Dashboard", "📰", "wide")
st.title("📰 Tech-News Dashboard")

# Sidebar ──────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("RSS Source")
    source_key = st.selectbox(
        "Pick one source", options=list(rss_sources.keys()), format_func=lambda k: rss_sources[k][0]
    )
    max_articles = st.slider("Articles to fetch", 10, 100, 50, 10)
    st.markdown("---")

    st.header("Keyword Filter")
    kw_input = st.text_area(
        "Enter keywords (one per line)", height=120, placeholder="AI\nMachine Learning\nRobotics"
    )
    keywords = [k.strip() for k in kw_input.splitlines() if k.strip()]

# Fetch feed ───────────────────────────────────────────────────────────────────
src_name, src_url = rss_sources[source_key]
with st.spinner(f"Loading **{src_name}** …"):
    articles = fetch_rss(src_url, max_articles)

filt_articles = filter_by_keywords(articles, keywords)

# Pagination ───────────────────────────────────────────────────────────────────
PER_PAGE = 5
total_pages = max(1, math.ceil(len(filt_articles) / PER_PAGE))
page = st.number_input("Page", 1, total_pages, 1, key="page_selector")

start, end = (page - 1) * PER_PAGE, page * PER_PAGE
page_articles = filt_articles[start:end]

st.subheader(f"{src_name} — {len(filt_articles)} article(s) found")

# Selection state
if "picked" not in st.session_state:
    st.session_state.picked = None
if "analysis" not in st.session_state:
    st.session_state.analysis = None

# Article cards ────────────────────────────────────────────────────────────────
for idx, art in enumerate(page_articles, start=start):
    st.markdown(f"### {art['title']}")
    st.write(f"Published: {art['published']}")
    st.write(art["summary"][:500] + ("…" if len(art["summary"]) > 500 else ""))
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Select", key=f"sel_{idx}"):
            st.session_state.picked = art
            st.session_state.analysis = None
    with col_b:
        st.markdown(f"[Read full article]({art['link']})")
    st.markdown("---")

# Navigation buttons
col_prev, col_next = st.columns(2)
with col_prev:
    if st.button("◀ Previous") and page > 1:
        st.session_state.page_selector -= 1
with col_next:
    if st.button("Next ▶") and page < total_pages:
        st.session_state.page_selector += 1

# Analyzer ─────────────────────────────────────────────────────────────────────
if st.session_state.picked:
    art = st.session_state.picked
    st.info(f"Selected: **{art['title']}**")
    if st.button("🔍 Analyze News"):
        prompt = build_prompt(art["link"], art["published"])
        st.code(prompt, language="markdown")
        # call the LLM
        result = call_openrouter_api(prompt)
        st.session_state.analysis = result

# Show LLM output
if st.session_state.analysis:
    if st.session_state.analysis["ok"]:
        st.success("Analysis complete")
        st.json(st.session_state.analysis["response"])
    else:
        st.error(st.session_state.analysis["error"])

st.caption("© 2025 Tech-News Dashboard")
# ---- End of Streamlit UI -----------------------------------------------------