import os
import json
import sqlite3
import urllib.request
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher

# ==========================================
# CONFIGURATION
# ==========================================
FB_JSON_PATH = "your_activity_on_facebook/posts/your_posts_1.json"
DB_NAME = "social_posts.db"
MEDIUM_USERNAME = "your_medium_username"
# To push to Medium, get a token from Medium Settings > Security and apps > Integration tokens
MEDIUM_API_TOKEN = "YOUR_MEDIUM_INTEGRATION_TOKEN"  

# ==========================================
# 1. PARSE FACEBOOK JSON & FIX ENCODING
# ==========================================
def fix_fb_encoding(text):
    """Fixes Meta's broken JSON string encoding (Mojibake)."""
    if not text:
        return ""
    try:
        return text.encode('latin-1').decode('utf-8')
    except Exception:
        return text

def load_and_store_fb_posts(json_path, db_path):
    """Reads Facebook JSON, cleans it, and saves it into local SQLite DB."""
    if not os.path.exists(json_path):
        print(f"❌ Error: Cannot find file at {json_path}. Please check your unzipped folder.")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Establish SQLite connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS facebook_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER,
            content TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)

    inserted_count = 0
    # Meta lists posts as an array of objects containing a 'data' array
    for item in data:
        timestamp = item.get("timestamp", 0)
        post_data = item.get("data", [])
        
        for element in post_data:
            post_record = element.get("post", "")
            if post_record:
                clean_content = fix_fb_encoding(post_record)
                
                # Check if it already exists in DB to prevent duplicates on reruns
                cursor.execute("SELECT id FROM facebook_posts WHERE timestamp = ? AND content = ?", (timestamp, clean_content))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO facebook_posts (timestamp, content) VALUES (?, ?)", (timestamp, clean_content))
                    inserted_count += 1
                    
    conn.commit()
    conn.close()
    print(f"💾 Step 1 & 2 Complete: Loaded and saved {inserted_count} new posts to local SQLite database ({db_path}).")

# ==========================================
# 2. MATCH AND VALIDATE WITH MEDIUM
# ==========================================
def get_medium_posts(username):
    """Fetches published Medium posts using the official public RSS feed."""
    url = f"https://medium.com@{username}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            root = ET.fromstring(response.read())
            
        articles = []
        for item in root.findall('.//item'):
            title = item.find('title').text if item.find('title') is not None else ""
            content_elem = item.find('{http://purl.org}encoded')
            content = content_elem.text if content_elem is not None else ""
            articles.append({'title': title, 'content': content})
        return articles
    except Exception as e:
        print(f"⚠️ Warning: Could not fetch Medium feed ({e}). Proceeding assuming 0 posts on Medium.")
        return []

def run_validation_report(db_path, medium_username):
    """Compares SQLite posts against Medium feed and outputs a text report."""
    medium_posts = get_medium_posts(medium_username)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, content FROM facebook_posts WHERE status = 'pending'")
    pending_posts = cursor.fetchall()

    missing_posts = []
    already_posted_ids = []

    print("\n🔍 Cross-checking with Medium entries...")
    for post_id, fb_text in pending_posts:
        is_on_medium = False
        
        for med_article in medium_posts:
            # Fuzzy match top 400 characters to tolerate structural formatting edits
            similarity = SequenceMatcher(None, fb_text[:400].lower(), med_article['content'][:400].lower()).ratio()
            if similarity > 0.75:  # 75% match match threshold
                is_on_medium = True
                already_posted_ids.append(post_id)
                break
        
        if is_on_medium:
            # Update local DB status so we don't try to sync it later
            cursor.execute("UPDATE facebook_posts SET status = 'replicated' WHERE id = ?", (post_id,))
        else:
            missing_posts.append((post_id, fb_text))

    conn.commit()
    conn.close()

    # Generate Report File
    report_path = "validation_report.txt"
    with open(report_path, "w", encoding="utf-8") as rep:
        rep.write(f"=== POST VALIDATION REPORT FOR MEDIUM (@{medium_username}) ===\n")
        rep.write(f"Posts identified as already on Medium: {len(already_posted_ids)}\n")
        rep.write(f"Posts unique to Facebook (Missing on Medium): {len(missing_posts)}\n\n")
        rep.write("--- MISSING POSTS DETAILS ---\n")
        for p_id, text in missing_posts:
            rep.write(f"[ID: {p_id}] {text[:120]}...\n\n")

    print(f"📊 Step 3 Complete: Report written to '{report_path}'.")
    print(f"   - {len(already_posted_ids)} posts matched/marked as replicated.")
    print(f"   - {len(missing_posts)} posts waiting to be uploaded.")
    return missing_posts

# ==========================================
# 3. CONVERT FORMAT & PUSH ONE TEST POST
# ==========================================
def format_facebook_to_medium_html(fb_text):
    """
    Converts plain Facebook updates into Medium-compliant rich HTML.
    Modify this function to change paragraphs, headers, or add hashtags!
    """
    lines = fb_text.strip().split("\n")
    
    # Formatting Rule: Use the first non-empty line as the Main Article Title
    title = "Facebook Archive Update"
    for line in lines:
        if line.strip():
            title = line.strip()[:60] + "..." if len(line.strip()) > 60 else line.strip()
            break

    # Wrap raw text breaks into clean HTML paragraph wrappers for Medium
    html_body = f"<h1>{title}</h1>"
    for line in lines:
        if line.strip():
            # Check if line looks like a subheader (short, no punctuation)
            if len(line.strip()) < 40 and not line.strip().endswith('.'):
                html_body += f"<h3>{line.strip()}</h3>"
            else:
                html_body += f"<p>{line.strip()}</p>"
                
    return title, html_body

def push_single_post_to_medium(post_id, fb_text, api_token):
    """Pushes a single post to Medium as a DRAFT so you can manually check layout."""
    if api_token == "YOUR_MEDIUM_INTEGRATION_TOKEN":
        print("🛑 Error: You must supply a valid Medium API integration token to run updates.")
        return False

    title, html_content = format_facebook_to_medium_html(fb_text)

    # Get Medium User ID profile details via Token Authentication
    try:
        user_url = "https://medium.com"
        req = urllib.request.Request(user_url, headers={"Authorization": f"Bearer {api_token}"})
        with urllib.request.urlopen(req) as response:
            user_id = json.loads(response.read().decode())["data"]["id"]
            
        # Post Article Endpoint
        post_url = f"https://medium.com{user_id}/posts"
        payload = {
            "title": title,
            "contentFormat": "html",
            "content": html_content,
            "publishStatus": "draft" # Kept as draft so it won't instantly go public before you see it
        }
        
        data_bytes = json.dumps(payload).encode('utf-8')
        post_req = urllib.request.Request(
            post_url, 
            data=data_bytes, 
            headers={"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(post_req) as response:
            res_data = json.loads(response.read().decode())
            draft_url = res_data["data"]["url"]
            print(f"\n🚀 Step 4 Complete: Test post [ID: {post_id}] sent successfully!")
            print(f"🔗 View Draft Layout here: {draft_url}")
            print("⚠️ Check the layout. If you don't like it, change the 'format_facebook_to_medium_html' function rules before launching a batch.")
            return True
            
    except Exception as e:
        print(f"❌ Failed pushing to Medium: {e}")
        return False

# ==========================================
# MAIN ROUTINE PIPELINE RUNNER
# ==========================================
if __name__ == "__main__":
    # 1 & 2. Parse JSON and Save to Database
    print("Step 1 & 2: Extracting files from Export...")
    load_and_store_fb_posts(FB_JSON_PATH, DB_NAME)
    
    # 3. Run Validation Report 
    missing = run_validation_report(DB_NAME, MEDIUM_USERNAME)
    
    # 4. Push exact single post for a visual preview
    if missing:
        test_id, test_text = missing[0]
        print(f"\nReady to push a sample post for formatting evaluation.")
        choice = input(f"Do you want to send post ID {test_id} to Medium as a draft? (yes/no): ")
        if choice.lower() in ['yes', 'y']:
            push_single_post_to_medium(test_id, test_text, MEDIUM_API_TOKEN)
    else:
        print("\n🎉 Everything matches! No missing content needs replication.")
