import sqlite3
from pathlib import Path

FB_DB = Path("fb_posts.db")
MEDIUM_DB = Path("medium_posts.db")

def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip()[:19], "%Y-%m-%dT%H:%M:%S")
    except:
        try:
            return datetime.strptime(date_str.strip()[:10], "%Y-%m-%d")
        except:
            return None

from datetime import datetime

# Get a few FB posts
conn = sqlite3.connect(FB_DB)
c = conn.cursor()
c.execute("SELECT id, content, date FROM fb_text_posts WHERE content IS NOT NULL LIMIT 5")
fb_samples = c.fetchall()
conn.close()

# Get a few Medium posts
conn2 = sqlite3.connect(MEDIUM_DB)
c2 = conn2.cursor()
c2.execute("SELECT id, title, body, date_published FROM medium_posts WHERE body IS NOT NULL LIMIT 5")
md_samples = c2.fetchall()
conn2.close()

print("=" * 60)
print("FB Posts Sample:")
print("=" * 60)
for fb in fb_samples:
    print(f"ID: {fb[0]}, Date: {fb[2][:10]}, Content (50 chars): {fb[1][:50] if fb[1] else 'EMPTY'}")
    print()

print("=" * 60)
print("Medium Posts Sample:")
print("=" * 60)
for md in md_samples:
    print(f"ID: {md[0]}, Date: {md[3][:10]}, Title: {md[1][:50] if md[1] else 'EMPTY'}")
    print(f"Body (50 chars): {md[2][:50] if md[2] else 'EMPTY'}")
    print()

print("=" * 60)
print("Testing similarity between FB[0] and MD[0]:")
print("=" * 60)
import difflib
fb_text = fb_samples[0][1] or ""
md_text = f"{md_samples[0][1] or ''} {md_samples[0][2] or ''}".strip()
print(f"FB text: {fb_text[:100]}")
print(f"MD text: {md_text[:100]}")
sim = difflib.SequenceMatcher(None, fb_text.lower(), md_text.lower()).ratio()
print(f"Similarity: {sim:.2%}")