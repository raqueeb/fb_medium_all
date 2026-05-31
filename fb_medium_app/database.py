import sqlite3
import os
from datetime import datetime

DB_PATH = "social_posts.db"

def get_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize the database with required tables."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS facebook_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER,
            content TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)
    conn.commit()
    conn.close()

def fix_fb_encoding(text):
    """Fixes Meta's broken JSON string encoding (Mojibake)."""
    if not text:
        return ""
    try:
        return text.encode('latin-1').decode('utf-8')
    except Exception:
        return text

def load_fb_posts_from_json(json_path):
    """Parse Facebook JSON and return a list of cleaned posts."""
    import json
    
    posts = []
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for item in data:
        timestamp = item.get("timestamp", 0)
        post_data = item.get("data", [])
        
        for element in post_data:
            post_record = element.get("post", "")
            if post_record:
                clean_content = fix_fb_encoding(post_record)
                posts.append({
                    'timestamp': timestamp,
                    'content': clean_content
                })
    
    return posts

def import_posts_to_db(posts):
    """Import posts into database, skipping duplicates."""
    conn = get_connection()
    cursor = conn.cursor()
    
    inserted_count = 0
    for post in posts:
        # Check if already exists
        cursor.execute(
            "SELECT id FROM facebook_posts WHERE timestamp = ? AND content = ?",
            (post['timestamp'], post['content'])
        )
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO facebook_posts (timestamp, content) VALUES (?, ?)",
                (post['timestamp'], post['content'])
            )
            inserted_count += 1
    
    conn.commit()
    conn.close()
    return inserted_count

def get_all_posts():
    """Get all posts from database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, timestamp, content, status FROM facebook_posts ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_pending_posts():
    """Get posts with 'pending' status."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, timestamp, content, status FROM facebook_posts WHERE status = 'pending' ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_post_status(post_id, status):
    """Update the status of a single post."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE facebook_posts SET status = ? WHERE id = ?", (status, post_id))
    conn.commit()
    conn.close()

def update_posts_status(post_ids, status):
    """Update the status of multiple posts."""
    conn = get_connection()
    cursor = conn.cursor()
    for post_id in post_ids:
        cursor.execute("UPDATE facebook_posts SET status = ? WHERE id = ?", (status, post_id))
    conn.commit()
    conn.close()

def get_post_count():
    """Get count of posts by status."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT status, COUNT(*) as count 
        FROM facebook_posts 
        GROUP BY status
    """)
    rows = cursor.fetchall()
    conn.close()
    
    counts = {'total': 0, 'pending': 0, 'replicated': 0, 'posted': 0}
    for row in rows:
        counts[row['status']] = row['count']
        counts['total'] += row['count']
    
    return counts

def clear_all_posts():
    """Clear all posts from database (for reset functionality)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM facebook_posts")
    conn.commit()
    conn.close()