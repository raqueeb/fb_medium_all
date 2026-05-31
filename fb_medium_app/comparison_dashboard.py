# Comparison Dashboard - sync with compare_posts.py results
import streamlit as st
import sqlite3
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

st.set_page_config(page_title="📊 Comparison Dashboard", layout="wide")

def get_comparison_stats():
    """Get stats from comparison database."""
    db_path = Path(__file__).parent.parent / "comparison.db"
    if not db_path.exists():
        return None
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    stats = {}
    
    # Total counts
    c.execute("SELECT COUNT(*) FROM matched_posts")
    stats['matched'] = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM unmatched_fb_posts")
    stats['unmatched'] = c.fetchone()[0]
    
    # Similarity buckets
    c.execute("SELECT COUNT(*) FROM matched_posts WHERE similarity >= 0.8")
    stats['high'] = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM matched_posts WHERE similarity >= 0.5 AND similarity < 0.8")
    stats['medium'] = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM matched_posts WHERE similarity >= 0.3 AND similarity < 0.5")
    stats['low'] = c.fetchone()[0]
    
    # Average similarity
    c.execute("SELECT AVG(similarity) FROM matched_posts")
    stats['avg_sim'] = c.fetchone()[0] or 0
    
    # Average days diff
    c.execute("SELECT AVG(days_diff) FROM matched_posts")
    stats['avg_days'] = c.fetchone()[0] or 0
    
    conn.close()
    
    stats['total'] = stats['matched'] + stats['unmatched']
    stats['match_rate'] = stats['matched'] / stats['total'] * 100 if stats['total'] > 0 else 0
    
    return stats

def get_matches(limit=50, sort_by='similarity'):
    """Get matched posts."""
    db_path = Path(__file__).parent.parent / "comparison.db"
    if not db_path.exists():
        return []
    
    conn = sqlite3.connect(db_path)
    if sort_by == 'similarity':
        rows = conn.execute("""
            SELECT fb_id, fb_content, fb_date, md_id, md_title, md_content, 
                   similarity, days_diff 
            FROM matched_posts 
            ORDER BY similarity DESC 
            LIMIT ?
        """, (limit,)).fetchall()
    elif sort_by == 'date':
        rows = conn.execute("""
            SELECT fb_id, fb_content, fb_date, md_id, md_title, md_content, 
                   similarity, days_diff 
            FROM matched_posts 
            ORDER BY fb_date DESC 
            LIMIT ?
        """, (limit,)).fetchall()
    conn.close()
    return rows

def get_unmatched(count=100):
    """Get unmatched FB posts."""
    db_path = Path(__file__).parent.parent / "comparison.db"
    if not db_path.exists():
        return []
    
    conn = sqlite3.connect(db_path)
    rows = conn.execute("""
        SELECT fb_id, content, date, post_type 
        FROM unmatched_fb_posts 
        ORDER BY date DESC 
        LIMIT ?
    """, (count,)).fetchall()
    conn.close()
    return rows

# ==========================================
# MAIN CONTENT
# ==========================================
st.title("📊 Comparison Dashboard")
st.caption("Facebook ↔ Medium post matching results")

stats = get_comparison_stats()

if stats is None:
    st.warning("⚠️ No comparison data found. Run `python compare_posts.py` first.")
    st.code("cd c:\\Downloads\\fb_medium; python compare_posts.py")
else:
    # Stats cards
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total FB Posts", stats['total'])
    with col2:
        st.metric("Found on Medium", stats['matched'])
    with col3:
        st.metric("Match Rate", f"{stats['match_rate']:.1f}%")
    with col4:
        st.metric("Avg Similarity", f"{stats['avg_sim']*100:.1f}%")
    with col5:
        st.metric("Not on Medium", stats['unmatched'])
    
    st.divider()
    
    # Similarity distribution
    st.subheader("📈 Similarity Distribution")
    col_sim1, col_sim2, col_sim3 = st.columns(3)
    with col_sim1:
        st.metric("High (≥80%)", stats['high'])
    with col_sim2:
        st.metric("Medium (50-79%)", stats['medium'])
    with col_sim3:
        st.metric("Low (30-49%)", stats['low'])
    
    st.divider()
    
    # Tabs
    tab_matches, tab_unmatched = st.tabs(["✅ Matches", "❌ Unmatched FB Posts"])
    
    with tab_matches:
        sort_by = st.radio("Sort matches by", ["similarity", "date"], horizontal=True)
        matches = get_matches(limit=50, sort_by=sort_by)
        
        st.write(f"Showing {len(matches)} matches")
        
        for m in matches:
            fb_id, fb_content, fb_date, md_id, md_title, md_content, similarity, days_diff = m
            
            with st.expander(f"🔗 FB {fb_id} ↔ MD {md_id} | {similarity*100:.1f}% similarity", expanded=False):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write("**Facebook Post**")
                    st.write(fb_content[:300] if fb_content else "(empty)")
                    st.caption(f"Date: {fb_date[:10]}")
                with col_b:
                    st.write("**Medium Post**")
                    st.write(md_title[:100] if md_title else "(empty)")
                    st.write(md_content[:200] if md_content else "(empty)")
                    st.caption(f"Date diff: {days_diff} days")
    
    with tab_unmatched:
        st.write("FB posts that didn't match any Medium post (candidates for publishing)")
        
        # Filter options
        col_filter1, col_filter2 = st.columns([3, 1])
        with col_filter1:
            search = st.text_input("Search unmatched posts", placeholder="Search content...")
        with col_filter2:
            post_type = st.selectbox("Type", ["All", "text", "link", "photo"])
        
        unmatched = get_unmatched(200)
        
        st.write(f"Showing first {len(unmatched)} unmatched posts")
        
        for p in unmatched[:50]:
            fb_id, content, date, post_type_val = p
            with st.expander(f"📝 FB {fb_id} | {date[:10]} | {post_type_val}", expanded=False):
                st.write(content[:300] if content else "(empty)")
                st.caption(f"Type: {post_type_val}")

st.divider()
st.caption("Run comparison: `cd c:\\Downloads\\fb_medium; python compare_posts.py`")