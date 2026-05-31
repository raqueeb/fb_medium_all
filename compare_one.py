# Compare one specific date: find the same post in both databases
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

bengali = re.compile(r'[\u0980-\u09FF]')

fb = sqlite3.connect('fb_posts.db')
md = sqlite3.connect('medium_posts.db')

# Let's check 2014-09-06 (first Medium post date)
print("=" * 60)
print("Checking posts from 2014-09-06")
print("=" * 60)

# Get FB posts from that date
fc = fb.cursor()
fc.execute("SELECT id, date, content FROM fb_text_posts WHERE date LIKE '2014-09-06%'")
fb_posts_on_date = fc.fetchall()
print(f"FB posts on 2014-09-06: {len(fb_posts_on_date)}")

for p in fb_posts_on_date:
    print(f"  FB ID {p[0]}: {fix_encoding(p[2] or '')[:100]}...")

# Get MD post from that date
mc = md.cursor()
mc.execute("SELECT id, title, body FROM medium_posts WHERE date_published LIKE '2014-09-06%'")
md_post = mc.fetchone()

if md_post:
    print(f"\nMD ID {md_post[0]}:")
    print(f"  Title: {md_post[1][:100] if md_post[1] else '(empty)'}")
    print(f"  Body: {md_post[2][:200] if md_post[2] else '(empty)'}")

# Now compare each FB post with the MD post
if md_post:
    md_title = md_post[1] or ""
    md_body = md_post[2] or ""
    md_full_text = f"{md_title} {md_body}".strip()
    
    print("\n" + "=" * 60)
    print("Comparing each FB post with MD post (Bengali text only)")
    print("=" * 60)
    
    for p in fb_posts_on_date:
        fb_id, date, content = p
        fb_text = fix_encoding(content or "")
        
        # Skip if no Bengali in FB text
        if not bengali.search(fb_text):
            continue
        
        # Calculate similarity
        sim = SequenceMatcher(None, fb_text, md_full_text).ratio()
        
        print(f"\nFB ID {fb_id} vs MD ID {md_post[0]}: {sim:.1%}")
        print(f"  FB: {fb_text[:80]}...")
        print(f"  MD: {md_full_text[:80]}...")

# Check another date - 2024-08-27 (MD Swift series)
print("\n" + "=" * 60)
print("Checking posts from 2024-08-27 (Swift series)")
print("=" * 60)

fc.execute("SELECT id, date, content FROM fb_text_posts WHERE date LIKE '2024-08-27%'")
fb_posts = fc.fetchall()
print(f"FB posts on 2024-08-27: {len(fb_posts)}")

mc.execute("SELECT id, title, body FROM medium_posts WHERE date_published LIKE '2024-08-27%'")
md_swift = mc.fetchone()

if md_swift:
    md_title = md_swift[1] or ""
    md_body = md_swift[2] or ""
    md_text = f"{md_title} {md_body}".strip()
    print(f"\nMD ID {md_swift[0]} - {md_title[:60]}")
    
    for p in fb_posts:
        fb_id, date, content = p
        fb_text = fix_encoding(content or "")
        
        if not bengali.search(fb_text):
            continue
        
        sim = SequenceMatcher(None, fb_text, md_text).ratio()
        print(f"  FB {fb_id}: {sim:.1%} - {fb_text[:50]}...")

fb.close()
md.close()
