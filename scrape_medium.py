"""
Scrape Medium posts using curl_cffi with Chrome TLS fingerprint.
Saves to SQLite database and JSON backup.
"""
import time
import re
import json
import sqlite3
from pathlib import Path
from curl_cffi import requests

DB_PATH = Path(__file__).parent / "medium_posts.db"
USERNAME = "raqueeb"
OUTPUT_FILE = Path(__file__).parent / "medium_posts_scraped.json"

def init_db(db_path):
    """Initialize database for storing Medium posts."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medium_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE,
            url TEXT,
            title TEXT,
            published_date TEXT,
            word_count INTEGER,
            scraped_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_posts_to_db(db_path, posts):
    """Save scraped posts to database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    saved = 0
    for post in posts:
        cursor.execute("""
            INSERT OR REPLACE INTO medium_posts (slug, url, title, published_date, word_count, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            post["slug"],
            post["url"],
            post.get("title", ""),
            post.get("published_date", ""),
            post.get("word_count", 0),
            post.get("scraped_at", "")
        ))
        saved += 1
    
    conn.commit()
    conn.close()
    return saved

def extract_posts_from_profile(html, username):
    """Extract posts from profile page HTML."""
    posts = {}
    
    # Pattern 1: Extract from slug patterns in hrefs
    href_pattern = rf'href="https://medium\.com/@{username}/([a-z0-9-]+)"'
    for match in re.finditer(href_pattern, html):
        slug = match.group(1)
        if len(slug) > 10:
            posts[slug] = {
                "slug": slug,
                "url": f"https://medium.com/@{username}/{slug}"
            }
    
    return list(posts.values())

def scrape_medium(username=None):
    """Scrape Medium posts and save to database."""
    username = username or USERNAME
    username_clean = username.lstrip("@")
    
    init_db(DB_PATH)
    
    print(f"🎯 Scraping Medium posts for @{username_clean}\n")
    print("=" * 60)
    
    all_posts = {}
    
    # Try profile page
    print("📄 Fetching profile page...")
    try:
        resp = requests.get(f"https://medium.com/@{username_clean}", impersonate='chrome')
        if resp.status_code == 200:
            posts = extract_posts_from_profile(resp.text, username_clean)
            for p in posts:
                all_posts[p["slug"]] = p
            print(f"   Found {len(posts)} posts on profile page")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Try RSS feed
    print("📡 Fetching RSS feed...")
    try:
        resp = requests.get(f"https://medium.com/feed/@{username_clean}", impersonate='chrome')
        if resp.status_code == 200:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(resp.text.encode('utf-8'))
            for item in root.findall('.//item'):
                link = item.find('link')
                if link is not None and link.text:
                    slug_match = re.search(rf'/{username_clean}/([a-z0-9-]+)/', link.text)
                    if slug_match:
                        slug = slug_match.group(1)
                        if len(slug) > 10 and slug not in all_posts:
                            all_posts[slug] = {
                                "slug": slug,
                                "url": link.text
                            }
            print(f"   Found {len(all_posts)} total unique posts")
    except Exception as e:
        print(f"   Error: {e}")
    
    posts_list = list(all_posts.values())
    
    # Add metadata
    scraped_at = time.strftime("%Y-%m-%d %H:%M:%S")
    for post in posts_list:
        post["scraped_at"] = scraped_at
    
    # Save to database
    saved = save_posts_to_db(DB_PATH, posts_list)
    
    # Save as JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "username": username_clean,
            "total_posts": len(posts_list),
            "scraped_at": scraped_at,
            "posts": posts_list
        }, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("✅ SCRAPING COMPLETE")
    print("=" * 60)
    print(f"📊 Total posts scraped: {len(posts_list)}")
    print(f"💾 Saved to database: {saved}")
    print(f"📄 JSON backup: {OUTPUT_FILE}")
    print(f"🗄️ Database: {DB_PATH}")
    
    if len(posts_list) < 10:
        print("\n⚠️ NOTE: Medium only allows access to ~10 most recent posts")
        print("   For full archive, export from Medium Dashboard")
    
    return posts_list

def get_posts_from_db():
    """Retrieve all posts from local database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT slug, url, title, published_date, word_count FROM medium_posts ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [
        {"slug": r[0], "url": r[1], "title": r[2], "published_date": r[3], "word_count": r[4]}
        for r in rows
    ]

def add_title_and_date_to_db():
    """Fetch titles and dates from individual post pages."""
    print("\n📝 Enriching posts with titles and dates...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT slug, url FROM medium_posts WHERE title = '' OR title IS NULL")
    posts = cursor.fetchall()
    conn.close()
    
    for slug, url in posts:
        try:
            resp = requests.get(url, impersonate='chrome', timeout=10)
            if resp.status_code == 200:
                # Extract title
                title_match = re.search(r'<title>([^<]+)</title>', resp.text)
                title = title_match.group(1).replace(f' – {USERNAME} – Medium', '') if title_match else ""
                
                # Extract date
                date_match = re.search(r'"datePublished"\s*:\s*"([^"]+)"', resp.text)
                pub_date = date_match.group(1) if date_match else ""
                
                if title or pub_date:
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE medium_posts 
                        SET title = ?, published_date = ?
                        WHERE slug = ?
                    """, (title, pub_date, slug))
                    conn.commit()
                    conn.close()
                    print(f"   Updated: {title[:50] if title else slug}...")
            
            time.sleep(0.5)  # Rate limiting
        except Exception as e:
            print(f"   Error fetching {url}: {e}")
    
    print("✅ Enrichment complete")

if __name__ == "__main__":
    posts = scrape_medium(USERNAME)
    
    if posts:
        print("\n📋 All posts:")
        for i, p in enumerate(posts, 1):
            print(f"   {i}. {p['slug']}")