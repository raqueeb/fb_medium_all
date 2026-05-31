# Save Bengali comparison results to database
import sqlite3
import re
from difflib import SequenceMatcher

def fix_encoding(text):
    if not text:
        return ""
    try:
        return text.encode('latin-1').decode('utf-8')
    except:
        return text

def clean_text(text):
    """Remove English and keep only Bengali text."""
    if not text:
        return ""
    text = re.sub(r'http\S+', '', text)
    bengali_only = re.sub(r'[^\u0980-\u09FF\u2000-\u206F\s,।?!]', ' ', text)
    bengali_only = ' '.join(bengali_only.split())
    return bengali_only.strip()

bengali = re.compile(r'[\u0980-\u09FF]')

# Create comparison database
conn = sqlite3.connect('comparison_bengali.db')
c = conn.cursor()

# Create tables
c.execute("""
    CREATE TABLE IF NOT EXISTS matched_bengali_posts (
        id INTEGER PRIMARY KEY,
        fb_id INTEGER,
        fb_date TEXT,
        fb_content TEXT,
        md_id INTEGER,
        md_title TEXT,
        md_content TEXT,
        md_date TEXT,
        similarity REAL,
        matched_date TEXT
    )
""")

c.execute("""
    CREATE TABLE IF NOT EXISTS unmatched_bengali_posts (
        id INTEGER PRIMARY KEY,
        fb_id INTEGER,
        fb_date TEXT,
        fb_content TEXT
    )
""")

conn.commit()

fb = sqlite3.connect('fb_posts.db')
md = sqlite3.connect('medium_posts.db')

matches = []
unmatched_fb_ids = []

# Get all Medium posts with Bengali content
mc = md.cursor()
mc.execute("SELECT id, title, body, date_published FROM medium_posts")
medium_posts = mc.fetchall()

fc = fb.cursor()
fc.execute("SELECT id, date, content FROM fb_text_posts WHERE content IS NOT NULL")
all_fb_posts = {p[0]: p for p in fc.fetchall()}

for md_post in medium_posts:
    md_id, md_title, md_body, md_date = md_post
    
    if not md_date or len(md_date) < 10:
        continue
    md_date_only = md_date[:10]
    
    md_full = f"{md_title or ''} {md_body or ''}".strip()
    md_bengali = clean_text(md_full)
    
    if not md_bengali or len(md_bengali) < 20:
        continue
    
    # Find FB posts from SAME date
    fc.execute("""
        SELECT id, date, content 
        FROM fb_text_posts 
        WHERE date LIKE ? 
        AND content IS NOT NULL
    """, (f"{md_date_only}%",))
    fb_posts_on_date = fc.fetchall()
    
    if not fb_posts_on_date:
        continue
    
    best_match = None
    best_sim = 0
    
    for fb_post in fb_posts_on_date:
        fb_id, fb_date, fb_content = fb_post
        fb_text = fix_encoding(fb_content or "")
        
        if not bengali.search(fb_text):
            continue
        
        fb_bengali = clean_text(fb_text)
        if not fb_bengali or len(fb_bengali) < 20:
            continue
        
        sim = SequenceMatcher(None, fb_bengali, md_bengali).ratio()
        
        if sim > best_sim:
            best_sim = sim
            best_match = (fb_id, fb_date, fb_text, md_id, md_title, md_full, md_date, sim)
    
    if best_match and best_sim >= 0.70:
        fb_id, fb_date, fb_text, _, md_title, md_full, md_date, sim = best_match
        matches.append((fb_id, fb_date, fb_text, md_id, md_title, md_full, md_date, sim))
        # Remove from unmatched list
        if fb_id in all_fb_posts:
            del all_fb_posts[fb_id]

# Save matches to database
for m in matches:
    c.execute("""
        INSERT INTO matched_bengali_posts 
        (fb_id, fb_date, fb_content, md_id, md_title, md_content, md_date, similarity, matched_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, m)

# Save unmatched FB posts (those with Bengali content)
for fb_id, (post_id, fb_date, fb_content) in all_fb_posts.items():
    fb_text = fix_encoding(fb_content or "")
    if bengali.search(fb_text):
        c.execute("""
            INSERT INTO unmatched_bengali_posts (fb_id, fb_date, fb_content)
            VALUES (?, ?, ?)
        """, (fb_id, fb_date, fb_text))

conn.commit()

print("=" * 60)
print(f"SAVED TO comparison_bengali.db")
print("=" * 60)
print(f"Matched posts: {len(matches)}")
print(f"Unmatched FB posts (Bengali): {len(all_fb_posts)}")

conn.close()
fb.close()
md.close()