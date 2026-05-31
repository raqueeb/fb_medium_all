"""
Extract long-text Facebook posts from exported JSON files.
Proper UTF-8 encoding handling from the start.
"""
import json
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("fb_posts.db")
EXTRACTED_DIR = Path("fb_extracted/your_facebook_activity/posts")
MIN_CHARS = 50   # Lowered from 100 to capture more posts
MIN_WORDS = 10    # Lowered from 20 to capture more posts

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fb_text_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER, date TEXT, content TEXT,
            post_type TEXT, word_count INTEGER, char_count INTEGER,
            has_media BOOLEAN, status TEXT DEFAULT 'pending', imported_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_post_text(post):
    for item in post.get('data', []):
        if 'post' in item:
            return item['post']
    return ""

def get_post_type(post):
    title = post.get('title', '').lower()
    if 'photo' in title: return 'photo'
    elif 'video' in title: return 'video'
    elif 'note' in title: return 'note'
    elif 'link' in title: return 'link'
    else: return 'text'

def extract_posts(json_path):
    posts = []
    for enc in ['utf-8-sig', 'utf-8', 'latin-1']:
        try:
            with open(json_path, 'r', encoding=enc) as f:
                data = json.load(f)
            break
        except:
            continue
    
    posts_list = data if isinstance(data, list) else data.get('data', [])
    
    for entry in posts_list:
        text = get_post_text(entry)
        if not text or len(text.strip()) < MIN_CHARS:
            continue
        
        # Fix double-encoding
        if len(text) > 2 and ord(text[0]) == 0xe0 and ord(text[1]) == 0xa6:
            try:
                text = text.encode('latin-1').decode('utf-8')
            except:
                pass
        
        if text.strip().startswith(('http://', 'https://')):
            continue
        
        words = text.split()
        if len(words) < MIN_WORDS:
            continue
        
        ts = entry.get('timestamp', 0)
        date = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M') if ts else "Unknown"
        
        posts.append({
            'timestamp': ts, 'date': date, 'content': text.strip(),
            'post_type': get_post_type(entry), 'word_count': len(words),
            'char_count': len(text), 'has_media': bool(entry.get('attachments', [])),
            'status': 'pending', 'imported_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    return posts

def main():
    print("=" * 50)
    print("Facebook Posts Extractor")
    print("=" * 50)
    
    init_db()
    
    json_files = list(EXTRACTED_DIR.glob("your_posts*.json"))
    print(f"Found {len(json_files)} JSON file(s)")
    
    all_posts = []
    for f in json_files:
        posts = extract_posts(f)
        print(f"{f.name}: {len(posts)} posts")
        all_posts.extend(posts)
    
    conn = sqlite3.connect(DB_PATH)
    for p in all_posts:
        conn.execute("""INSERT INTO fb_text_posts 
            (timestamp, date, content, post_type, word_count, char_count, has_media, status, imported_at)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (p['timestamp'], p['date'], p['content'], p['post_type'],
             p['word_count'], p['char_count'], p['has_media'], p['status'], p['imported_at']))
    conn.commit()
    conn.close()
    
    print(f"\nTotal: {len(all_posts)} posts saved")

if __name__ == "__main__":
    main()