"""
Facebook ↔ Medium Post Comparison Tool
Matches FB posts to Medium posts based on date proximity and text similarity.
"""
import sqlite3
import difflib
from datetime import datetime, timedelta
from pathlib import Path

# Paths
FB_DB = Path(__file__).parent / "fb_posts.db"
MEDIUM_DB = Path(__file__).parent / "medium_posts.db"
COMPARISON_DB = Path(__file__).parent / "comparison.db"

# Constants
DATE_TOLERANCE_DAYS = 30
MIN_SIMILARITY = 0.30  # 30% minimum similarity (lowered for Bengali content)

def fix_encoding(text):
    """Fix double-encoded text."""
    if not text:
        return ""
    try:
        return text.encode('latin-1').decode('utf-8')
    except:
        return text

def load_fb_posts():
    """Load all Facebook posts from database."""
    conn = sqlite3.connect(FB_DB)
    c = conn.cursor()
    c.execute("""
        SELECT id, date, content, post_type, word_count
        FROM fb_text_posts
        ORDER BY date DESC
    """)
    posts = c.fetchall()
    conn.close()
    return posts

def load_medium_posts():
    """Load all Medium posts from database."""
    conn = sqlite3.connect(MEDIUM_DB)
    c = conn.cursor()
    c.execute("""
        SELECT id, title, body, date_published
        FROM medium_posts
        ORDER BY date_published DESC
    """)
    posts = c.fetchall()
    conn.close()
    return posts

def parse_date(date_str):
    """Parse various date formats."""
    if not date_str:
        return None
    
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%B %d, %Y",
        "%d %B %Y",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip()[:19], fmt)
        except:
            continue
    return None

def date_diff_days(date1, date2):
    """Calculate days between two dates."""
    if not date1 or not date2:
        return 0  # No date = no constraint on matching
    return abs((date1 - date2).days)

def text_similarity(text1, text2):
    """Calculate similarity ratio between two texts (0.0 to 1.0)."""
    if not text1 or not text2:
        return 0.0
    
    # Normalize texts
    t1 = ' '.join(text1.lower().split())
    t2 = ' '.join(text2.lower().split())
    
    if not t1 or not t2:
        return 0.0
    
    return difflib.SequenceMatcher(None, t1, t2).ratio()

def find_matches():
    """Find matching posts between Facebook and Medium."""
    fb_posts = load_fb_posts()
    medium_posts = load_medium_posts()
    
    matches = []
    unmatched_fb = []
    
    print(f"Comparing {len(fb_posts)} FB posts with {len(medium_posts)} Medium posts...")
    
    # Group Medium posts by rough year for faster lookup
    md_by_year = {}
    for md in medium_posts:
        md_datetime = parse_date(md[3])  # md_date
        year = md_datetime.year if md_datetime else None
        if year not in md_by_year:
            md_by_year[year] = []
        md_by_year[year].append(md)
    
    processed = 0
    for fb in fb_posts:
        fb_id, fb_date, fb_content, fb_type, fb_word_count = fb
        
        # Parse FB date
        fb_datetime = parse_date(fb_date)
        fb_year = fb_datetime.year if fb_datetime else None
        # Fix encoding for Bengali text
        fb_text = fix_encoding(fb_content or "")
        
        best_match = None
        best_score = 0
        
        # Only compare with Medium posts from same year (or any if no date)
        candidates = []
        if fb_year and fb_year in md_by_year:
            candidates = md_by_year[fb_year]
        elif None in md_by_year:
            candidates.extend(md_by_year[None])
        
        for md in candidates:
            md_id, md_title, md_body, md_date = md
            
            # Parse Medium date
            md_datetime = parse_date(md_date)
            md_text = f"{md_title or ''} {md_body or ''}".strip()
            
            # Calculate content similarity
            similarity = text_similarity(fb_text, md_text)
            
            # Title similarity bonus
            title_sim = 0
            if md_title:
                title_sim = text_similarity(fb_text[:100], md_title)
                similarity = max(similarity, similarity * 0.5 + title_sim * 0.5)
            
            if similarity > MIN_SIMILARITY and similarity > best_score:
                best_score = similarity
                days_diff = date_diff_days(fb_datetime, md_datetime)
                best_match = {
                    'md_id': md_id,
                    'md_title': md_title,
                    'md_date': md_date,
                    'md_url': None,
                    'md_text': md_text[:500] + "..." if len(md_text) > 500 else md_text,
                    'days_diff': days_diff,
                    'similarity': similarity,
                    'title_similarity': title_sim
                }
        
        if best_match:
            matches.append({
                'fb_id': fb_id,
                'fb_title': None,
                'fb_content': fb_content[:500] + "..." if fb_content and len(fb_content) > 500 else fb_content,
                'fb_date': fb_date,
                'fb_type': fb_type,
                **best_match
            })
        else:
            unmatched_fb.append({
                'fb_id': fb_id,
                'fb_title': None,
                'fb_content': fb_content,
                'fb_date': fb_date,
                'fb_type': fb_type,
            })
    
    print(f"Found {len(matches)} matches out of {len(fb_posts)} FB posts")
    return matches, unmatched_fb

def save_comparison(matches, unmatched):
    """Save comparison results to database."""
    conn = sqlite3.connect(COMPARISON_DB)
    c = conn.cursor()
    
    # Create tables
    c.execute("""
        CREATE TABLE IF NOT EXISTS matched_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fb_id INTEGER,
            fb_content TEXT,
            fb_date TEXT,
            fb_type TEXT,
            md_id INTEGER,
            md_title TEXT,
            md_content TEXT,
            md_date TEXT,
            days_diff INTEGER,
            similarity REAL,
            status TEXT DEFAULT 'pending'
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS unmatched_fb_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fb_id INTEGER,
            content TEXT,
            date TEXT,
            post_type TEXT,
            synced INTEGER DEFAULT 0
        )
    """)
    
    c.execute("DELETE FROM matched_posts")
    c.execute("DELETE FROM unmatched_fb_posts")
    
    # Insert matches
    for m in matches:
        c.execute("""
            INSERT INTO matched_posts 
            (fb_id, fb_content, fb_date, fb_type, md_id, md_title, md_content, md_date, days_diff, similarity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            m['fb_id'], m['fb_content'], m['fb_date'], m['fb_type'],
            m['md_id'], m['md_title'], m['md_text'], m['md_date'],
            m['days_diff'], m['similarity']
        ))
    
    # Insert unmatched FB posts
    for p in unmatched:
        c.execute("""
            INSERT INTO unmatched_fb_posts (fb_id, content, date, post_type)
            VALUES (?, ?, ?, ?)
        """, (p['fb_id'], p['fb_content'], p['fb_date'], p['fb_type']))
    
    conn.commit()
    conn.close()
    
    return len(matches), len(unmatched)

def get_stats():
    """Get comparison statistics."""
    conn = sqlite3.connect(COMPARISON_DB)
    c = conn.cursor()
    
    stats = {}
    
    c.execute("SELECT COUNT(*) FROM matched_posts")
    stats['matched'] = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM unmatched_fb_posts")
    stats['unmatched'] = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM matched_posts WHERE similarity >= 0.8")
    stats['high_confidence'] = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM matched_posts WHERE similarity >= 0.5 AND similarity < 0.8")
    stats['medium_confidence'] = c.fetchone()[0]
    
    c.execute("SELECT AVG(similarity) FROM matched_posts")
    avg_sim = c.fetchone()[0]
    stats['avg_similarity'] = round(avg_sim * 100, 1) if avg_sim else 0
    
    c.execute("SELECT AVG(days_diff) FROM matched_posts")
    avg_days = c.fetchone()[0]
    stats['avg_days_diff'] = round(avg_days, 1) if avg_days else 0
    
    conn.close()
    
    stats['total_fb'] = stats['matched'] + stats['unmatched']
    stats['match_rate'] = round(stats['matched'] / stats['total_fb'] * 100, 1) if stats['total_fb'] > 0 else 0
    
    return stats

if __name__ == "__main__":
    print("=" * 50)
    print("Facebook ↔ Medium Post Comparison")
    print("=" * 50)
    
    matches, unmatched = find_matches()
    matched_count, unmatched_count = save_comparison(matches, unmatched)
    stats = get_stats()
    
    print("\n" + "=" * 50)
    print("RESULTS")
    print("=" * 50)
    print(f"Total Facebook Posts:     {stats['total_fb']:,}")
    print(f"Found on Medium:          {stats['matched']:,} ({stats['match_rate']}%)")
    print(f"Not on Medium:            {stats['unmatched']:,}")
    print()
    print(f"High Confidence (≥80%):   {stats['high_confidence']}")
    print(f"Medium Confidence (50-79%): {stats['medium_confidence']}")
    print(f"Average Similarity:       {stats['avg_similarity']}%")
    print(f"Average Date Difference:  {stats['avg_days_diff']} days")
    print("=" * 50)