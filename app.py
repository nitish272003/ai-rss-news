import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime
import requests
from urllib.parse import urlparse

# Import your configuration
from config import Config, rss_sources

def fetch_rss_feed(url, max_entries=5):
    """Fetch and parse RSS feed from URL"""
    try:
        feed = feedparser.parse(url)
        
        if feed.bozo:
            st.warning(f"Warning: Feed may have parsing issues")
        
        entries = []
        for entry in feed.entries[:max_entries]:
            # Extract publication date
            pub_date = "No date"
            if hasattr(entry, 'published'):
                try:
                    pub_date = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %z').strftime('%Y-%m-%d %H:%M')
                except:
                    pub_date = entry.published
            elif hasattr(entry, 'updated'):
                try:
                    pub_date = datetime.strptime(entry.updated, '%a, %d %b %Y %H:%M:%S %z').strftime('%Y-%m-%d %H:%M')
                except:
                    pub_date = entry.updated
            
            entries.append({
                'title': entry.get('title', 'No title'),
                'link': entry.get('link', ''),
                'summary': entry.get('summary', 'No summary available')[:200] + '...' if len(entry.get('summary', '')) > 200 else entry.get('summary', 'No summary available'),
                'published': pub_date
            })
        
        return {
            'feed_title': feed.feed.get('title', 'Unknown Feed'),
            'feed_description': feed.feed.get('description', ''),
            'entries': entries,
            'success': True
        }
    
    except Exception as e:
        return {
            'error': str(e),
            'success': False
        }

def main():
    st.set_page_config(
        page_title="RSS Sources Dashboard",
        page_icon="📰",
        layout="wide"
    )
    
    st.title("🔄 RSS Sources Dashboard")
    st.markdown("---")
    
    # Sidebar for source selection
    with st.sidebar:
        st.header("📋 RSS Sources")
        st.markdown("Select sources to view their latest articles:")
        
        # Create checkboxes for each RSS source
        selected_sources = {}
        for source_id, (source_name, source_url) in rss_sources.items():
            selected_sources[source_id] = st.checkbox(
                source_name,
                key=f"source_{source_id}",
                help=f"URL: {source_url}"
            )
        
        st.markdown("---")
        
        # Settings
        st.subheader("⚙️ Settings")
        max_articles = st.slider("Max articles per source", 1, 20, 5)
        auto_refresh = st.checkbox("Auto refresh (every 5 minutes)")
        
        if auto_refresh:
            st.rerun()
    
    # Main content area
    if not any(selected_sources.values()):
        st.info("👈 Please select one or more RSS sources from the sidebar to get started!")
        
        # Show all available sources
        st.subheader("📡 Available RSS Sources")
        
        sources_data = []
        for source_id, (source_name, source_url) in rss_sources.items():
            domain = urlparse(source_url).netloc
            sources_data.append({
                'ID': source_id,
                'Source Name': source_name,
                'Domain': domain,
                'URL': source_url
            })
        
        df = pd.DataFrame(sources_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    else:
        # Process selected sources
        for source_id, is_selected in selected_sources.items():
            if is_selected:
                source_name, source_url = rss_sources[source_id]
                
                with st.expander(f"📰 {source_name}", expanded=True):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Source:** {source_name}")
                    with col2:
                        if st.button(f"🔄 Refresh", key=f"refresh_{source_id}"):
                            st.rerun()
                    
                    # Fetch RSS feed
                    with st.spinner(f"Loading articles from {source_name}..."):
                        feed_data = fetch_rss_feed(source_url, max_articles)
                    
                    if feed_data['success']:
                        st.success(f"✅ Loaded {len(feed_data['entries'])} articles")
                        
                        # Display feed info
                        if feed_data.get('feed_description'):
                            st.markdown(f"*{feed_data['feed_description']}*")
                        
                        # Display articles
                        for i, article in enumerate(feed_data['entries']):
                            with st.container():
                                st.markdown(f"### 📄 {article['title']}")
                                
                                col1, col2 = st.columns([2, 1])
                                with col1:
                                    st.markdown(f"**Published:** {article['published']}")
                                with col2:
                                    if article['link']:
                                        st.markdown(f"[🔗 Read More]({article['link']})")
                                
                                st.markdown(article['summary'])
                                
                                if i < len(feed_data['entries']) - 1:
                                    st.markdown("---")
                    
                    else:
                        st.error(f"❌ Failed to load RSS feed: {feed_data['error']}")
                        st.markdown(f"**URL:** {source_url}")

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center'>
            <p>🤖 RSS Sources Dashboard | Built with Streamlit</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()