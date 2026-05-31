import sqlite3
import difflib
from datetime import datetime
import re

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

# Check Bengali characters in both databases
print("Checking Bengali text presence...")

# Bengali Unicode ranges: \u0980-\u09FF
import re
bengali_pattern = re.compile(r'[\u0980-\u09FF]')

# Check FB posts for Bengali
fb_c.execute("SELECT id, content, date FROM fb_text_posts WHERE content LIKE '%া%' OR content LIKE '%ি%' OR content LIKE '%ু%' LIMIT 5")
fb_bengali = fb_c.fetchall()
print(f"\nFB posts with Bengali characters: {len(list(fb_c.execute('SELECT id FROM fb_text_posts WHERE content LIKE \"%া%\" OR content LIKE \"%ি%\" OR content LIKE \"%ু%\"')))}")

for fb in fb_bengali:
    print(f"  ID {fb[0]}: {fb[2][:10]}")
    print(f"  Content: {fb[1][:100] if fb[1] else 'EMPTY'}")
    print()

# Check Medium posts for Bengali
md_c.execute("SELECT id, title, date_published FROM medium_posts WHERE title LIKE '%া%' OR title LIKE '%ি%' LIMIT 5")
md_bengali = md_c.fetchall()
print(f"\nMedium posts with Bengali in title:")

for md in md_bengali:
    print(f"  ID {md[0]}: {md[1][:50] if md[1] else 'EMPTY'}")

# Try to find ANY match between any FB and any Medium post
print("\n" + "=" * 60)
print("Searching for ANY high-similarity pair...")

md_c.execute("SELECT id, title, body, date_published FROM medium_posts WHERE body IS NOT NULL")
all_md = md_c.fetchall()

fb_c.execute("SELECT id, content, date FROM fb_text_posts WHERE content IS NOT NULL")
all_fb = fb_c.fetchall()

found = 0
for md in all_md[:10]:  # Test first 10 Medium posts
    md_text = f"{md[1] or ''} {md[2] or ''}".strip()
    for fb in all_fb[:100]:  # Test first 100 FB posts
        fb_text = fix_encoding(fb[1] or "")
        sim = difflib.SequenceMatcher(None, md_text.lower(), fb_text.lower()).ratio()
        if sim > 0.3:
            print(f"FOUND! FB ID {fb[0]} vs MD ID {md[0]}: {sim:.1%}")
            found += 1
            if found >= 5:
                break
    if found >= 5:
        break

if found == 0:
    print("No matches found with >30% similarity")

fb_conn.close()
md_conn.close()