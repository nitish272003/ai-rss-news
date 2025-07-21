import streamlit as st
import pandas as pd
import feedparser
from datetime import datetime
import requests

# Configuration
st.set_page_config(page_title="📰 News Analyzer", page_icon="📰", layout="wide")

# RSS Sources
RSS_SOURCES = {
    "DeepMind Blog": "https://rss.app/feeds/dISWeyZM2Tzfmh7n.xml",
    "NVIDIA Gen AI": "https://rss.app/feeds/sh5T3ziuw18ppMnJ.xml", 
    "OpenAI News": "https://rss.app/feeds/88lTJ2E61JPFhtfy.xml",
    "AWS ML Blog": "https://rss.app/feeds/IvbT7TcwbDQXkpio.xml",
    "Perplexity AI": "https://rss.app/feeds/nZ4JF5xejzLVJXkA.xml"
}

def fetch_rss_articles(url, limit=20):
    """Fetch articles from RSS feed"""
    try:
        feed = feedparser.parse(url)
        articles = []
        
        for entry in feed.entries[:limit]:
            # Handle published date
            published = getattr(entry, 'published', getattr(entry, 'updated', 'Unknown'))
            try:
                pub_date = datetime.strptime(published, "%a, %d %b %Y %H:%M:%S %z").strftime("%Y-%m-%d %H:%M")
            except:
                pub_date = published
            
            articles.append({
                'title': entry.get('title', 'No Title'),
                'link': entry.get('link', ''),
                'summary': entry.get('summary', 'No summary available'),
                'published': pub_date
            })
        
        return articles
    except Exception as e:
        st.error(f"Error fetching RSS: {str(e)}")
        return []

def analyze_article(article_url, article_title):
    """Analyze article using OpenRouter API"""
    try:
        # Get credentials from Streamlit secrets
        api_key = st.secrets["OPENROUTER_API_KEY"]
        base_url = st.secrets["OPENROUTER_BASE_URL"]
        model = st.secrets["OPENROUTER_MODEL"]
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""
        Analyze this technology news article and provide insights:
        
        Title: {article_title}
        URL: {article_url}
        
        Please provide:
        1. Key Points (3-5 bullet points)
        2. Technology Impact
        3. Market Implications
        4. Summary (2-3 sentences)
        """
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a technology news analyst. Provide clear, structured analysis of tech news articles."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000
        }
        
        response = requests.post(base_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content']
        
    except Exception as e:
        return f"Analysis failed: {str(e)}"

# Main App
st.title("📰 Tech News Analyzer")
st.markdown("Analyze the latest technology news with AI-powered insights")

# Sidebar
with st.sidebar:
    st.header("Settings")
    selected_source = st.selectbox("Choose News Source", list(RSS_SOURCES.keys()))
    num_articles = st.slider("Number of Articles", 5, 30, 10)
    
    # Check credentials
    try:
        api_key = st.secrets["OPENROUTER_API_KEY"]
        if api_key:
            st.success("✅ API credentials loaded")
        else:
            st.error("❌ API key missing")
    except:
        st.error("❌ Secrets file not found")

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader(f"📄 Latest from {selected_source}")
    
    # Fetch articles
    if st.button("🔄 Fetch Articles"):
        with st.spinner("Fetching articles..."):
            rss_url = RSS_SOURCES[selected_source]
            articles = fetch_rss_articles(rss_url, num_articles)
            st.session_state['articles'] = articles
    
    # Display articles
    if 'articles' in st.session_state:
        for i, article in enumerate(st.session_state['articles']):
            with st.expander(f"📰 {article['title'][:80]}..."):
                st.write(f"**Published:** {article['published']}")
                st.write(f"**Summary:** {article['summary'][:200]}...")
                st.write(f"**Link:** {article['link']}")
                
                if st.button(f"🔍 Analyze This Article", key=f"analyze_{i}"):
                    st.session_state['selected_article'] = article

with col2:
    st.subheader("🤖 AI Analysis")
    
    if 'selected_article' in st.session_state:
        article = st.session_state['selected_article']
        st.write(f"**Analyzing:** {article['title']}")
        
        if st.button("🚀 Start Analysis"):
            with st.spinner("Analyzing article..."):
                analysis = analyze_article(article['link'], article['title'])
                st.session_state['analysis'] = analysis
        
        # Display analysis
        if 'analysis' in st.session_state:
            st.markdown("### 📊 Analysis Results")
            st.write(st.session_state['analysis'])
    else:
        st.info("👈 Select an article from the left panel to analyze")

# Footer
st.markdown("---")
st.caption("© 2025 Tech News Analyzer")