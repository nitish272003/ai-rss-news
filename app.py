import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from urllib.parse import urlparse
import math

# Try to import feedparser with error handling
try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False

# Import RSS sources from the separate file
try:
    from config.rss_sources import rss_sources
    RSS_SOURCES_AVAILABLE = True
except ImportError:
    RSS_SOURCES_AVAILABLE = False
    st.error("⚠️ Could not import rss_sources.py. Please make sure the file exists in the same directory.")
    # Fallback RSS sources
    rss_sources = {
        "1": ("DeepMind Blog", "https://rss.app/feeds/dISWeyZM2Tzfmh7n.xml"),
        "2": ("NVIDIA Developer - Generative AI", "https://rss.app/feeds/sh5T3ziuw18ppMnJ.xml"),
        "3": ("OpenAI News", "https://rss.app/feeds/88lTJ2E61JPFhtfy.xml"),
    }

def fetch_rss_feed(url, max_entries=50):
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
                'summary': entry.get('summary', 'No summary available'),
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

def filter_entries_by_keywords(entries, keywords):
    """Filter entries based on keywords in title and summary"""
    if not keywords:
        return entries
    
    keywords_lower = [keyword.strip().lower() for keyword in keywords if keyword.strip()]
    if not keywords_lower:
        return entries
    
    filtered_entries = []
    for entry in entries:
        title_lower = entry['title'].lower()
        summary_lower = entry['summary'].lower()
        
        # Check if any keyword appears in title or summary
        if any(keyword in title_lower or keyword in summary_lower for keyword in keywords_lower):
            filtered_entries.append(entry)
    
    return filtered_entries

def paginate_entries(entries, page_size=5):
    """Calculate pagination information"""
    total_entries = len(entries)
    total_pages = math.ceil(total_entries / page_size) if total_entries > 0 else 1
    return total_entries, total_pages

def get_page_entries(entries, page_num, page_size=5):
    """Get entries for a specific page"""
    start_idx = (page_num - 1) * page_size
    end_idx = start_idx + page_size
    return entries[start_idx:end_idx]

def main():
    st.set_page_config(
        page_title="RSS News Dashboard",
        page_icon="📰",
        layout="wide"
    )
    
    st.title("🔄 RSS News Dashboard with Pagination & Filtering")
    
    # Check for dependencies
    if not FEEDPARSER_AVAILABLE:
        st.error("📦 Missing Required Dependencies")
        st.markdown("""
        **The `feedparser` library is required to run this app.**
        
        Please install it using:
        ```bash
        pip install feedparser
        ```
        """)
        st.stop()
    
    # Initialize session state for pagination
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
    if 'total_pages' not in st.session_state:
        st.session_state.total_pages = 1
    if 'filtered_entries' not in st.session_state:
        st.session_state.filtered_entries = []
    if 'keywords' not in st.session_state:
        st.session_state.keywords = []
    
    # Create two columns for layout
    col1, col2 = st.columns([3, 1])
    
    # Left column - RSS Source Selection and News Display
    with col1:
        st.subheader("📡 Select RSS Source")
        
        # Create select box for RSS sources
        source_options = ["-- Select a Source --"] + [f"{source_name}" for source_name in [info[0] for info in rss_sources.values()]]
        selected_source_name = st.selectbox(
            "Choose a news source:",
            source_options,
            key="source_selector"
        )
        
        # Find the selected source ID and URL
        selected_source_id = None
        selected_source_url = None
        if selected_source_name != "-- Select a Source --":
            for source_id, (source_name, source_url) in rss_sources.items():
                if source_name == selected_source_name:
                    selected_source_id = source_id
                    selected_source_url = source_url
                    break
        
        # Display news if source is selected
        if selected_source_id and selected_source_url:
            st.markdown(f"**Selected Source:** {selected_source_name}")
            
            # Fetch RSS feed
            with st.spinner(f"Loading articles from {selected_source_name}..."):
                feed_data = fetch_rss_feed(selected_source_url)
            
            if feed_data['success']:
                # Apply keyword filtering
                keywords = st.session_state.get('keywords', [])
                filtered_entries = filter_entries_by_keywords(feed_data['entries'], keywords)
                st.session_state.filtered_entries = filtered_entries
                
                # Calculate pagination
                total_entries, total_pages = paginate_entries(filtered_entries, 5)
                st.session_state.total_pages = total_pages
                
                # Reset to page 1 if current page exceeds total pages
                if st.session_state.current_page > total_pages:
                    st.session_state.current_page = 1
                
                # Display pagination info
                st.markdown(f"**Total Articles:** {total_entries} | **Total Pages:** {total_pages}")
                
                if total_entries > 0:
                    # Pagination controls at top
                    col_prev, col_info, col_next = st.columns([1, 2, 1])
                    
                    with col_prev:
                        if st.button("⬅️ Previous", disabled=(st.session_state.current_page <= 1)):
                            st.session_state.current_page -= 1
                            st.rerun()
                    
                    with col_info:
                        st.markdown(f"**Page {st.session_state.current_page} of {total_pages}**")
                    
                    with col_next:
                        if st.button("➡️ Next", disabled=(st.session_state.current_page >= total_pages)):
                            st.session_state.current_page += 1
                            st.rerun()
                    
                    st.markdown("---")
                    
                    # Get current page entries
                    page_entries = get_page_entries(filtered_entries, st.session_state.current_page, 5)
                    
                    # Display articles for current page
                    for i, article in enumerate(page_entries):
                        with st.container():
                            st.markdown(f"### 📄 {article['title']}")
                            
                            col_date, col_link = st.columns([2, 1])
                            with col_date:
                                st.markdown(f"**Published:** {article['published']}")
                            with col_link:
                                if article['link']:
                                    st.markdown(f"[🔗 Read More]({article['link']})")
                            
                            # Show summary (truncate if too long for better readability)
                            summary = article['summary']
                            if len(summary) > 400:
                                summary = summary[:400] + "..."
                            st.markdown(summary)
                            
                            if i < len(page_entries) - 1:
                                st.markdown("---")
                    
                    # Bottom pagination controls
                    st.markdown("---")
                    col_prev2, col_info2, col_next2 = st.columns([1, 2, 1])
                    
                    with col_prev2:
                        if st.button("⬅️ Previous ", disabled=(st.session_state.current_page <= 1), key="prev2"):
                            st.session_state.current_page -= 1
                            st.rerun()
                    
                    with col_info2:
                        # Page number input
                        page_input = st.number_input(
                            "Jump to page:",
                            min_value=1,
                            max_value=total_pages,
                            value=st.session_state.current_page,
                            key="page_input"
                        )
                        if page_input != st.session_state.current_page:
                            st.session_state.current_page = page_input
                            st.rerun()
                    
                    with col_next2:
                        if st.button("➡️ Next ", disabled=(st.session_state.current_page >= total_pages), key="next2"):
                            st.session_state.current_page += 1
                            st.rerun()
                
                else:
                    st.info("No articles found matching your keyword filters.")
                    st.markdown("Try adjusting your keywords or clear all filters.")
            
            else:
                st.error(f"❌ Failed to load RSS feed: {feed_data['error']}")
                st.markdown(f"**URL:** {selected_source_url}")
        
        else:
            st.info("👆 Please select an RSS source to view articles.")
            
            # Show available sources table
            st.subheader("📋 Available RSS Sources")
            sources_data = []
            for source_id, (source_name, source_url) in rss_sources.items():
                domain = urlparse(source_url).netloc
                sources_data.append({
                    'ID': source_id,
                    'Source Name': source_name,
                    'Domain': domain
                })
            
            df = pd.DataFrame(sources_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Right column - Keyword Filtering and Settings
    with col2:
        st.subheader("🔍 Keyword Filtering")
        
        # Keyword input
        st.markdown("**Filter news by keywords:**")
        keyword_input = st.text_area(
            "Enter keywords (one per line):",
            height=120,
            placeholder="AI\\nmachine learning\\nrobotics\\ndeep learning\\nChatGPT\\nOpenAI",
            key="keyword_input"
        )
        
        # Process keywords
        keywords = [keyword.strip() for keyword in keyword_input.split('\n') if keyword.strip()]
        
        # Display active keywords
        if keywords:
            st.markdown("**Active Keywords:**")
            for keyword in keywords:
                st.markdown(f"• {keyword}")
        else:
            st.markdown("*No keywords set - showing all articles*")
        
        # Update keywords and reset pagination
        if st.button("🔄 Apply Filters", type="primary"):
            st.session_state.keywords = keywords
            st.session_state.current_page = 1  # Reset to page 1 when applying filters
            st.rerun()
        
        # Clear filters button
        if st.button("🗑️ Clear All Filters"):
            st.session_state.keywords = []
            st.session_state.current_page = 1
            st.rerun()
        
        st.markdown("---")
        
        # Quick filter presets
        st.subheader("🎯 Quick Filters")
        st.markdown("**Popular Topics:**")
        
        if st.button("🤖 AI & Machine Learning"):
            st.session_state.keywords = ["AI", "artificial intelligence", "machine learning", "neural", "deep learning"]
            st.session_state.current_page = 1
            st.rerun()
        
        if st.button("🦾 Robotics"):
            st.session_state.keywords = ["robot", "robotics", "automation", "autonomous"]
            st.session_state.current_page = 1
            st.rerun()
        
        if st.button("💬 Language Models"):
            st.session_state.keywords = ["GPT", "LLM", "language model", "ChatGPT", "Claude", "Gemini"]
            st.session_state.current_page = 1
            st.rerun()
        
        if st.button("🧠 Research & Development"):
            st.session_state.keywords = ["research", "breakthrough", "study", "paper", "development"]
            st.session_state.current_page = 1
            st.rerun()
        
        st.markdown("---")
        
        # Settings section
        st.subheader("⚙️ Settings")
        
        # Auto refresh option
        auto_refresh = st.checkbox("Auto refresh (every 5 minutes)")
        if auto_refresh:
            st.rerun()
        
        # Manual refresh button
        if st.button("🔄 Refresh Current Source"):
            st.rerun()
        
        # Display current filter status
        st.markdown("---")
        st.subheader("📊 Current Status")
        if st.session_state.get('keywords'):
            st.markdown(f"**Active Filters:** {len(st.session_state.keywords)}")
        else:
            st.markdown("**Active Filters:** None")
        
        st.markdown(f"**Current Page:** {st.session_state.current_page}")
        st.markdown(f"**Total Pages:** {st.session_state.total_pages}")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """<div style='text-align: center; color: gray;'>
        🤖 RSS News Dashboard with Pagination & Filtering | Built with Streamlit<br>
        <small>📰 Browse AI/ML news • 🔍 Filter by keywords • 📄 Navigate with pagination</small>
        </div>""", 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()