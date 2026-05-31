"""
Medium Posts Viewer - Streamlit app to view exported Medium posts
"""
import streamlit as st
import os
import re
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup

# Page config
st.set_page_config(page_title="Medium Posts Viewer", page_icon="📝", layout="wide")

# Paths
MEDIUM_POSTS_DIR = Path(__file__).parent / "medium_extracted" / "posts"
DB_PATH = Path(__file__).parent / "medium_posts.db"

# Initialize database
def init_db():
    import sqlite3
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS medium_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            subtitle TEXT,
            body TEXT,
            date_published TEXT,
            url TEXT,
            filename TEXT,
            word_count INTEGER
        )
    """)
    conn.commit()
    return conn

def parse_html_file(filepath):
    """Parse a Medium HTML export file and extract content."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract title
        title_elem = soup.find('h1', class_='p-name')
        title = title_elem.get_text(strip=True) if title_elem else ""
        
        # Extract subtitle
        subtitle_elem = soup.find('section', attrs={'data-field': 'subtitle'})
        subtitle = subtitle_elem.get_text(strip=True) if subtitle_elem else ""
        
        # Extract body
        body_elem = soup.find('section', attrs={'data-field': 'body'})
        body = body_elem.get_text(strip=True) if body_elem else ""
        
        # Extract date
        time_elem = soup.find('time', class_='dt-published')
        date_published = time_elem.get('datetime', '') if time_elem else ""
        
        # Extract URL
        canonical = soup.find('a', class_='p-canonical')
        url = canonical.get('href', '') if canonical else ""
        
        # Word count
        word_count = len(body.split()) if body else 0
        
        return {
            'title': title,
            'subtitle': subtitle,
            'body': body,
            'date_published': date_published,
            'url': url,
            'filename': filepath.name,
            'word_count': word_count
        }
    except Exception as e:
        return None

def extract_all_posts(conn):
    """Extract all Medium posts from HTML files."""
    c = conn.cursor()
    
    # Check if already extracted (and not empty)
    c.execute("SELECT COUNT(*) FROM medium_posts")
    count = c.fetchone()[0]
    
    # Get all HTML files
    all_html = list(MEDIUM_POSTS_DIR.glob("*.html"))
    drafts = [f for f in all_html if f.name.startswith("draft_")]
    published = [f for f in all_html if not f.name.startswith("draft_")]
    all_files = published + drafts  # Process published first, then drafts
    
    if count > 0 and count == len(all_files):
        return count  # Already fully extracted
    
    # Clear and re-extract if partial
    if count > 0 and count < len(all_files):
        c.execute("DELETE FROM medium_posts")
        conn.commit()
    
    extracted = 0
    for filepath in all_files:
        post = parse_html_file(filepath)
        if post:
            c.execute("""
                INSERT INTO medium_posts (title, subtitle, body, date_published, url, filename, word_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                post['title'],
                post['subtitle'],
                post['body'],
                post['date_published'],
                post['url'],
                post['filename'],
                post['word_count']
            ))
            extracted += 1
    
    conn.commit()
    return extracted

def load_posts(conn, page=1, per_page=10, year_filter=None, search_query=""):
    """Load posts with pagination and filters."""
    c = conn.cursor()
    
    where_clause = "1=1"
    params = []
    
    if year_filter:
        where_clause += " AND date_published LIKE ?"
        params.append(f"{year_filter}-%")
    
    if search_query:
        where_clause += " AND (title LIKE ? OR body LIKE ?)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])
    
    offset = (page - 1) * per_page
    
    c.execute(f"""
        SELECT id, title, subtitle, body, date_published, url, word_count
        FROM medium_posts
        WHERE {where_clause}
        ORDER BY date_published DESC
        LIMIT ? OFFSET ?
    """, params + [per_page, offset])
    
    posts = c.fetchall()
    
    # Get total count
    c.execute(f"SELECT COUNT(*) FROM medium_posts WHERE {where_clause}", params)
    total = c.fetchone()[0]
    
    return posts, total

def get_available_years(conn):
    """Get list of years with posts."""
    c = conn.cursor()
    c.execute("""
        SELECT DISTINCT substr(date_published, 1, 4) as year
        FROM medium_posts
        WHERE date_published IS NOT NULL AND date_published != ''
        ORDER BY year DESC
    """)
    return [row[0] for row in c.fetchall()]

# Main app
def main():
    st.title("📝 Medium Posts Viewer")
    
    # Initialize database
    conn = init_db()
    
    # Extract posts on first run
    with st.spinner("Loading Medium posts..."):
        count = extract_all_posts(conn)
        if count > 0:
            st.success(f"Loaded {count} Medium posts")
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Get available years
    years = get_available_years(conn)
    
    year_filter = st.sidebar.selectbox(
        "Year",
        ["All Years"] + years,
        index=0
    )
    
    search_query = st.sidebar.text_input("Search posts", placeholder="Search by title or content...")
    
    # Pagination
    col1, col2, col3 = st.columns([1, 2, 1])
    
    page = int(col2.number_input("Page", min_value=1, value=1, step=1))
    per_page = st.sidebar.radio("Posts per page", [5, 10, 20], index=1, horizontal=True)
    
    # Filter by year
    year_filter_val = None if year_filter == "All Years" else year_filter
    
    # Load posts
    posts, total = load_posts(conn, page, per_page, year_filter_val, search_query)
    
    # Dashboard
    st.markdown("### 📊 Dashboard")
    col1, col2, col3 = st.columns(3)
    
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM medium_posts")
    total_posts = c.fetchone()[0]
    
    c.execute("SELECT SUM(word_count) FROM medium_posts")
    total_words = c.fetchone()[0] or 0
    
    c.execute("SELECT AVG(word_count) FROM medium_posts")
    avg_words = int(c.fetchone()[0] or 0)
    
    col1.metric("Total Posts", total_posts)
    col2.metric("Total Words", f"{total_words:,}")
    col3.metric("Avg Words/Post", avg_words)
    
    st.markdown("---")
    
    # Display posts
    if posts:
        st.markdown(f"### 📖 Showing {len(posts)} of {total} posts")
        
        for post in posts:
            post_id, title, subtitle, body, date_published, url, word_count = post
            
            with st.expander(f"📄 {title[:80]}{'...' if len(title) > 80 else ''}", expanded=False):
                # Metadata
                col_date, col_words = st.columns(2)
                
                if date_published:
                    try:
                        dt = datetime.fromisoformat(date_published.replace('Z', '+00:00'))
                        col_date.markdown(f"**Date:** {dt.strftime('%B %d, %Y')}")
                    except:
                        col_date.markdown(f"**Date:** {date_published}")
                
                col_words.markdown(f"**Words:** {word_count:,}")
                
                if subtitle:
                    st.markdown(f"*Quote: {subtitle[:100]}...*")
                
                # Body preview
                if body:
                    preview = body[:500] + "..." if len(body) > 500 else body
                    st.markdown(preview)
                
                # Links
                if url:
                    st.markdown(f"[🔗 View on Medium]({url})")
    
    else:
        st.info("No posts found matching your criteria.")
    
    conn.close()

if __name__ == "__main__":
    main()