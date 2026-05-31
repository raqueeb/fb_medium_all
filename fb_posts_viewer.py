"""
Facebook Posts Viewer
A simple Streamlit app to browse and search your extracted Facebook posts.
Smart pagination and filtering for faster loading.
"""
import streamlit as st
import sqlite3
from pathlib import Path
from datetime import datetime

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="📘 Facebook Posts",
    page_icon="📘",
    layout="wide"
)

# ==========================================
# DATABASE SETUP
# ==========================================
DB_PATH = Path("fb_posts.db")
POSTS_PER_PAGE = 10

def get_db_connection():
    """Get database connection."""
    return sqlite3.connect(DB_PATH)

def get_stats():
    """Get overall statistics."""
    conn = get_db_connection()
    stats = conn.execute("""
        SELECT COUNT(*), MIN(date), MAX(date), SUM(word_count), AVG(word_count)
        FROM fb_text_posts
    """).fetchone()
    
    type_counts = conn.execute("""
        SELECT post_type, COUNT(*) FROM fb_text_posts GROUP BY post_type ORDER BY COUNT(*) DESC
    """).fetchall()
    
    length_dist = conn.execute("""
        SELECT 
            SUM(CASE WHEN word_count < 50 THEN 1 ELSE 0 END),
            SUM(CASE WHEN word_count >= 50 AND word_count < 200 THEN 1 ELSE 0 END),
            SUM(CASE WHEN word_count >= 200 AND word_count < 500 THEN 1 ELSE 0 END),
            SUM(CASE WHEN word_count >= 500 THEN 1 ELSE 0 END)
        FROM fb_text_posts
    """).fetchone()
    
    conn.close()
    return {'total': stats[0], 'min_date': stats[1], 'max_date': stats[2],
            'total_words': stats[3], 'avg_words': stats[4], 'type_counts': type_counts,
            'short': length_dist[0], 'medium': length_dist[1], 'long': length_dist[2], 'very_long': length_dist[3]}

def get_filters():
    """Get available filter options (years and months)."""
    conn = get_db_connection()
    
    years = conn.execute("SELECT DISTINCT substr(date, 1, 4) as year FROM fb_text_posts ORDER BY year DESC").fetchall()
    years = [y[0] for y in years]
    
    # Get month-year combinations for dropdown
    month_years = conn.execute("""
        SELECT DISTINCT substr(date, 1, 7) as month_year 
        FROM fb_text_posts 
        ORDER BY month_year DESC
    """).fetchall()
    month_years = [my[0] for my in month_years]
    
    post_types = conn.execute("SELECT DISTINCT post_type FROM fb_text_posts ORDER BY post_type").fetchall()
    post_types = [t[0] for t in post_types]
    
    conn.close()
    return {'years': years, 'month_years': month_years, 'post_types': post_types}

def get_posts(year=None, month_year=None, post_type=None, search=None, min_words=0, page=1):
    """Get paginated posts with filters."""
    conn = get_db_connection()
    
    # Build query
    query = "SELECT id, timestamp, date, content, post_type, word_count, has_media FROM fb_text_posts WHERE 1=1"
    params = []
    
    if year:
        query += " AND date LIKE ?"
        params.append(f"{year}%")
    elif month_year:
        query += " AND date LIKE ?"
        params.append(f"{month_year}%")
    
    if post_type and post_type != "All":
        query += " AND post_type = ?"
        params.append(post_type)
    
    if search:
        query += " AND content LIKE ?"
        params.append(f"%{search}%")
    
    if min_words > 0:
        query += " AND word_count >= ?"
        params.append(min_words)
    
    # Get total count
    count_query = query.replace("SELECT id, timestamp, date, content, post_type, word_count, has_media", "SELECT COUNT(*)")
    total = conn.execute(count_query, params).fetchone()[0]
    
    # Add pagination
    offset = (page - 1) * POSTS_PER_PAGE
    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params.extend([POSTS_PER_PAGE, offset])
    
    posts = conn.execute(query, params).fetchall()
    conn.close()
    
    return {'posts': posts, 'total': total, 'total_pages': (total + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE}

# ==========================================
# MAIN APP
# ==========================================
st.title("📘 Facebook Posts Viewer")

if not DB_PATH.exists():
    st.error("❌ Database not found! Run `python extract_fb_posts.py` first.")
    st.stop()

stats = get_stats()
filters = get_filters()

# ==========================================
# DASHBOARD (Summary Cards)
# ==========================================
st.subheader("📊 Dashboard")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Posts", f"{stats['total']:,}")
with col2:
    st.metric("Total Words", f"{stats['total_words']:,}")
with col3:
    st.metric("Avg Words", f"{stats['avg_words']:.0f}")
with col4:
    years_range = int(stats['max_date'][:4]) - int(stats['min_date'][:4]) if stats['min_date'] else 0
    st.metric("Years Active", years_range)

# Date range
st.caption(f"📅 {stats['min_date'][:10] if stats['min_date'] else 'N/A'} → {stats['max_date'][:10] if stats['max_date'] else 'N/A'}")

# Posts by type
st.write("**📂 Posts by Type**")
type_cols = st.columns(len(stats['type_counts']))
for i, (ptype, count) in enumerate(stats['type_counts']):
    with type_cols[i]:
        emoji = {"text": "📝", "link": "🔗", "photo": "🖼️", "video": "🎬", "note": "📄"}.get(ptype, "📄")
        st.metric(f"{emoji}", count)

st.divider()

# ==========================================
# FILTERS
# ==========================================
st.subheader("🔍 Filter & Browse Posts")

col_filter1, col_filter2, col_filter3 = st.columns(3)
with col_filter1:
    filter_mode = st.radio("📅 Filter by", ["All Time", "By Year", "By Month"], horizontal=True)
with col_filter2:
    if filter_mode == "By Year":
        selected_year = st.selectbox("Year", ["All"] + filters['years'])
    elif filter_mode == "By Month":
        selected_month = st.selectbox("Month", ["All"] + filters['month_years'])
    else:
        selected_year = None
        selected_month = None
with col_filter3:
    post_type_filter = st.selectbox("📂 Type", ["All"] + filters['post_types'])

col_search1, col_search2 = st.columns([3, 1])
with col_search1:
    search_term = st.text_input("🔍 Search", placeholder="Search in posts...", label_visibility="collapsed")
with col_search2:
    min_words = st.number_input("Min words", min_value=0, value=0, step=10, label_visibility="collapsed")

# Pagination state
if 'page' not in st.session_state:
    st.session_state.page = 1

# ==========================================
# POSTS LIST
# ==========================================
# Determine active filters
active_year = selected_year if filter_mode == "By Year" else None
active_month = selected_month if filter_mode == "By Month" else None

result = get_posts(year=active_year, month_year=active_month, post_type=post_type_filter,
                   search=search_term if search_term else None, min_words=min_words, page=st.session_state.page)

total_pages = result['total_pages']
posts = result['posts']

st.write(f"**{result['total']} posts** found" + (f" • Page {st.session_state.page}/{total_pages}" if total_pages > 1 else ""))

# Pagination controls
if total_pages > 1:
    col_prev, col_pages, col_next = st.columns([1, 3, 1])
    with col_prev:
        if st.button("◀️ Prev", disabled=st.session_state.page <= 1):
            st.session_state.page -= 1
            st.rerun()
    with col_pages:
        st.write(f"Page {st.session_state.page} of {total_pages}")
    with col_next:
        if st.button("Next ▶", disabled=st.session_state.page >= total_pages):
            st.session_state.page += 1
            st.rerun()

st.divider()

# Display posts
if posts:
    for post in posts:
        post_id, timestamp, date, content, post_type, word_count, has_media = post
        
        emoji = {"text": "📝", "link": "🔗", "photo": "🖼️", "video": "🎬", "note": "📄"}.get(post_type, "📄")
        
        with st.expander(f"{emoji} {date[:10]} | {word_count} words | {content[:60]}...", expanded=False):
            st.write(content)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.caption(f"🗂️ {post_type}")
            with col2:
                st.caption(f"📏 {word_count} words")
            with col3:
                st.caption(f"🖼️ Has media" if has_media else "📄 Text only")
else:
    st.info("No posts match your filters.")

# Footer
st.divider()
st.caption("📘 Facebook Posts Viewer")