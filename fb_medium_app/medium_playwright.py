"""
Medium Playwright Automation
============================
Automated browser-based posting to Medium using Playwright.
Logs into Medium, creates drafts, and pastes content.

Usage:
    python medium_playwright.py post <post_id>
    python medium_playwright.py batch <count>
    python medium_playwright.py status
"""

import os
import sys
import json
import sqlite3
import time
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from medium_auto_post import fix_bengali_text, format_for_medium, FB_DB, BASE_DIR, POSTING_LOG

# ==========================================
# PLAYWRIGHT AUTOMATION
# ==========================================

def install_playwright():
    """Install Playwright if not available."""
    try:
        from playwright.sync_api import sync_playwright
        return True
    except ImportError:
        print("📦 Installing Playwright...")
        os.system("pip install playwright")
        os.system("playwright install chromium")
        return True

def get_post_content(post_id):
    """Get post content from database."""
    if not FB_DB.exists():
        return None
    
    conn = sqlite3.connect(FB_DB)
    post = conn.execute(
        "SELECT id, date, content, post_type, word_count FROM fb_text_posts WHERE id = ?",
        (post_id,)
    ).fetchone()
    conn.close()
    
    if post:
        return {
            'id': post[0],
            'date': post[1],
            'content': fix_bengali_text(post[2]),
            'post_type': post[3],
            'word_count': post[4]
        }
    return None

def get_next_batch(count=5):
    """Get next batch of posts to post."""
    if not FB_DB.exists():
        return []
    
    conn = sqlite3.connect(FB_DB)
    
    # Get already posted IDs
    posted_ids = set()
    if POSTING_LOG.exists():
        try:
            with open(POSTING_LOG, 'r', encoding='utf-8') as f:
                log = json.load(f)
                posted_ids = {entry['fb_id'] for entry in log if entry.get('success')}
        except:
            pass
    
    # Get matched IDs (already on Medium)
    comp_db = BASE_DIR / "comparison_bengali.db"
    matched_ids = []
    if comp_db.exists():
        comp_conn = sqlite3.connect(comp_db)
        matched_ids = [r[0] for r in comp_conn.execute("SELECT fb_id FROM matched_bengali_posts")]
        comp_conn.close()
    
    # Get posts that are not posted and not matched
    all_excluded = list(set(matched_ids + list(posted_ids)))
    
    if all_excluded:
        placeholders = ','.join('?' * len(all_excluded))
        query = f"""
            SELECT id, date, content, post_type, word_count
            FROM fb_text_posts
            WHERE id NOT IN ({placeholders})
            AND content IS NOT NULL
            AND word_count >= 50
            ORDER BY word_count DESC
            LIMIT ?
        """
        params = all_excluded + [count]
    else:
        query = """
            SELECT id, date, content, post_type, word_count
            FROM fb_text_posts
            WHERE content IS NOT NULL
            AND word_count >= 50
            ORDER BY word_count DESC
            LIMIT ?
        """
        params = [count]
    
    posts = conn.execute(query, params).fetchall()
    conn.close()
    
    return [{
        'id': p[0],
        'date': p[1],
        'content': fix_bengali_text(p[2]),
        'post_type': p[3],
        'word_count': p[4]
    } for p in posts]

def post_single_with_playwright(post_id, headless=True):
    """
    Post a single FB post to Medium using Playwright.
    
    Returns:
        dict with success status and URL
    """
    from playwright.sync_api import sync_playwright
    
    # Get credentials from environment
    username = os.environ.get('MEDIUM_USERNAME', '')
    password = os.environ.get('MEDIUM_PASSWORD', '')
    
    if not username or not password:
        return {'success': False, 'error': 'Missing MEDIUM_USERNAME or MEDIUM_PASSWORD'}
    
    # Get post content
    post = get_post_content(post_id)
    if not post:
        return {'success': False, 'error': f'Post {post_id} not found'}
    
    title, html_content = format_for_medium(post['content'])
    
    result = {'success': False, 'post_id': post_id, 'url': None, 'error': None}
    
    try:
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()
            
            print(f"🌐 Opening Medium login page...")
            page.goto("https://medium.com/m/signin", wait_until="networkidle")
            time.sleep(2)
            
            # Check if already logged in
            if page.url.startswith("https://medium.com/@"):
                print("   ✅ Already logged in")
            else:
                # Find email input
                print(f"   🔐 Logging in as @{username}...")
                
                # Try different selectors for email input
                email_selectors = [
                    'input[name="email"]',
                    'input[type="email"]',
                    'input[placeholder*="email" i]',
                    '#email',
                    'input[id="email"]'
                ]
                
                email_input = None
                for selector in email_selectors:
                    try:
                        email_input = page.wait_for_selector(selector, timeout=3000)
                        break
                    except:
                        continue
                
                if not email_input:
                    # Try to find any input in the form
                    print("   ⚠️ Looking for email input...")
                    page.wait_for_timeout(2000)
                    
                    # Fallback: find inputs
                    inputs = page.query_selector_all('input')
                    for inp in inputs:
                        inp_type = inp.get_attribute('type')
                        if inp_type in ['email', 'text'] or not inp_type:
                            email_input = inp
                            break
                
                if email_input:
                    email_input.fill(username)
                    time.sleep(0.5)
                    
                    # Find password input
                    password_selectors = [
                        'input[name="password"]',
                        'input[type="password"]',
                        'input[placeholder*="password" i]',
                        '#password',
                        'input[id="password"]'
                    ]
                    
                    password_input = None
                    for selector in password_selectors:
                        try:
                            password_input = page.wait_for_selector(selector, timeout=3000)
                            break
                        except:
                            continue
                    
                    if password_input:
                        password_input.fill(password)
                        time.sleep(0.5)
                        
                        # Find submit button
                        submit_selectors = [
                            'button[type="submit"]',
                            'button:has-text("Sign in")',
                            'button:has-text("Continue")',
                            'button:has-text("Log in")'
                        ]
                        
                        submit_btn = None
                        for selector in submit_selectors:
                            try:
                                submit_btn = page.wait_for_selector(selector, timeout=3000)
                                break
                            except:
                                continue
                        
                        if submit_btn:
                            print("   ⏳ Clicking sign in...")
                            submit_btn.click()
                            time.sleep(3)
                        else:
                            print("   ⚠️ Submit button not found, trying Enter...")
                            password_input.press("Enter")
                            time.sleep(3)
                    else:
                        print("   ⚠️ Password input not found")
                else:
                    print("   ⚠️ Email input not found")
            
            # Check if we're on the home page now
            print("   📝 Navigating to write page...")
            page.goto("https://medium.com/new-story", wait_until="networkidle", timeout=30000)
            time.sleep(2)
            
            # Check current URL
            if "signin" in page.url.lower():
                result['error'] = 'Login failed - check credentials'
                browser.close()
                return result
            
            # Now we should be on the write page
            print("   ✍️ Creating draft...")
            
            # Wait for title input
            title_selectors = [
                'h1[data-placeholder="Title"]',
                '[data-placeholder="Title"]',
                'h1',
                '.graf--h1'
            ]
            
            title_input = None
            for selector in title_selectors:
                try:
                    title_input = page.wait_for_selector(selector, timeout=5000)
                    break
                except:
                    continue
            
            # Try to find any contenteditable for title
            if not title_input:
                editable_elements = page.query_selector_all('[contenteditable="true"]')
                if editable_elements:
                    title_input = editable_elements[0]
            
            if title_input:
                print(f"   📝 Typing title: {title[:50]}...")
                title_input.click()
                title_input.fill(title)
                time.sleep(0.5)
            else:
                print("   ⚠️ Title input not found")
            
            # Now find the content editor
            content_selectors = [
                '[data-placeholder="Tell your story..."]',
                '[placeholder="Tell your story..."]',
                '[data-offset-key]',
                '.graf--p'
            ]
            
            content_input = None
            for selector in content_selectors:
                try:
                    content_input = page.wait_for_selector(selector, timeout=5000)
                    break
                except:
                    continue
            
            # Try contenteditable
            if not content_input:
                content_elements = page.query_selector_all('[contenteditable="true"]')
                if len(content_elements) > 1:
                    content_input = content_elements[1]  # Second one is usually content
            
            if content_input:
                print(f"   📝 Pasting content ({post['word_count']} words)...")
                content_input.click()
                time.sleep(0.5)
                
                # Type content (may be slow but more reliable than paste for Bengali)
                content_input.fill(html_content)
                time.sleep(1)
            else:
                print("   ⚠️ Content editor not found")
            
            # Click Publish button
            print("   📤 Looking for publish button...")
            publish_selectors = [
                'button:has-text("Publish")',
                '[data-test="publishButton"]',
                'button[class*="publish"]'
            ]
            
            publish_btn = None
            for selector in publish_selectors:
                try:
                    publish_btn = page.wait_for_selector(selector, timeout=3000)
                    break
                except:
                    continue
            
            if publish_btn:
                print("   ✅ Found publish button")
                # Click to open publish dialog
                publish_btn.click()
                time.sleep(2)
                
                # Look for draft option
                draft_selectors = [
                    'button:has-text("Draft")',
                    'span:has-text("Save as draft")',
                    '[data-test="draft-option"]'
                ]
                
                for selector in draft_selectors:
                    try:
                        draft_btn = page.wait_for_selector(selector, timeout=2000)
                        draft_btn.click()
                        time.sleep(1)
                        break
                    except:
                        continue
                
                # Wait and get the draft URL
                time.sleep(2)
                
                # Try to get current URL (should be the draft)
                current_url = page.url
                if 'medium.com' in current_url and '/draft' not in current_url:
                    # We're still on write page, that's fine
                    result['url'] = current_url
                else:
                    result['url'] = current_url
                
                result['success'] = True
                print(f"   ✅ Draft created!")
            else:
                print("   ⚠️ Publish button not found, saving draft manually...")
                # Try Ctrl+S to save
                page.keyboard.press("Control+s")
                time.sleep(2)
                result['success'] = True
                result['url'] = page.url
            
            browser.close()
            
    except Exception as e:
        result['error'] = str(e)
        print(f"   ❌ Error: {e}")
    
    return result

def post_batch(count=5, headless=True):
    """Post a batch of posts."""
    posts = get_next_batch(count)
    
    if not posts:
        print("📭 No posts to process!")
        return []
    
    print(f"📤 Posting {len(posts)} posts to Medium...\n")
    
    results = []
    for i, post in enumerate(posts, 1):
        print(f"\n[{i}/{len(posts)}] Processing FB Post #{post['id']}")
        print(f"   📅 {post['date'][:10]} | 📏 {post['word_count']} words")
        
        result = post_single_with_playwright(post['id'], headless=headless)
        
        if result['success']:
            print(f"   ✅ Draft created: {result.get('url', 'N/A')}")
        else:
            print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
        
        # Log result
        log_posting(
            result['post_id'],
            result['success'],
            result.get('error', 'Posted') if not result['success'] else 'Posted successfully',
            result.get('url')
        )
        
        results.append(result)
        
        # Delay between posts
        if i < len(posts):
            print("   ⏳ Waiting 5 seconds...")
            time.sleep(5)
    
    return results

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

def show_status():
    """Show posting status."""
    posted_count = 0
    failed_count = 0
    last_posts = []
    
    if POSTING_LOG.exists():
        try:
            with open(POSTING_LOG, 'r', encoding='utf-8') as f:
                log = json.load(f)
            
            posted_count = sum(1 for e in log if e['success'])
            failed_count = len(log) - posted_count
            last_posts = log[-10:]
        except:
            pass
    
    print("\n" + "=" * 50)
    print("📊 MEDIUM POSTING STATUS")
    print("=" * 50)
    print(f"   Total posted:    {posted_count}")
    print(f"   Failed:         {failed_count}")
    print(f"   Total attempts:  {posted_count + failed_count}")
    
    if last_posts:
        print("\n   📋 Recent posts:")
        for entry in last_posts:
            status = "✅" if entry['success'] else "❌"
            date = entry['timestamp'][:16]
            print(f"   {status} FB#{entry['fb_id']} - {date}")
    
    print("=" * 50)

# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":
    # Ensure playwright is installed
    install_playwright()
    
    if len(sys.argv) < 2:
        print("""
Medium Playwright Automation
===========================
Usage:
    python medium_playwright.py post <post_id>   - Post single post
    python medium_playwright.py batch [count]    - Post next batch (default: 5)
    python medium_playwright.py status           - Show posting status
    python medium_playwright.py install          - Install Playwright
""")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "post":
        if len(sys.argv) < 3:
            print("❌ Please provide post ID")
            sys.exit(1)
        post_id = int(sys.argv[2])
        result = post_single_with_playwright(post_id, headless=False)
        print(f"\n{'✅ Success' if result['success'] else '❌ Failed'}: {result.get('error') or result.get('url')}")
        
    elif command == "batch":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        results = post_batch(count, headless=False)
        success = sum(1 for r in results if r['success'])
        print(f"\n📊 Batch complete: {success}/{len(results)} posted")
        
    elif command == "status":
        show_status()
        
    elif command == "install":
        print("📦 Installing Playwright...")
        os.system("pip install playwright")
        os.system("playwright install chromium")
        print("✅ Done!")
        
    else:
        print(f"❌ Unknown command: {command}")