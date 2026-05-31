"""
Fix Bengali encoding in extracted Facebook posts.
Re-reads JSON with proper encoding and updates the database.
"""
import json
import sqlite3
import sqlite3
from pathlib import Path

DB_PATH = Path("fb_posts.db")
JSON_PATH = Path("fb_extracted/your_facebook_activity/posts/your_posts__check_ins__photos_and_videos_1.json")

def fix_encoding(text):
    """Fix double-encoded Bengali text."""
    if not text:
        return text
    try:
        # Check if text has the double-encoding pattern (starts with char > 127)
        if ord(text[0]) > 127:
            # This is double-encoded - decode latin-1 then UTF-8
            fixed = text.encode('latin-1').decode('utf-8')
            return fixed
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass
    return text

def check_encoding(text):
    """Check if text has double-encoding issue."""
    if not text or len(text) < 3:
        return False
    # Double-encoded Bengali starts with à (0xe0) followed by ¦ (0xa6)
    return ord(text[0]) == 0xe0 and ord(text[1]) == 0xa6

# Update database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get all posts
cursor.execute("SELECT id, content FROM fb_text_posts")
posts = cursor.fetchall()

fixed_count = 0
total = len(posts)

for post_id, content in posts:
    if check_encoding(content):
        fixed = fix_encoding(content)
        cursor.execute("UPDATE fb_text_posts SET content = ? WHERE id = ?", (fixed, post_id))
        fixed_count += 1

conn.commit()
conn.close()

print(f"✅ Fixed {fixed_count}/{total} posts with Bengali encoding issues")