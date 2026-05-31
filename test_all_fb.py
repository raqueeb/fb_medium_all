import sqlite3
import difflib
from datetime import datetime, timedelta

def fix_encoding(text):
    if not text:
        return ""
    try:
        return text.encode('latin-1').decode('utf-8')
    except:
        return text

fb_conn = sqlite3.connect('fb_posts.db')
fb_c = fb_conn.cursor()

md_conn = sqlite3.connect('medium_posts.db')
md_c = md_conn.cursor()

# Get a Bengali Medium post
md_c.execute("SELECT id, title, body, date_published FROM medium_posts WHERE date_published LIKE '2014-09-06%'")
md = md_c.fetchone()
md_text = f"{md[1] or ''} {md[2] or ''}".strip()

# Search for any similar FB post regardless of date
# First, let's just compare all Bengali FB posts to this Medium post
print("Testing ALL FB posts against one Medium post...")
print(f"Medium: {md[1][:50] if md[1] else 'EMPTY'}")

fb_c.execute("SELECT id, date, content FROM fb_text_posts WHERE content IS NOT NULL")
fb_posts = fb_c.fetchall()

matches = []
for fb in fb_posts:
    fb_fixed = fix_encoding(fb[1] or "")
    sim = difflib.SequenceMatcher(None, md_text.lower(), fb_fixed.lower()).ratio()
    if sim > 0.05:  # Very low threshold just to see
        matches.append((fb[0], fb[2], fb_fixed[:100], sim))
        print(f"  FB ID {fb[0]}: sim={sim:.1%}")

print(f"\nTotal matches above 5%: {len(matches)}")

fb_conn.close()
md_conn.close()