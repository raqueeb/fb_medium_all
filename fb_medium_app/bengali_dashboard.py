# Bengali Comparison Dashboard
import streamlit as st
import sqlite3
from pathlib import Path

st.set_page_config(page_title="📊 Bengali Comparison", layout="wide")

def get_bengali_stats():
    db_path = Path(__file__).parent.parent / "comparison_bengali.db"
    if not db_path.exists():
        return None
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    stats = {}
    c.execute("SELECT COUNT(*) FROM matched_bengali_posts")
    stats['matched'] = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM unmatched_bengali_posts")
    stats['unmatched'] = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM matched_bengali_posts WHERE similarity >= 0.95")
    stats['exact'] = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM matched_bengali_posts WHERE similarity >= 0.90 AND similarity < 0.95")
    stats['high'] = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM matched_bengali_posts WHERE similarity >= 0.70 AND similarity < 0.90")
    stats['medium'] = c.fetchone()[0]
    
    c.execute("SELECT AVG(similarity) FROM matched_bengali_posts")
    stats['avg_sim'] = c.fetchone()[0] or 0
    
    conn.close()
    stats['total'] = stats['matched'] + stats['unmatched']
    stats['match_rate'] = stats['matched'] / (stats['matched'] + stats['unmatched']) * 100 if stats['total'] > 0 else 0
    return stats

def get_matches(limit=100, min_sim=0.70):
    db_path = Path(__file__).parent.parent / "comparison_bengali.db"
    conn = sqlite3.connect(db_path)
    rows = conn.execute("""
        SELECT fb_id, fb_date, fb_content, md_id, md_title, md_content, md_date, similarity
        FROM matched_bengali_posts 
        WHERE similarity >= ?
        ORDER BY similarity DESC
        LIMIT ?
    """, (min_sim, limit)).fetchall()
    conn.close()
    return rows

def get_unmatched(count=100):
    db_path = Path(__file__).parent.parent / "comparison_bengali.db"
    conn = sqlite3.connect(db_path)
    rows = conn.execute("""
        SELECT fb_id, fb_date, fb_content 
        FROM unmatched_bengali_posts 
        ORDER BY fb_date DESC 
        LIMIT ?
    """, (count,)).fetchall()
    conn.close()
    return rows

st.title("📊 Bengali Content Comparison Dashboard")
st.caption("Facebook ↔ Medium | Same date matching | Bengali text only")

stats = get_bengali_stats()

if stats is None:
    st.warning("Run `python compare_bengali.py` first to generate comparison data.")
else:
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Bengali Posts", stats['total'])
    with col2:
        st.metric("Found on Medium", stats['matched'])
    with col3:
        st.metric("Match Rate", f"{stats['match_rate']:.1f}%")
    with col4:
        st.metric("Avg Similarity", f"{stats['avg_sim']*100:.1f}%")
    with col5:
        st.metric("Not on Medium", stats['unmatched'])
    
    st.divider()
    
    col_sim1, col_sim2, col_sim3 = st.columns(3)
    with col_sim1:
        st.metric("Exact Match (≥95%)", stats['exact'])
    with col_sim2:
        st.metric("High (90-94%)", stats['high'])
    with col_sim3:
        st.metric("Good (70-89%)", stats['medium'])
    
    st.divider()
    
    tab1, tab2 = st.tabs(["✅ Matches (61)", "❌ Unmatched FB Posts"])
    
    with tab1:
        min_sim = st.slider("Minimum similarity", 0.5, 1.0, 0.70, 0.05)
        matches = get_matches(100, min_sim)
        st.write(f"Showing {len(matches)} matches above {min_sim*100:.0f}% similarity")
        
        for m in matches:
            fb_id, fb_date, fb_content, md_id, md_title, md_content, md_date, sim = m
            with st.expander(f"🔗 FB {fb_id} ↔ MD {md_id} | {fb_date[:10]} | {sim*100:.1f}%", expanded=False):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write("**Facebook (বাংলা)**")
                    st.write(fb_content[:300] if fb_content else "(empty)")
                with col_b:
                    st.write("**Medium (বাংলা)**")
                    st.write(f"Title: {md_title[:60] if md_title else '(empty)'}")
                    st.write(md_content[:200] if md_content else "(empty)")
    
    with tab2:
        st.write("Facebook posts with Bengali content that were NOT found on Medium")
        unmatched = get_unmatched(200)
        st.write(f"Showing {len(unmatched)} unmatched posts")
        
        for p in unmatched[:50]:
            fb_id, fb_date, fb_content = p
            with st.expander(f"📝 FB {fb_id} | {fb_date[:10]}", expanded=False):
                st.write(fb_content[:300] if fb_content else "(empty)")

st.divider()
st.caption("Run: `cd c:\\Downloads\\fb_medium; python compare_bengali.py`")