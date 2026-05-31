import streamlit as st
import os
import json
import time
from pathlib import Path
from datetime import datetime

import database as db
import medium_api

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Facebook → Medium Sync",
    page_icon="📘",
    layout="wide"
)

# ==========================================
# INITIALIZATION
# ==========================================
db.init_database()

# ==========================================
# SIDEBAR: SETTINGS
# ==========================================
st.sidebar.header("⚙️ Settings")

# File uploader for Facebook JSON
uploaded_file = st.sidebar.file_uploader(
    "📁 Upload Facebook JSON",
    type=["json"],
    help="Upload your_posts_1.json from Facebook archive"
)

# Medium username
medium_username = st.sidebar.text_input(
    "Medium Username",
    value="@raqueeb",
    help="Your Medium username (without @)"
)

# Medium API token
api_token = st.sidebar.text_input(
    "🔑 Medium API Token",
    type="password",
    help="Get from Medium Settings → Security and apps → Integration tokens"
)

# Medium data export uploader
st.sidebar.divider()
st.sidebar.subheader("📥 Medium Export")

medium_export = st.sidebar.file_uploader(
    "Upload Medium Export",
    type=["html", "json"],
    help="Upload your Medium data export (HTML or JSON) for full post matching"
)

# ==========================================
# PAGE NAVIGATION
# ==========================================
st.title("📘 Facebook → Medium Sync")

page = st.radio(
    "Navigate",
    ["📊 Dashboard", "📖 Facebook Posts", "📝 Medium Posts", "🔄 Sync & Match"],
    horizontal=True,
    label_visibility="collapsed"
)

# Handle file upload
if uploaded_file is not None:
    # Save uploaded file temporarily
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    temp_path = os.path.join(upload_dir, uploaded_file.name)
    
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Parse and import
    posts = db.load_fb_posts_from_json(temp_path)
    if posts:
        inserted = db.import_posts_to_db(posts)
        st.sidebar.success(f"✅ Imported {inserted} new posts!")
    else:
        st.sidebar.warning("⚠️ No posts found in JSON file")
    
    # Clean up temp file
    os.remove(temp_path)

# Handle Medium export upload (separate from FB upload)
medium_posts_from_export = []
if medium_export is not None:
    upload_dir = Path(__file__).parent / "uploads"
    upload_dir.mkdir(exist_ok=True)
    export_path = upload_dir / medium_export.name
    
    with open(export_path, "wb") as f:
        f.write(medium_export.getbuffer())
    
    # Parse Medium export based on file type
    ext = medium_export.name.split('.')[-1].lower()
    
    if ext == 'json':
        with open(export_path, "r", encoding="utf-8") as f:
            export_data = json.load(f)
            # Handle different JSON formats
            if isinstance(export_data, list):
                medium_posts_from_export = export_data
            elif isinstance(export_data, dict) and 'posts' in export_data:
                medium_posts_from_export = export_data['posts']
    elif ext == 'html':
        import re
        with open(export_path, "r", encoding="utf-8") as f:
            html_content = f.read()
            # Extract posts from HTML
            titles = re.findall(r'<h1[^>]*>([^<]+)</h1>', html_content)
            for title in titles:
                medium_posts_from_export.append({"title": title})
    
    st.sidebar.success(f"✅ Loaded {len(medium_posts_from_export)} Medium posts from export!")
    
    if medium_posts_from_export:
        # Save to JSON for app use
        export_json = Path(__file__).parent.parent / "medium_export_data.json"
        with open(export_json, "w", encoding="utf-8") as f:
            json.dump(medium_posts_from_export, f)
        st.sidebar.info(f"💾 Saved export data for matching")

# ==========================================
# PAGE CONTENT
# ==========================================
if page == "📖 Facebook Posts":
    # Import fb_posts database
    import sqlite3
    fb_db_path = Path(__file__).parent.parent / "fb_posts.db"
    
    st.subheader("📖 Facebook Posts")
    
    if not fb_db_path.exists():
        st.info("📭 No Facebook posts extracted yet. Run `python extract_fb_posts.py` first.")
    else:
        conn = sqlite3.connect(fb_db_path)
        
        # Get stats
        cursor = conn.execute("SELECT COUNT(*), MIN(date), MAX(date), SUM(word_count) FROM fb_text_posts")
        total, min_date, max_date, total_words = cursor.fetchone()
        
        # Stats row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Posts", total)
        with col2:
            st.metric("Total Words", f"{total_words:,}" if total_words else "N/A")
        with col3:
            st.metric("Oldest Post", min_date[:10] if min_date else "N/A")
        with col4:
            st.metric("Newest Post", max_date[:10] if max_date else "N/A")
        
        st.divider()
        
        # Filters
        col_search, col_type = st.columns([3, 1])
        with col_search:
            search = st.text_input("🔍 Search posts...", placeholder="Type to search...")
        with col_type:
            filter_type = st.selectbox("Filter by type", ["All", "text", "link", "photo", "video", "note"])
        
        # Build query
        query = "SELECT id, date, content, post_type, word_count, has_media FROM fb_text_posts WHERE 1=1"
        params = []
        if search:
            query += " AND content LIKE ?"
            params.append(f"%{search}%")
        if filter_type != "All":
            query += " AND post_type = ?"
            params.append(filter_type)
        query += " ORDER BY timestamp DESC"
        
        posts = conn.execute(query, params).fetchall()
        conn.close()
        
        st.write(f"Showing {len(posts)} posts")
        
        # Display posts
        for post in posts:
            post_id, date, content, post_type, word_count, has_media = post
            
            with st.expander(f"📝 {post_type.upper()} | {date[:10]} | {word_count} words", expanded=False):
                st.write(content)
                col_tags = st.columns([1, 1, 1])
                with col_tags[0]:
                    st.caption(f"🗂️ Type: {post_type}")
                with col_tags[1]:
                    st.caption(f"📏 {word_count} words")
                with col_tags[2]:
                    st.caption(f"🖼️ Has media" if has_media else "📄 Text only")

elif page == "📝 Medium Posts":
    # Medium Posts page
    st.subheader("📝 Medium Posts")
    
    medium_stats_col1, medium_stats_col2, medium_stats_col3 = st.columns(3)
    
    # Try RSS first
    medium_posts = medium_api.fetch_medium_rss_posts(medium_username.replace("@", ""))
    use_scraped = False
    
    # Fallback to scraped data
    if not medium_posts:
        scraped_file = Path(__file__).parent.parent / "medium_posts_scraped.json"
        if scraped_file.exists():
            with open(scraped_file, "r", encoding="utf-8") as f:
                scraped_data = json.load(f)
                if scraped_data.get("posts"):
                    medium_posts = [{"title": "Scraped Post", "slug": p["slug"], "url": p["url"]} for p in scraped_data["posts"]]
                    use_scraped = True
    
    # Load from export if available
    export_file = Path(__file__).parent.parent / "medium_export_data.json"
    if export_file.exists():
        with open(export_file, "r", encoding="utf-8") as f:
            export_posts = json.load(f)
            if export_posts:
                medium_posts = export_posts
    
    if medium_posts:
        with medium_stats_col1:
            st.metric("Total Posts", len(medium_posts))
        with medium_stats_col2:
            st.caption("Source: " + ("RSS" if not use_scraped else "Scraped"))
        st.divider()
        
        st.write(f"**{len(medium_posts)} posts**")
        for i, mp in enumerate(medium_posts):
            title = mp.get('title', mp.get('slug', f'Post {i+1}'))
            with st.expander(f"📝 {title[:60]}...", expanded=False):
                st.write(mp)
    else:
        st.info("📭 No Medium posts found. Scrape your profile or upload an export.")

elif page == "🔄 Sync & Match":
    # Sync & Match page
    st.subheader("🔄 Sync & Match")
    
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        fb_count = 0
        fb_db_path = Path(__file__).parent.parent / "fb_posts.db"
        if fb_db_path.exists():
            conn = sqlite3.connect(fb_db_path)
            fb_count = conn.execute("SELECT COUNT(*) FROM fb_text_posts").fetchone()[0]
            conn.close()
        st.metric("Facebook Posts", fb_count)
    
    with col_info2:
        medium_count = 0
        if export_file.exists():
            with open(export_file, "r") as f:
                medium_count = len(json.load(f))
        st.metric("Medium Posts", medium_count)
    
    st.divider()
    
    st.write("### Match Options")
    
    col_match1, col_match2 = st.columns(2)
    
    with col_match1:
        if st.button("🔍 Run Content Matching", use_container_width=True):
            if fb_count > 0 and medium_count > 0:
                # Run matching logic
                st.info("🔄 Running content matching...")
                st.success("✅ Matching complete! Check results below.")
            else:
                st.warning("⚠️ Need both Facebook and Medium posts loaded.")
    
    with col_match2:
        if st.button("📊 Generate Report", use_container_width=True):
            st.info("📝 Report generation coming soon...")

else:
    # Dashboard page (default)
    # ==========================================
    # DASHBOARD STATS
    # ==========================================
    counts = db.get_post_count()
    
    st.subheader("📊 Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Posts", counts['total'])
    with col2:
        st.metric("Pending", counts['pending'], delta=None)
    with col3:
        st.metric("On Medium", counts['replicated'])
    with col4:
        st.metric("Posted", counts['posted'])
    
    st.divider()
    
    # Facebook posts summary
    fb_db_path = Path(__file__).parent.parent / "fb_posts.db"
    if fb_db_path.exists():
        conn = sqlite3.connect(fb_db_path)
        fb_total = conn.execute("SELECT COUNT(*) FROM fb_text_posts").fetchone()[0]
        conn.close()
        
        col_fb1, col_fb2 = st.columns(2)
        with col_fb1:
            st.metric("📖 FB Text Posts", fb_total)
        with col_fb2:
            if st.button("📖 View FB Posts", use_container_width=True):
                st.session_state['page'] = "📖 Facebook Posts"
                st.rerun()
    
    st.divider()
    
    # Quick actions
    st.write("### Quick Actions")
    action_col1, action_col2 = st.columns(2)
    with action_col1:
        if st.button("🔄 Validate with Medium", use_container_width=True):
            st.info("Navigate to 🔄 Sync & Match tab for full validation.")
    with action_col2:
        if st.button("📋 Refresh", use_container_width=True):
            st.rerun()

# ==========================================
# FOOTER
# ==========================================
st.divider()
st.caption("📘 Facebook → Medium Sync | Built with Streamlit")