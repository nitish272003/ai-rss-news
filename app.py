import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime
import requests
import json

# Configuration
st.set_page_config(page_title="📰 Tech News Analyzer", page_icon="📰", layout="wide")

# RSS Sources
RSS_SOURCES = {
    "DeepMind Blog": "https://rss.app/feeds/dISWeyZM2Tzfmh7n.xml",
    "NVIDIA Gen AI": "https://rss.app/feeds/sh5T3ziuw18ppMnJ.xml",
    "OpenAI News": "https://rss.app/feeds/88lTJ2E61JPFhtfy.xml",
    "AWS ML Blog": "https://rss.app/feeds/IvbT7TcwbDQXkpio.xml",
    "Perplexity AI": "https://rss.app/feeds/nZ4JF5xejzLVJXkA.xml",
    "NVIDIA Robotics": "https://rss.app/feeds/fgok8MDwu6ZJCOl7.xml",
    "Anthropic Updates": "https://rss.app/feeds/R87xeBq4tXiHLS3s.xml",
    "Microsoft AI": "https://rss.app/feeds/bQF9FLInBGQsYBi5.xml"
}

def fetch_rss_entries(url, source_name):
    """Fetch entries from RSS feed URL"""
    try:
        feed = feedparser.parse(url)
        entries = []

        for entry in feed.entries:
            # Handle published date formatting
            published = entry.get("published", "")
            try:
                if published:
                    pub_date = datetime.strptime(published, "%a, %d %b %Y %H:%M:%S %z").strftime("%Y-%m-%d %H:%M")
                else:
                    pub_date = "Unknown"
            except:
                pub_date = published

            entries.append({
                "title": entry.get("title", ""),
                "description": entry.get("summary", ""),
                "link": entry.get("link", ""),
                "published_date": pub_date,
                "source": source_name,
                "selected": False,
                "analyzed": False
            })

        return entries
    except Exception as e:
        st.error(f"Error fetching RSS from {source_name}: {str(e)}")
        return []

def analyze_news_content(link, published_date):
    """Analyze news content using Perplexity API"""
    try:
        # Get API credentials from Streamlit secrets
        api_key = st.secrets["OPENROUTER_API_KEY"]
        base_url = st.secrets.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")
        model = st.secrets.get("OPENROUTER_MODEL", "perplexity/sonar-pro")

        prompt = f"""
# Technology News Analysis Prompt Template

## System Instructions
You are a specialized AI assistant designed to analyze technology news articles with precision and depth. Your role is to transform raw news content into structured, actionable insights that provide comprehensive understanding of technological developments, market movements, and industry trends.

## Required Output Format
Please analyze the article at this URL and provide a structured response in the following format:

Feed Title: [Your compelling 80-character headline]
Description: [Concise overview of main development]
Core Message: [Comprehensive summary covering all major points, context, implications from the entire article. Remove citation brackets like [1], [2], [3] from text.]
Key Tags: [keyword1, keyword2, keyword3, keyword4, keyword5]
Sector: [Selected primary technology sector]
Published Date: {published_date}

## Article to Analyze:
{link}

Please visit the URL, read the full article content, and provide the analysis in the exact format specified above.
"""

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional AI assistant for structured technology news analysis. You can browse the web to read articles and provide detailed analysis."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.4,
            "max_tokens": 2000
        }

        response = requests.post(base_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        analysis_text = result['choices'][0]['message']['content']
        
        # Parse the structured response
        parsed_analysis = parse_analysis_response(analysis_text)
        
        return {
            "success": True,
            "analysis": parsed_analysis,
            "raw_response": analysis_text
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Analysis failed: {str(e)}"
        }

def parse_analysis_response(response_text):
    """Parse the structured analysis response"""
    try:
        lines = response_text.split('\n')
        analysis = {}
        
        for line in lines:
            if line.startswith('Feed Title:'):
                analysis['feed_title'] = line.replace('Feed Title:', '').strip()
            elif line.startswith('Description:'):
                analysis['description'] = line.replace('Description:', '').strip()
            elif line.startswith('Core Message:'):
                analysis['core_message'] = line.replace('Core Message:', '').strip()
            elif line.startswith('Key Tags:'):
                analysis['key_tags'] = line.replace('Key Tags:', '').strip()
            elif line.startswith('Sector:'):
                analysis['sector'] = line.replace('Sector:', '').strip()
            elif line.startswith('Published Date:'):
                analysis['published_date'] = line.replace('Published Date:', '').strip()
        
        return analysis
    except:
        return {"raw_text": response_text}

# Initialize session state
if 'articles' not in st.session_state:
    st.session_state.articles = []
if 'selected_article' not in st.session_state:
    st.session_state.selected_article = None
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

# Main UI
st.title("📰 Tech News Analyzer")
st.markdown("Analyze technology news articles with AI-powered insights")

# Sidebar
with st.sidebar:
    st.header("🔧 Settings")
    
    # API Status Check
    try:
        api_key = st.secrets["OPENROUTER_API_KEY"]
        if api_key and api_key.startswith("sk-"):
            st.success("✅ API Key Connected")
        else:
            st.error("❌ Invalid API Key")
    except:
        st.error("❌ API Key Missing")
    
    # Source Selection
    selected_source = st.selectbox("📡 Choose News Source", list(RSS_SOURCES.keys()))
    num_articles = st.slider("📄 Number of Articles", 5, 50, 20)
    
    st.markdown("---")
    
    # Fetch Articles Button
    if st.button("🔄 Fetch Latest Articles", type="primary"):
        with st.spinner(f"Fetching articles from {selected_source}..."):
            source_url = RSS_SOURCES[selected_source]
            articles = fetch_rss_entries(source_url, selected_source)
            st.session_state.articles = articles[:num_articles]
            st.session_state.selected_article = None
            st.session_state.analysis_result = None
        st.success(f"✅ Fetched {len(st.session_state.articles)} articles")

# Main Content
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("📰 Articles")
    
    if st.session_state.articles:
        # Display articles
        for i, article in enumerate(st.session_state.articles):
            with st.container():
                st.markdown(f"### {article['title'][:100]}...")
                st.markdown(f"**Source:** {article['source']} | **Published:** {article['published_date']}")
                
                # Show preview of description
                description_preview = article['description'][:200] + "..." if len(article['description']) > 200 else article['description']
                st.markdown(f"**Preview:** {description_preview}")
                
                col_btn1, col_btn2 = st.columns([1, 2])
                
                with col_btn1:
                    if st.button(f"🔍 Select & Analyze", key=f"select_{i}"):
                        st.session_state.selected_article = article
                        st.session_state.analysis_result = None
                
                with col_btn2:
                    st.markdown(f"[🔗 Read Full Article]({article['link']})")
                
                st.markdown("---")
    else:
        st.info("👈 Select a source and click 'Fetch Latest Articles' to get started")

with col2:
    st.subheader("🤖 AI Analysis")
    
    if st.session_state.selected_article:
        article = st.session_state.selected_article
        
        st.markdown("### 📄 Selected Article")
        st.markdown(f"**Title:** {article['title']}")
        st.markdown(f"**Source:** {article['source']}")
        st.markdown(f"**Published:** {article['published_date']}")
        
        # Analysis Button
        if st.button("🚀 Start AI Analysis", type="primary"):
            with st.spinner("🔍 Analyzing article with AI..."):
                result = analyze_news_content(article['link'], article['published_date'])
                st.session_state.analysis_result = result
        
        # Display Analysis Results
        if st.session_state.analysis_result:
            result = st.session_state.analysis_result
            
            if result['success']:
                st.success("✅ Analysis Complete!")
                
                analysis = result['analysis']
                
                # Display structured analysis
                st.markdown("### 📊 Analysis Results")
                
                if 'feed_title' in analysis:
                    st.markdown(f"**📰 Feed Title:** {analysis['feed_title']}")
                
                if 'description' in analysis:
                    st.markdown(f"**📝 Description:** {analysis['description']}")
                
                if 'core_message' in analysis:
                    st.markdown(f"**💡 Core Message:** {analysis['core_message']}")
                
                if 'key_tags' in analysis:
                    st.markdown(f"**🏷️ Key Tags:** {analysis['key_tags']}")
                
                if 'sector' in analysis:
                    st.markdown(f"**🏢 Sector:** {analysis['sector']}")
                
                # Show raw response in expander
                with st.expander("📋 View Raw Analysis"):
                    st.text(result['raw_response'])
                
            else:
                st.error("❌ Analysis Failed")
                st.error(result['error'])
    
    else:
        st.info("👈 Select an article to analyze")

# Footer
st.markdown("---")
st.caption("© 2025 Tech News Analyzer")