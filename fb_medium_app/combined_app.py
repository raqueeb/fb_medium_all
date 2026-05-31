"""
Combined Facebook → Medium Sync Application
============================================
5-tab interface for browsing, comparing, and automating post cross-posting.
"""

import streamlit as st
import sqlite3
import os
import json
import re
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher

# Page configuration
st.set_page_config(
    page_title="📘 FB Medium Sync",
    page_icon="📘",
    layout="wide"
)

# ==========================================
# DATABASE PATHS
# ==========================================
BASE_DIR = Path(__file__).parent.parent
FB_DB = BASE_DIR / "fb_posts.db"
COMPARISON_DB = BASE_DIR / "comparison_bengali.db"

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def fix_bengali_text(text):
    """Fix Bengali encoding issues."""
    if not text:
        return ""
    try:
        # Common fix for encoding issues
        return text.encode('latin-1').decode('utf-8')
    except:
        return text

def is_bengali(text):
    """Check if text contains Bengali characters."""
    if not text:
        return False
    bengali_pattern = re.compile(r'[\u0980-\u09FF]')
    return bool(bengali_pattern.search(text))

def extract_bengali_content(text):
    """Extract Bengali portions from mixed content."""
    if not text:
        return ""
    # Split by newlines and keep lines with Bengali
    lines = text.split('\n')
    bengali_lines = [line for line in lines if is_bengali(line)]
    return '\n'.join(bengali_lines)

def count_bengali_words(text):
    """Count Bengali words in text."""
    if not text:
        return 0
    words = text.split()
    return sum(1 for w in words if is_bengali(w))

def categorize_post(content):
    """Auto-categorize post based on keywords."""
    content_lower = content.lower()
    
    categories = {
        'ML/AI': ['machine learning', 'ai', 'artificial intelligence', 'deep learning', 'neural', 'model', 'training'],
        'Tech': ['technology', 'software', 'programming', 'code', 'developer', 'python', 'javascript'],
        'Opinion': ['think', 'believe', 'feel', 'opinion', 'perspective', 'personal'],
        'News': ['news', 'update', 'announcement', 'report', 'breaking'],
        'Tutorial': ['how to', 'tutorial', 'guide', 'learn', 'step', 'example'],
        'Personal': ['my', 'i ', ' personal', 'life', 'day', 'today', 'yesterday'],
        'বাংলা': []  # Auto-categorize all Bengali as বাংলা if no other match
    }
    
    # Check for category matches
    for category, keywords in categories.items():
        if category == 'বাংলা':
            if is_bengali(content):
                return 'বাংলা'
            continue
        for keyword in keywords:
            if keyword in content_lower:
                return category
    
    return 'Other'

def get_db_connection(db_path):
    """Create database connection."""
    return sqlite3.connect(db_path)

def shorten_url(url):
    """Shorten Medium URLs for display."""
    if not url:
        return ""
    # Remove the long hash and simplify
    url = url.replace("?source=---------", "")
    url = url.replace("?source=---", "")
    return url if len(url) < 60 else url[:57] + "..."

def get_fb_stats():
    """Get Facebook posts statistics."""
    if not FB_DB.exists():
        return None
    
    conn = get_db_connection(FB_DB)
    stats = {}
    
    stats['total'] = conn.execute("SELECT COUNT(*) FROM fb_text_posts").fetchone()[0]
    stats['with_media'] = conn.execute("SELECT COUNT(*) FROM fb_text_posts WHERE has_media=1").fetchone()[0]
    stats['text_only'] = stats['total'] - stats['with_media']
    
    result = conn.execute("SELECT MIN(date), MAX(date), SUM(word_count) FROM fb_text_posts").fetchone()
    stats['oldest'] = result[0]
    stats['newest'] = result[1]
    stats['total_words'] = result[2] or 0
    
    conn.close()
    return stats

def get_medium_stats():
    """Get Medium posts statistics from comparison database."""
    if not COMPARISON_DB.exists():
        return None
    
    conn = get_db_connection(COMPARISON_DB)
    stats = {}
    
    matched_count = conn.execute("SELECT COUNT(*) FROM matched_bengali_posts").fetchone()[0]
    unmatched_count = conn.execute("SELECT COUNT(*) FROM unmatched_bengali_posts").fetchone()[0]
    stats['total'] = matched_count + unmatched_count
    stats['matched'] = matched_count
    stats['unmatched'] = unmatched_count
    
    conn.close()
    return stats

def get_unmatched_fb_posts(limit=100, offset=0, category=None, year=None, min_words=None):
    """
    Get FB posts that are NOT used for Medium posts.
    These are candidates for future cross-posting.
    """
    if not FB_DB.exists() or not COMPARISON_DB.exists():
        return []
    
    conn = get_db_connection(FB_DB)
    
    # Get IDs of FB posts that are matched to Medium
    comp_conn = get_db_connection(COMPARISON_DB)
    matched_ids = [r[0] for r in comp_conn.execute("SELECT fb_id FROM matched_bengali_posts")]
    comp_conn.close()
    
    # Build query for unmatched posts
    query = """
        SELECT id, timestamp, date, content, post_type, word_count, char_count, has_media
        FROM fb_text_posts 
        WHERE id NOT IN ({})
        AND content IS NOT NULL
        AND length(content) > 50
    """.format(','.join('?' * len(matched_ids)) if matched_ids else "SELECT -1")
    
    params = list(matched_ids) if matched_ids else []
    
    if category:
        # Filter by category (need to categorize first)
        pass  # Handle in Python after fetch
    
    if year:
        query += " AND date LIKE ?"
        params.append(f"{year}%")
    
    if min_words:
        query += " AND word_count >= ?"
        params.append(min_words)
    
    query += " ORDER BY date DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    posts = conn.execute(query, params).fetchall()
    conn.close()
    
    # Add category to each post
    result = []
    for post in posts:
        post_id, timestamp, date, content, post_type, word_count, char_count, has_media = post
        fixed_content = fix_bengali_text(content)
        cat = categorize_post(fixed_content)
        result.append({
            'id': post_id,
            'timestamp': timestamp,
            'date': date,
            'content': fixed_content,
            'post_type': post_type,
            'word_count': word_count,
            'char_count': char_count,
            'has_media': has_media,
            'category': cat
        })
    
    # Filter by category in Python if needed
    if category:
        result = [p for p in result if p['category'] == category]
    
    return result

def get_category_stats():
    """Get statistics for each category."""
    posts = get_unmatched_fb_posts(limit=10000)
    stats = {}
    for post in posts:
        cat = post['category']
        if cat not in stats:
            stats[cat] = 0
        stats[cat] += 1
    return stats

# ==========================================
# INITIALIZATION
# ==========================================
if 'copy_buffer' not in st.session_state:
    st.session_state.copy_buffer = ""

# ==========================================
# SIDEBAR
# ==========================================
st.sidebar.header("⚙️ Settings")

# Medium credentials from environment
st.sidebar.subheader("🔐 Medium Credentials")
medium_user = os.environ.get('MEDIUM_USERNAME', '')
medium_pass = os.environ.get('MEDIUM_PASSWORD', '')

if medium_user and medium_pass:
    st.sidebar.success("✅ Credentials loaded from environment")
else:
    st.sidebar.warning("⚠️ Set MEDIUM_USERNAME and MEDIUM_PASSWORD environment variables")

# Stats summary
st.sidebar.divider()
st.sidebar.subheader("📊 Quick Stats")

fb_stats = get_fb_stats()
if fb_stats:
    st.sidebar.metric("FB Posts", fb_stats['total'])
    st.sidebar.caption(f"📅 {fb_stats['oldest'][:10]} to {fb_stats['newest'][:10]}")

comp_stats = get_medium_stats()
if comp_stats:
    st.sidebar.metric("Matched", comp_stats['matched'])
    st.sidebar.metric("Unmatched Medium", comp_stats['unmatched'])

# ==========================================
# MAIN TABS
# ==========================================
tabs = st.tabs(["🏠 Home", "📖 Facebook", "📝 Medium", "🔄 Compare", "📋 Unmatched Queue"])

# ==========================================
# TAB 1: HOME DASHBOARD
# ==========================================
with tabs[0]:
    st.title("📘 Facebook → Medium Sync")
    st.caption("Combined dashboard for browsing, comparing, and automating post cross-posting")
    
    st.divider()
    
    # Main stats row
    col1, col2, col3, col4 = st.columns(4)
    
    if fb_stats:
        with col1:
            st.metric("Facebook Posts", fb_stats['total'])
        with col2:
            st.metric("Total Words", f"{fb_stats['total_words']:,}")
        with col3:
            st.metric("Text Only", fb_stats['text_only'])
        with col4:
            st.metric("With Media", fb_stats['with_media'])
    
    st.divider()
    
    # Comparison stats
    st.subheader("📊 Cross-Posting Status")
    
    if comp_stats:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("On Medium", comp_stats['matched'])
        with col2:
            st.metric("Not Matched", comp_stats['unmatched'])
        with col3:
            match_rate = (comp_stats['matched'] / comp_stats['total'] * 100) if comp_stats['total'] > 0 else 0
            st.metric("Match Rate", f"{match_rate:.1f}%")
    
    # Unmatched FB posts (candidates)
    conn = get_db_connection(FB_DB)
    if COMPARISON_DB.exists():
        comp_conn = get_db_connection(COMPARISON_DB)
        matched_ids = [r[0] for r in comp_conn.execute("SELECT fb_id FROM matched_bengali_posts")]
        comp_conn.close()
        
        if matched_ids:
            placeholders = ','.join('?' * len(matched_ids))
            unmatched_count = conn.execute(f"SELECT COUNT(*) FROM fb_text_posts WHERE id NOT IN ({placeholders}) AND word_count > 50", matched_ids).fetchone()[0]
        else:
            unmatched_count = conn.execute("SELECT COUNT(*) FROM fb_text_posts WHERE word_count > 50").fetchone()[0]
    else:
        unmatched_count = 0
    conn.close()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🔴 Unmatched FB Posts (Queue)", unmatched_count)
    with col2:
        if st.button("📋 Go to Unmatched Queue →", use_container_width=True):
            st.session_state['active_tab'] = 4
            st.rerun()
    
    st.divider()
    
    # Quick actions
    st.subheader("🚀 Quick Actions")
    
    action_col1, action_col2, action_col3 = st.columns(3)
    with action_col1:
        if st.button("🔍 Browse FB Posts", use_container_width=True):
            st.session_state['active_tab'] = 1
            st.rerun()
    with action_col2:
        if st.button("🔄 View Matches", use_container_width=True):
            st.session_state['active_tab'] = 3
            st.rerun()
    with action_col3:
        if st.button("📤 Export Queue", use_container_width=True):
            posts = get_unmatched_fb_posts(limit=1000)
            data = [{'id': p['id'], 'date': p['date'], 'words': p['word_count'], 'type': p['post_type']} for p in posts]
            st.download_button(
                "Download Queue CSV",
                data=json.dumps(data, ensure_ascii=False),
                file_name="unmatched_queue.json",
                mime="application/json"
            )

# ==========================================
# TAB 2: FACEBOOK POSTS
# ==========================================
with tabs[1]:
    st.title("📖 Facebook Posts")
    
    if not FB_DB.exists():
        st.info("📭 No Facebook posts database found. Run `python extract_fb_posts.py` first.")
    else:
        conn = get_db_connection(FB_DB)
        
        # Filters
        col_search, col_type, col_year = st.columns([3, 1, 1])
        with col_search:
            search = st.text_input("🔍 Search posts...", placeholder="Search in content...")
        with col_type:
            filter_type = st.selectbox("Type", ["All", "text", "link", "photo", "video", "note"])
        with col_year:
            years = ["All Years"] + [str(y) for y in range(2024, 2009, -1)]
            year_filter = st.selectbox("Year", years)
        
        # Build query
        query = "SELECT id, date, content, post_type, word_count, char_count, has_media, status FROM fb_text_posts WHERE 1=1"
        params = []
        
        if search:
            query += " AND content LIKE ?"
            params.append(f"%{search}%")
        if filter_type != "All":
            query += " AND post_type = ?"
            params.append(filter_type)
        if year_filter != "All Years":
            query += " AND date LIKE ?"
            params.append(f"{year_filter}%")
        
        query += " ORDER BY timestamp DESC LIMIT 200"
        
        posts = conn.execute(query, params).fetchall()
        conn.close()
        
        st.write(f"📊 Showing {len(posts)} posts (sorted by newest)")
        
        # Pagination
        page = st.number_input("Page", min_value=1, max_value=max(1, (len(posts) - 1) // 20 + 1), value=1)
        start_idx = (page - 1) * 20
        end_idx = start_idx + 20
        page_posts = posts[start_idx:end_idx]
        
        for post in page_posts:
            post_id, date, content, post_type, word_count, char_count, has_media, status = post
            
            fixed_content = fix_bengali_text(content)
            status_emoji = "✅" if status == "posted" else "⏳" if status == "pending" else "📄"
            
            with st.expander(f"{status_emoji} {post_type.upper()} | {date[:10]} | {word_count} words | ID: {post_id}", expanded=False):
                st.write(fixed_content[:500] + "..." if len(fixed_content) > 500 else fixed_content)
                
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.caption(f"🗂️ {post_type}")
                with col_b:
                    st.caption(f"📏 {word_count} words")
                with col_c:
                    if has_media:
                        st.caption("🖼️ Has media")
                    else:
                        st.caption("📄 Text only")
                
                # Copy button
                if st.button(f"📋 Copy to Clipboard", key=f"copy_{post_id}"):
                    st.session_state.copy_buffer = fixed_content
                    st.success("Copied to clipboard!")
                
                if st.session_state.copy_buffer:
                    st.text_area("📋 Clipboard", value=st.session_state.copy_buffer, height=100, key=f"clip_{post_id}")

# ==========================================
# TAB 3: MEDIUM POSTS
# ==========================================
with tabs[2]:
    st.title("📝 Medium Posts")
    
    if not COMPARISON_DB.exists():
        st.info("📭 No comparison database found. Run comparison first.")
    else:
        conn = get_db_connection(COMPARISON_DB)
        
        # Stats
        matched = conn.execute("SELECT COUNT(*) FROM matched_bengali_posts").fetchone()[0]
        unmatched = conn.execute("SELECT COUNT(*) FROM unmatched_bengali_posts").fetchone()[0]
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("✅ Matched with FB", matched)
        with col2:
            st.metric("❌ Not Matched", unmatched)
        
        st.divider()
        
        # View options
        view_type = st.radio("View", ["Matched (from FB)", "Unmatched (no FB source)"], horizontal=True)
        
        if view_type == "Matched (from FB)":
            posts = conn.execute("""
                SELECT id, fb_id, fb_date, md_title, md_content, md_date, similarity, matched_date
                FROM matched_bengali_posts
                ORDER BY matched_date DESC
                LIMIT 100
            """).fetchall()
            
            for post in posts:
                pid, fb_id, fb_date, md_title, md_content, md_date, similarity, matched_date = post
                
                with st.expander(f"🔗 FB#{fb_id} → Medium | {similarity*100:.0f}% | {md_date[:10] if md_date else 'N/A'}", expanded=False):
                    st.write(f"**Title:** {md_title[:100] if md_title else 'N/A'}")
                    if md_content:
                        st.write(fixed_content := fix_bengali_text(md_content[:300]))
                    st.caption(f"FB Date: {fb_date[:10] if fb_date else 'N/A'} | Matched: {matched_date[:10] if matched_date else 'N/A'}")
        else:
            posts = conn.execute("""
                SELECT id, md_id, md_title, fb_id
                FROM unmatched_bengali_posts
                ORDER BY id DESC
                LIMIT 100
            """).fetchall()
            
            for post in posts:
                pid, md_id, md_title, fb_id = post
                st.write(f"- MD#{md_id}: {md_title[:60] if md_title else 'No title'} (no FB match)")

# ==========================================
# TAB 4: COMPARE
# ==========================================
with tabs[3]:
    st.title("🔄 Compare Results")
    st.caption("Detailed view of matched and unmatched posts")
    
    if not COMPARISON_DB.exists():
        st.info("📭 No comparison data. Run comparison first.")
    else:
        conn = get_db_connection(COMPARISON_DB)
        
        # Overview stats
        matched = conn.execute("SELECT COUNT(*) FROM matched_bengali_posts").fetchone()[0]
        unmatched = conn.execute("SELECT COUNT(*) FROM unmatched_bengali_posts").fetchone()[0]
        
        # Similarity distribution
        high_sim = conn.execute("SELECT COUNT(*) FROM matched_bengali_posts WHERE similarity >= 0.95").fetchone()[0]
        mid_sim = conn.execute("SELECT COUNT(*) FROM matched_bengali_posts WHERE similarity >= 0.8 AND similarity < 0.95").fetchone()[0]
        low_sim = conn.execute("SELECT COUNT(*) FROM matched_bengali_posts WHERE similarity >= 0.5 AND similarity < 0.8").fetchone()[0]
        
        st.subheader("📈 Similarity Distribution")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Exact (≥95%)", high_sim)
        with col2:
            st.metric("Near (80-94%)", mid_sim)
        with col3:
            st.metric("Edited (50-79%)", low_sim)
        with col4:
            st.metric("Unmatched", unmatched)
        
        st.divider()
        
        # View matches by similarity
        sim_filter = st.slider("Minimum Similarity", 0.0, 1.0, 0.5, 0.05)
        
        matches = conn.execute("""
            SELECT fb_id, fb_date, fb_content, md_title, md_content, similarity
            FROM matched_bengali_posts
            WHERE similarity >= ?
            ORDER BY similarity DESC
            LIMIT 50
        """, (sim_filter,)).fetchall()
        
        st.write(f"📊 Showing {len(matches)} matches with ≥{sim_filter*100:.0f}% similarity")
        
        for m in matches:
            fb_id, fb_date, fb_content, md_title, md_content, similarity = m
            
            with st.expander(f"🔗 FB#{fb_id} ↔ MD | {similarity*100:.0f}% | {fb_date[:10] if fb_date else 'N/A'}", expanded=False):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write("**Facebook Post**")
                    st.write(fix_bengali_text(fb_content[:300]) if fb_content else "(empty)")
                    st.caption(f"Date: {fb_date[:10] if fb_date else 'N/A'}")
                with col_b:
                    st.write("**Medium Post**")
                    st.write(f"**{md_title[:100] if md_title else 'No title'}**")
                    if md_content:
                        st.write(fix_bengali_text(md_content[:200]))
        
        conn.close()

# ==========================================
# TAB 5: UNMATCHED QUEUE (PRIORITY)
# ==========================================
with tabs[4]:
    st.title("📋 Unmatched FB Posts Queue")
    st.caption("Facebook posts NOT on Medium - candidates for future cross-posting")
    
    if not FB_DB.exists():
        st.info("📭 No Facebook posts database found.")
    else:
        # Get category stats
        cat_stats = get_category_stats()
        
        col1, col2 = st.columns(2)
        with col1:
            total_unmatched = sum(cat_stats.values())
            st.metric("📊 Total Unmatched Posts", total_unmatched)
        with col2:
            st.metric("📁 Categories", len(cat_stats))
        
        st.divider()
        
        # Category breakdown
        st.subheader("📁 By Category")
        cat_cols = st.columns(min(len(cat_stats), 5))
        for i, (cat, count) in enumerate(sorted(cat_stats.items(), key=lambda x: -x[1])):
            with cat_cols[i % 5]:
                st.metric(cat, count)
        
        st.divider()
        
        # Filters
        st.subheader("🔍 Filter Queue")
        col_cat, col_year, col_words = st.columns([1, 1, 1])
        with col_cat:
            cat_filter = st.selectbox("Category", ["All"] + list(cat_stats.keys()))
        with col_year:
            years = ["All"] + [str(y) for y in range(2024, 2009, -1)]
            year_filter = st.selectbox("Year", years)
        with col_words:
            min_words = st.number_input("Min Words", min_value=0, max_value=1000, value=50)
        
        # Fetch posts
        kwargs = {'limit': 100}
        if cat_filter != "All":
            kwargs['category'] = cat_filter
        if year_filter != "All":
            kwargs['year'] = year_filter
        if min_words > 0:
            kwargs['min_words'] = min_words
        
        posts = get_unmatched_fb_posts(**kwargs)
        
        st.write(f"📋 Showing {len(posts)} posts")
        
        # Batch copy feature
        if posts:
            all_content = "\n\n---\n\n".join([f"[{p['date'][:10]}] {p['content']}" for p in posts[:20]])
            
            if st.button("📋 Copy First 20 Posts", use_container_width=True):
                st.session_state.copy_buffer = all_content
                st.success("Copied 20 posts to clipboard!")
        
        # Display posts
        for post in posts[:50]:
            cat = post['category']
            has_bengali = is_bengali(post['content'])
            emoji = "🇧🇩" if has_bengali else "🌐"
            
            with st.expander(f"{emoji} {cat} | {post['post_type']} | {post['date'][:10]} | {post['word_count']} words | ID: {post['id']}", expanded=False):
                st.write(post['content'][:500] + "..." if len(post['content']) > 500 else post['content'])
                
                col_a, col_b, col_c, col_d = st.columns(4)
                with col_a:
                    st.caption(f"🗂️ {post['post_type']}")
                with col_b:
                    st.caption(f"📏 {post['word_count']} words")
                with col_c:
                    st.caption(f"📁 {cat}")
                with col_d:
                    if post['has_media']:
                        st.caption("🖼️ Media")
                
                # Individual copy button
                cols = st.columns([1, 1, 1])
                with cols[0]:
                    if st.button(f"📋 Copy", key=f"ucopy_{post['id']}"):
                        st.session_state.copy_buffer = post['content']
                        st.success("Copied!")
                
                with cols[1]:
                    if st.button(f"🤖 Post to Medium", key=f"autopost_{post['id']}"):
                        # Import automation function
                        from fb_medium_app.medium_playwright import post_single_with_playwright
                        
                        with st.spinner("🤖 Opening browser to post..."):
                            result = post_single_with_playwright(post['id'], headless=True)
                        
                        if result.get('success'):
                            st.success(f"✅ Draft created!")
                            if result.get('url'):
                                st.markdown(f"🔗 [View Draft]({shorten_url(result['url'])})")
                        else:
                            st.error(f"❌ Failed: {result.get('error', 'Unknown error')}")
                
                with cols[2]:
                    st.caption(f"📏 {post['word_count']} words")
        
        # Clipboard area
        if st.session_state.copy_buffer:
            st.divider()
            st.subheader("📋 Clipboard")
            st.text_area("Copy this content:", value=st.session_state.copy_buffer, height=200, key="main_clipboard")
            if st.button("🗑️ Clear Clipboard"):
                st.session_state.copy_buffer = ""
                st.rerun()

# ==========================================
# FOOTER
# ==========================================
st.divider()
st.caption("📘 Facebook → Medium Sync | Combined Dashboard")