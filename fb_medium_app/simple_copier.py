"""
Facebook → Medium Simple Copier
================================
A focused tool to browse FB posts and copy them to Medium.
No tabs, no complexity - just posts and copy buttons.
"""

import streamlit as st
import sqlite3
import os
import re
from pathlib import Path
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="📋 FB to Medium Copier",
    page_icon="📋",
    layout="wide"
)

# ==========================================
# DATABASE PATHS
# ==========================================
BASE_DIR = Path(__file__).parent.parent
FB_DB = BASE_DIR / "fb_posts.db"
MATCHED_DB = BASE_DIR / "comparison_bengali.db"
POSTING_LOG = BASE_DIR / "medium_posting_log.json"

# ==========================================
# HELPERS
# ==========================================

def fix_encoding(text):
    """Fix Bengali encoding."""
    if not text:
        return ""
    try:
        return text.encode('latin-1').decode('utf-8')
    except:
        return text

def get_db():
    """Get database connection."""
    return sqlite3.connect(FB_DB)

def get_matched_ids():
    """Get FB post IDs already on Medium (matched + manually posted)."""
    ids = set()
    
    # From comparison database (matched during comparison)
    if MATCHED_DB.exists():
        conn = sqlite3.connect(MATCHED_DB)
        ids.update(r[0] for r in conn.execute("SELECT fb_id FROM matched_bengali_posts"))
        conn.close()
    
    # From posting log (posted via Playwright)
    if POSTING_LOG.exists():
        try:
            import json
            with open(POSTING_LOG, 'r', encoding='utf-8') as f:
                log = json.load(f)
            # Only count successful posts
            ids.update(r['fb_id'] for r in log if r.get('success'))
        except:
            pass
    
    return ids

def count_words(text):
    """Count words in text."""
    if not text:
        return 0
    return len(text.split())

def categorize(content):
    """Simple categorization."""
    if not content:
        return "Other"
    content_lower = content.lower()
    if any(w in content_lower for w in ['ai', 'machine learning', 'neural', 'model']):
        return "AI/ML"
    if any(w in content_lower for w in ['python', 'code', 'programming', 'javascript']):
        return "Tech"
    if any(w in content_lower for w in ['tutorial', 'how to', 'learn']):
        return "Tutorial"
    # Check Bengali
    if re.search(r'[\u0980-\u09FF]', content):
        return "বাংলা"
    return "General"

# ==========================================
# SIDEBAR - SETTINGS & FILTERS
# ==========================================

st.sidebar.title("🔧 Settings")

# Credential configuration
st.sidebar.subheader("🔐 Medium Credentials")

# Get stored credentials or use env vars
stored_username = os.environ.get('MEDIUM_USERNAME', '')
stored_password = os.environ.get('MEDIUM_PASSWORD', '')

username_input = st.sidebar.text_input(
    "Email",
    value=stored_username,
    placeholder="your@email.com",
    key="medium_username"
)

password_input = st.sidebar.text_input(
    "Password",
    value="*" * len(stored_password) if stored_password else "",
    placeholder="••••••••",
    type="password",
    key="medium_password"
)

# Save credentials to environment
if username_input and password_input:
    os.environ['MEDIUM_USERNAME'] = username_input
    os.environ['MEDIUM_PASSWORD'] = password_input
    st.sidebar.success("✅ Credentials configured")
elif username_input or password_input:
    st.sidebar.warning("⚠️ Enter both email and password")

st.sidebar.divider()

# Show only unmatched posts?
show_unmatched_only = st.sidebar.checkbox(
    "Show only unmatched posts",
    value=True,
    help="Hide posts already on Medium"
)

# Filters
st.sidebar.subheader("📊 Filters")

# Date filter
date_filter = st.sidebar.selectbox(
    "Date range",
    ["All time", "Last 30 days", "Last 90 days", "Last year", "2024", "2023", "2022", "2021", "2020"]
)

# Category filter
category_filter = st.sidebar.selectbox(
    "Category",
    ["All", "AI/ML", "Tech", "Tutorial", "বাংলা", "General", "Other"]
)

# Word count filter
min_words = st.sidebar.slider("Min words", 0, 500, 50, step=10)

# Sort by
sort_by = st.sidebar.selectbox(
    "Sort by",
    ["Newest first", "Oldest first", "Most words", "Least words"]
)

# ==========================================
# MAIN CONTENT
# ==========================================

st.title("📋 Facebook → Medium Copier")
st.caption("Click on any post to copy its content, then paste in Medium")

# Get stats
conn = get_db()
total_posts = conn.execute("SELECT COUNT(*) FROM fb_text_posts").fetchone()[0]

# Get matched from both sources
matched_ids = get_matched_ids()

# Count how many were posted via Playwright specifically
playwright_posted = 0
if POSTING_LOG.exists():
    try:
        with open(POSTING_LOG, 'r', encoding='utf-8') as f:
            log = json.load(f)
        playwright_posted = sum(1 for r in log if r.get('success'))
    except:
        pass

unmatched_count = total_posts - len(matched_ids)

# Show quick stats
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total FB Posts", f"{total_posts:,}")
with col2:
    st.metric("Already on Medium", f"{len(matched_ids):,}")
with col3:
    st.metric("Posted via Bot", f"{playwright_posted:,}")
with col4:
    st.metric("Available", f"{unmatched_count:,}")

st.divider()

# ==========================================
# POSTS LIST
# ==========================================

# Build query
query = "SELECT id, date, content, post_type, word_count, has_media FROM fb_text_posts WHERE content IS NOT NULL"
params = []

# Date filter
today = datetime.now()
if date_filter == "Last 30 days":
    cutoff = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    query += " AND date >= ?"
    params.append(cutoff)
elif date_filter == "Last 90 days":
    cutoff = (today - timedelta(days=90)).strftime("%Y-%m-%d")
    query += " AND date >= ?"
    params.append(cutoff)
elif date_filter == "Last year":
    cutoff = (today - timedelta(days=365)).strftime("%Y-%m-%d")
    query += " AND date >= ?"
    params.append(cutoff)
elif date_filter != "All time":
    year = date_filter
    query += " AND date LIKE ?"
    params.append(f"{year}%")

# Word count filter
query += " AND word_count >= ?"
params.append(min_words)

# Exclude matched if needed
if show_unmatched_only and matched_ids:
    placeholders = ','.join('?' * len(matched_ids))
    query += f" AND id NOT IN ({placeholders})"
    params.extend(list(matched_ids))

# Sort
if sort_by == "Newest first":
    query += " ORDER BY date DESC"
elif sort_by == "Oldest first":
    query += " ORDER BY date ASC"
elif sort_by == "Most words":
    query += " ORDER BY word_count DESC"
else:
    query += " ORDER BY word_count ASC"

# Execute
posts = conn.execute(query, params).fetchall()
conn.close()

st.subheader(f"📝 {len(posts)} posts found")

# ==========================================
# INDIVIDUAL POST CARDS
# ==========================================

if not posts:
    st.info("📭 No posts match your filters")
else:
    for post in posts:
        post_id, date, content, post_type, word_count, has_media = post
        
        # Fix encoding
        content = fix_encoding(content)
        
        # Category
        cat = categorize(content)
        
        # Show filter for category
        if category_filter != "All" and cat != category_filter:
            continue
        
        with st.container():
            # Post header
            cols = st.columns([6, 1, 1, 1])
            with cols[0]:
                st.markdown(f"**📅 {date[:10]}** • {word_count} words")
            with cols[1]:
                st.caption(f"🗂️ {post_type or 'post'}")
            with cols[2]:
                st.caption(f"📁 {cat}")
            with cols[3]:
                if has_media:
                    st.caption("🖼️")
            
            # Content preview (truncated)
            preview = content[:300] + "..." if len(content) > 300 else content
            
            # Show first 300 chars in a code block for easy reading
            st.text_area(
                "Content",
                value=preview,
                height=100,
                key=f"post_{post_id}",
                disabled=True
            )
            
            # Action buttons
            cols2 = st.columns([1, 1, 1])
            with cols2[0]:
                # Copy full content
                if st.button(f"📋 Copy", key=f"copy_{post_id}"):
                    st.session_state.copy_buffer = content
                    st.success("✅ Copied to clipboard!")
            
            with cols2[1]:
                # View full content
                if st.button(f"👁️ View Full", key=f"view_{post_id}"):
                    st.session_state[f'show_{post_id}'] = not st.session_state.get(f'show_{post_id}', False)
            
            with cols2[2]:
                # Playwright automation button
                if st.button(f"🤖 Post to Medium", key=f"playwright_{post_id}"):
                    with st.spinner("🤖 Opening browser..."):
                        from fb_medium_app.medium_playwright import post_single_with_playwright
                        result = post_single_with_playwright(post_id, headless=True)
                    
                    if result.get('success'):
                        st.success(f"✅ Draft created! Post #{post_id} marked as posted.")
                        # Clear clipboard area to show new content
                        st.session_state.copy_buffer = ""
                    else:
                        st.error(f"❌ Failed: {result.get('error', 'Check credentials in Settings')}")
            
            # Show full content if toggled
            if st.session_state.get(f'show_{post_id}', False):
                st.text_area(
                    "Full Content",
                    value=content,
                    height=200,
                    key=f"full_{post_id}"
                )
                copy_col, _ = st.columns([1, 3])
                with copy_col:
                    if st.button(f"📋 Copy Full Post", key=f"copyfull_{post_id}"):
                        st.session_state.copy_buffer = content
                        st.success("✅ Content saved - scroll down to clipboard")
            
            st.divider()

# ==========================================
# CLIPBOARD AREA
# ==========================================

st.divider()
st.subheader("📋 Clipboard")

# Initialize clipboard in session state
if 'copy_buffer' not in st.session_state:
    st.session_state.copy_buffer = ""

# Show current clipboard content
clipboard_content = st.text_area(
    "Paste this content into Medium:",
    value=st.session_state.copy_buffer,
    height=300,
    key="main_clipboard",
    help="Click 'Copy Full Post' on any post above to load content here"
)

# Update session state
st.session_state.copy_buffer = clipboard_content

# Clear button
if st.button("🗑️ Clear Clipboard"):
    st.session_state.copy_buffer = ""
    st.rerun()

# Copy to system clipboard button
if st.session_state.copy_buffer:
    st.info("💡 Select all text in the box above (Ctrl+A) and copy (Ctrl+C)")

# ==========================================
# FOOTER
# ==========================================

st.divider()
st.caption("📘 FB → Medium Copier | Simple tool for cross-posting")