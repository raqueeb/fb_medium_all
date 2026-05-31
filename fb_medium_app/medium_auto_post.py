"""
Medium Auto-Post Script
======================
Automate posting Facebook posts to Medium using the unofficial API.
Uses credentials from environment variables.
"""

import os
import re
import json
import sqlite3
import urllib.request
import urllib.parse
import http.cookiejar
from pathlib import Path
from datetime import datetime

# ==========================================
# CONFIGURATION
# ==========================================

# Get credentials from environment
MEDIUM_USERNAME = os.environ.get('MEDIUM_USERNAME', '')
MEDIUM_PASSWORD = os.environ.get('MEDIUM_PASSWORD', '')

# Database paths
BASE_DIR = Path(__file__).parent.parent
FB_DB = BASE_DIR / "fb_posts.db"
POSTING_LOG = BASE_DIR / "medium_posting_log.json"

# ==========================================
# MEDIUM API (UNOFFICIAL)
# ==========================================

class MediumAPI:
    """Unofficial Medium API for creating draft posts."""
    
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.cookies = None
        self.token = None
        self.user_id = None
        
    def login(self):
        """
        Login to Medium using the web interface.
        Returns True if successful, False otherwise.
        """
        if not self.username or not self.password:
            print("❌ Missing username or password")
            return False
        
        print(f"🔐 Attempting login as @{self.username}...")
        
        # Create password manager
        import urllib.request
        import urllib.parse
        
        # Step 1: Get the login page to extract CSRF token
        login_url = "https://medium.com/m/signin"
        
        try:
            # Create opener with cookie jar
            cj = http.cookiejar.CookieJar()
            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
            opener.addheaders = [
                ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
                ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
            ]
            
            # Get login page
            req = urllib.request.Request(login_url)
            with opener.open(req) as response:
                login_html = response.read().decode('utf-8')
            
            # Extract CSRF token from cookies or page
            csrf_token = None
            for cookie in cj:
                if cookie.name == 'csrf':
                    csrf_token = cookie.value
                    break
            
            if not csrf_token:
                # Try to extract from page
                csrf_match = re.search(r'name="csrf"[^>]*value="([^"]+)"', login_html)
                if csrf_match:
                    csrf_token = csrf_match.group(1)
            
            if not csrf_token:
                print("⚠️ Could not extract CSRF token, attempting anyway...")
                csrf_token = "dummy_token"
            
            print(f"   CSRF token: {csrf_token[:20]}...")
            
            # Step 2: Submit login form
            login_data = urllib.parse.urlencode({
                'username': self.username,
                'password': self.password,
                'csrf': csrf_token,
                'source': 'https://medium.com'
            }).encode('utf-8')
            
            login_post_url = "https://medium.com/_/api/users/login"
            req = urllib.request.Request(
                login_post_url,
                data=login_data,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRF-Token': csrf_token,
                    'Referer': login_url
                }
            )
            
            with opener.open(req) as response:
                result = response.read().decode('utf-8')
            
            # Check for success
            try:
                result_json = json.loads(result)
                if result_json.get('success'):
                    self.token = result_json.get('token', '')
                    self.user_id = result_json.get('userId', '')
                    self.cookies = opener
                    print(f"   ✅ Login successful! User ID: {self.user_id[:10]}...")
                    return True
                else:
                    print(f"   ❌ Login failed: {result_json.get('error', 'Unknown error')}")
                    return False
            except json.JSONDecodeError:
                print(f"   ⚠️ Could not parse login response")
                # Still try to extract cookies
                self.cookies = opener
                return False
                
        except Exception as e:
            print(f"   ❌ Login error: {e}")
            return False
    
    def create_draft(self, title, content, tags=None):
        """
        Create a draft post on Medium.
        
        Args:
            title: Post title
            content: HTML content
            tags: List of tags (max 5)
            
        Returns:
            dict with success status and draft URL
        """
        if not self.token and not self.login():
            return {'success': False, 'error': 'Not authenticated'}
        
        # Prepare content
        if tags is None:
            tags = []
        
        # Medium API endpoint
        api_url = f"https://medium.com/_/api/posts"
        
        payload = {
            'title': title[:500],  # Medium has title limits
            'contentFormat': 'html',
            'content': content,
            'publishStatus': 'draft',
            'tags': tags[:5]  # Max 5 tags
        }
        
        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                api_url,
                data=data,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.token}',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                }
            )
            
            with self.cookies.open(req) as response:
                result = json.loads(response.read().decode('utf-8'))
            
            if 'success' in result and result['success']:
                post_id = result.get('data', {}).get('postId', '')
                return {
                    'success': True,
                    'post_id': post_id,
                    'url': f"https://medium.com/@{self.username}/{post_id}"
                }
            else:
                return {'success': False, 'error': result.get('error', 'Unknown error')}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def fix_bengali_text(text):
    """Fix Bengali encoding issues."""
    if not text:
        return ""
    try:
        return text.encode('latin-1').decode('utf-8')
    except:
        return text

def is_bengali(text):
    """Check if text contains Bengali characters."""
    if not text:
        return False
    bengali_pattern = re.compile(r'[\u0980-\u09FF]')
    return bool(bengali_pattern.search(text))

def extract_bengali_content(text):
    """Extract Bengali portions from mixed content."""
    if not text:
        return ""
    lines = text.split('\n')
    bengali_lines = [line for line in lines if is_bengali(line)]
    return '\n'.join(bengali_lines)

def format_for_medium(content, title=None):
    """
    Convert Facebook post to Medium HTML format.
    
    Args:
        content: Plain text or HTML content
        title: Optional title (will be extracted from first line if not provided)
        
    Returns:
        tuple of (title, html_content)
    """
    # Fix encoding
    content = fix_bengali_text(content)
    
    # Extract title from first non-empty line if not provided
    if not title:
        lines = content.strip().split('\n')
        for line in lines:
            if line.strip() and len(line.strip()) > 5:
                title = line.strip()[:100]
                break
        if not title:
            title = datetime.now().strftime("%Y-%m-%d Post")
    
    # Convert to HTML
    html_parts = [f"<h1>{title}</h1>"]
    
    lines = content.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if line looks like a header (short, no ending punctuation)
        if len(line) < 50 and not line.endswith('.') and not line.endswith('!') and not line.endswith('?'):
            # Check if it's actually a subheader
            if line.startswith('#'):
                html_parts.append(f"<h2>{line[1:].strip()}</h2>")
            else:
                html_parts.append(f"<h3>{line}</h3>")
        else:
            # Escape HTML and wrap in paragraph
            escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            html_parts.append(f"<p>{escaped}</p>")
    
    html_content = '\n'.join(html_parts)
    return title, html_content

def get_unmatched_posts(min_words=100, limit=10):
    """
    Get Facebook posts that haven't been posted to Medium yet.
    """
    if not FB_DB.exists():
        print("❌ FB database not found")
        return []
    
    conn = sqlite3.connect(FB_DB)
    
    # Get matched FB IDs
    comp_db = BASE_DIR / "comparison_bengali.db"
    matched_ids = []
    if comp_db.exists():
        comp_conn = sqlite3.connect(comp_db)
        matched_ids = [r[0] for r in comp_conn.execute("SELECT fb_id FROM matched_bengali_posts")]
        comp_conn.close()
    
    # Get posting log to exclude already posted
    posted_ids = set()
    if POSTING_LOG.exists():
        with open(POSTING_LOG, 'r', encoding='utf-8') as f:
            log = json.load(f)
            posted_ids = {entry['fb_id'] for entry in log if entry.get('success')}
    
    # Build query for posts that are:
    # 1. Not matched to any Medium post
    # 2. Not already attempted to post
    # 3. Have significant content (min_words)
    all_excluded = list(set(matched_ids + list(posted_ids)))
    
    if all_excluded:
        placeholders = ','.join('?' * len(all_excluded))
        query = f"""
            SELECT id, date, content, post_type, word_count
            FROM fb_text_posts
            WHERE id NOT IN ({placeholders})
            AND content IS NOT NULL
            AND word_count >= ?
            ORDER BY word_count DESC
            LIMIT ?
        """
        params = all_excluded + [min_words, limit]
    else:
        query = """
            SELECT id, date, content, post_type, word_count
            FROM fb_text_posts
            WHERE content IS NOT NULL
            AND word_count >= ?
            ORDER BY word_count DESC
            LIMIT ?
        """
        params = [min_words, limit]
    
    posts = conn.execute(query, params).fetchall()
    conn.close()
    
    return posts

def log_posting(fb_id, success, message, url=None):
    """Log posting attempt to file."""
    log_entries = []
    
    if POSTING_LOG.exists():
        try:
            with open(POSTING_LOG, 'r', encoding='utf-8') as f:
                log_entries = json.load(f)
        except:
            log_entries = []
    
    entry = {
        'fb_id': fb_id,
        'success': success,
        'message': message,
        'url': url,
        'timestamp': datetime.now().isoformat()
    }
    
    log_entries.append(entry)
    
    with open(POSTING_LOG, 'w', encoding='utf-8') as f:
        json.dump(log_entries, f, ensure_ascii=False, indent=2)

def post_to_medium(post_id, content):
    """
    Post a single Facebook post to Medium as a draft.
    
    Returns:
        dict with success status and details
    """
    # Initialize API
    api = MediumAPI(MEDIUM_USERNAME, MEDIUM_PASSWORD)
    
    # Format content
    title, html_content = format_for_medium(content)
    
    # Create draft
    result = api.create_draft(title, html_content)
    
    # Log result
    log_posting(
        post_id,
        result.get('success', False),
        result.get('error', 'Posted successfully'),
        result.get('url')
    )
    
    return result

# ==========================================
# MAIN FUNCTIONS
# ==========================================

def post_next_batch(count=5):
    """
    Post the next batch of unmatched posts to Medium.
    
    Args:
        count: Number of posts to process
        
    Returns:
        list of results
    """
    posts = get_unmatched_posts(min_words=100, limit=count)
    
    if not posts:
        print("📭 No posts to process")
        return []
    
    print(f"📤 Processing {len(posts)} posts...")
    
    results = []
    for post in posts:
        post_id, date, content, post_type, word_count = post
        
        print(f"\n📝 Processing FB post #{post_id} ({date[:10]}, {word_count} words)...")
        
        # Format and post
        title, html = format_for_medium(content)
        print(f"   Title: {title[:50]}...")
        
        # Attempt to post (may fail due to API limitations)
        result = post_to_medium(post_id, content)
        
        if result.get('success'):
            print(f"   ✅ Draft created: {result.get('url')}")
        else:
            print(f"   ❌ Failed: {result.get('error')}")
        
        results.append({
            'post_id': post_id,
            'result': result
        })
    
    return results

def view_posting_log():
    """View the posting log."""
    if not POSTING_LOG.exists():
        print("📭 No posting log found")
        return []
    
    with open(POSTING_LOG, 'r', encoding='utf-8') as f:
        log = json.load(f)
    
    return log

def clear_posting_log():
    """Clear the posting log (dangerous!)."""
    global POSTING_LOG
    if POSTING_LOG.exists():
        POSTING_LOG.unlink()
    print("✅ Posting log cleared")

# ==========================================
# CLI INTERFACE
# ==========================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("""
Medium Auto-Post Script
======================
Usage:
    python medium_auto_post.py post [count]   - Post next batch (default: 5)
    python medium_auto_post.py log            - View posting log
    python medium_auto_post.py clear          - Clear posting log
    python medium_auto_post.py status         - Show status
""")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "post":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        post_next_batch(count)
    elif command == "log":
        log = view_posting_log()
        print(f"📋 Posting log ({len(log)} entries):")
        for entry in log[-10:]:
            status = "✅" if entry['success'] else "❌"
            print(f"   {status} FB#{entry['fb_id']}: {entry['message'][:50]}")
    elif command == "clear":
        confirm = input("⚠️ Clear all posting history? (yes/no): ")
        if confirm.lower() == 'yes':
            clear_posting_log()
    elif command == "status":
        posts = get_unmatched_posts(min_words=100, limit=100)
        print(f"📊 Queue status:")
        print(f"   Unposted: {len(posts)}")
        
        log = view_posting_log()
        successful = sum(1 for e in log if e['success'])
        failed = len(log) - successful
        print(f"   Posted: {successful}")
        print(f"   Failed: {failed}")
    else:
        print(f"❌ Unknown command: {command}")