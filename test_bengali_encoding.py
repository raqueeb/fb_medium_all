# Test Bengali encoding in both databases
import sqlite3
import re

def fix_encoding(text):
    """Fix double-encoded Bengali text from Facebook."""
    if not text:
        return ""
    try:
        return text.encode('latin-1').decode('utf-8')
    except:
        return text

# Check for Bengali Unicode pattern
bengali = re.compile(r'[\u0980-\u09FF]')

fb = sqlite3.connect('fb_posts.db')
md = sqlite3.connect('medium_posts.db')

print("=" * 60)
print("FACEBOOK POSTS - Sample Bengali Content")
print("=" * 60)

fc = fb.cursor()
fc.execute("SELECT id, date, content FROM fb_text_posts WHERE content LIKE '%া%' LIMIT 5")
for p in fc.fetchall():
    post_id, date, content = p
    fixed = fix_encoding(content or "")
    has_bengali_fixed = bool(bengali.search(fixed))
    print(f"FB ID {post_id} ({date[:10]}):")
    print(f"  Original (first 80): {content[:80] if content else 'EMPTY'}")
    print(f"  Fixed (first 80): {fixed[:80]}")
    print(f"  Has Bengali after fix: {has_bengali_fixed}")
    print()

print("=" * 60)
print("MEDIUM POSTS - Sample Bengali Content")
print("=" * 60)

mc = md.cursor()
mc.execute("SELECT id, title, body, date_published FROM medium_posts WHERE title LIKE '%া%' OR title LIKE '%ি%' LIMIT 5")
for p in mc.fetchall():
    post_id, title, body, date = p
    title_clean = title or ""
    has_bengali_title = bool(bengali.search(title_clean))
    print(f"MD ID {post_id} ({date[:10] if date else 'NO DATE'}):")
    print(f"  Title (first 80): {title_clean[:80]}")
    print(f"  Body (first 80): {(body or '')[:80]}")
    print(f"  Has Bengali in title: {has_bengali_title}")
    print()

fb.close()
md.close()