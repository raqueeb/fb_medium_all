import urllib.request
import json
import xml.etree.ElementTree as ET
import re
from difflib import SequenceMatcher

def get_medium_user_id(api_token):
    """Get Medium user ID using the integration token."""
    if api_token == "YOUR_MEDIUM_INTEGRATION_TOKEN":
        return None
    
    try:
        req = urllib.request.Request(
            "https://medium.com",
            headers={"Authorization": f"Bearer {api_token}"}
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data["data"]["id"]
    except Exception as e:
        print(f"Error getting user ID: {e}")
        return None

def fetch_medium_rss_posts(username):
    """Fetch published Medium posts via RSS feed (limited to ~10 posts)."""
    # Remove @ if included
    username_clean = username.replace("@", "")
    url = f"https://medium.com/feed/@{username_clean}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            content = response.read().decode('utf-8')
            root = ET.fromstring(content)
            
        articles = []
        for item in root.findall('.//item'):
            title = item.find('title').text if item.find('title') is not None else ""
            link = item.find('link').text if item.find('link') is not None else ""
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
            
            # Try content:encoded which is commonly used
            content_elem = item.find('content:encoded') or item.find('{http://purl.org/rss/1.0/modules/content/}encoded')
            if content_elem is None:
                # Try alternative namespace
                for child in item:
                    if 'encoded' in child.tag:
                        content_elem = child
                        break
            content = content_elem.text if content_elem is not None else ""
            
            # Extract slug from link
            slug = ""
            if link:
                parts = link.split('/')
                for part in parts:
                    if re.match(r'^[a-f0-9]{12}$', part):
                        slug = part
                        break
            
            articles.append({
                'title': title, 
                'content': content,
                'link': link,
                'slug': slug,
                'pub_date': pub_date
            })
        return articles
    except Exception as e:
        print(f"Warning: Could not fetch Medium RSS feed: {e}")
        return []

def fetch_all_medium_posts(username):
    """
    Fetch ALL Medium posts by scraping the profile page.
    Returns list of all posts with title, slug, link, and date.
    """
    username_clean = username.replace("@", "")
    
    posts = []
    page = 1
    
    while True:
        # Medium uses pagination with ?page=X
        if page == 1:
            url = f"https://medium.com/@{username_clean}"
        else:
            url = f"https://medium.com/@{username_clean}?page={page}"
        
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            with urllib.request.urlopen(req) as response:
                html = response.read().decode('utf-8')
            
            # Parse posts from the page
            # Medium uses data-source-feed or article cards
            post_pattern = r'href="(https://medium\.com/@' + re.escape(username_clean) + r'/[^"]+)"[^>]*>.*?<img[^>]*title="([^"]*)"'
            
            # Alternative pattern: look for article links
            article_pattern = r'"slug":"([^"]+)".*?"title":"([^"]+)".*?"createdAt":(\d+)'
            
            # Find all article cards with title and link
            card_pattern = r'<article[^>]*>.*?<a[^>]*href="(/@' + re.escape(username_clean) + r'/[^?#"]+)"[^>]*>.*?<img[^>]*alt="([^"]*)"'
            
            # Try to extract posts
            found_any = False
            
            # Pattern 1: Image-based cards
            img_pattern = r'<img[^>]*alt="([^"]+)"[^>]*src="[^"]*"[^>]*>.*?<a[^>]*href="(/@' + re.escape(username_clean) + r'/[^?#"]+)"'
            
            for match in re.finditer(img_pattern, html, re.DOTALL):
                title = match.group(1).strip()
                link = "https://medium.com" + match.group(2)
                slug = match.group(2).split('/')[-1]
                
                if title and slug and slug not in [p.get('slug', '') for p in posts]:
                    posts.append({
                        'title': title,
                        'slug': slug,
                        'link': link,
                        'pub_date': ''
                    })
                    found_any = True
            
            # Pattern 2: Script data with post info
            script_pattern = r'window\.__hep\.push\((.*?)\);'
            for match in re.finditer(script_pattern, html):
                try:
                    data = json.loads(match.group(1))
                    if 'title' in data and 'slug' in data:
                        posts.append({
                            'title': data['title'],
                            'slug': data['slug'],
                            'link': f"https://medium.com/@{username_clean}/{data['slug']}",
                            'pub_date': data.get('createdAt', '')
                        })
                        found_any = True
                except:
                    pass
            
            # Pattern 3: Use RSS as base + follow pagination
            # Check if there's a "Load more" or next page indicator
            if not found_any:
                # Check for pagination or end marker
                if 'No more stories' in html or page > 50:
                    break
                # Try to find more posts in the page
                link_pattern = r'"(?:url|link)":"(https://medium\.com/@' + re.escape(username_clean) + r'/([^"]+))"'
                for match in re.finditer(link_pattern, html):
                    full_link = match.group(1)
                    slug = match.group(2)
                    if slug and slug not in [p.get('slug', '') for p in posts]:
                        posts.append({
                            'title': slug,  # Will be replaced if we get title
                            'slug': slug,
                            'link': full_link,
                            'pub_date': ''
                        })
                        found_any = True
            
            # If no posts found on this page, we've reached the end
            if not found_any and page > 1:
                break
            
            page += 1
            
            # Safety limit
            if page > 20:
                break
                
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break
    
    return posts

def get_medium_profile_stats(username):
    """Get comprehensive stats for a Medium profile."""
    username_clean = username.replace("@", "")
    
    posts = fetch_all_medium_posts(username_clean)
    
    stats = {
        'total_posts': len(posts),
        'posts': posts
    }
    
    return stats

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

def push_to_medium(post_id, fb_text, api_token):
    """
    Push a single post to Medium as a DRAFT.
    Returns (success: bool, message: str, draft_url: str or None)
    """
    if api_token == "YOUR_MEDIUM_INTEGRATION_TOKEN" or not api_token:
        return False, "Invalid or missing API token", None
    
    title, html_content = format_facebook_to_medium_html(fb_text)
    
    try:
        # Get user ID
        user_id = get_medium_user_id(api_token)
        if not user_id:
            return False, "Failed to authenticate with Medium", None
        
        # Prepare payload
        payload = {
            "title": title,
            "contentFormat": "html",
            "content": html_content,
            "publishStatus": "draft"
        }
        
        # Post to Medium
        post_url = f"https://medium.com/v1/posts"
        data_bytes = json.dumps(payload).encode('utf-8')
        
        post_req = urllib.request.Request(
            post_url,
            data=data_bytes,
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        
        with urllib.request.urlopen(post_req) as response:
            res_data = json.loads(response.read().decode())
            draft_url = res_data.get("data", {}).get("url", None)
            return True, "Successfully pushed to Medium", draft_url
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        return False, f"HTTP Error {e.code}: {error_body}", None
    except Exception as e:
        return False, f"Error: {str(e)}", None

def check_post_on_medium(fb_text, medium_posts, threshold=0.75):
    """
    Check if a Facebook post already exists on Medium using fuzzy matching.
    Returns True if found on Medium, False otherwise.
    """
    fb_preview = fb_text[:400].lower().strip()
    
    for med_article in medium_posts:
        med_preview = med_article['content'][:400].lower()
        # Remove HTML tags for better comparison
        import re
        med_preview_clean = re.sub(r'<[^>]+>', '', med_preview)
        
        similarity = SequenceMatcher(None, fb_preview, med_preview_clean).ratio()
        if similarity > threshold:
            return True
    
    return False

def validate_posts_against_medium(posts, medium_posts):
    """
    Validate a list of posts against Medium posts.
    Returns list of posts that are missing on Medium.
    """
    missing_posts = []
    
    for post in posts:
        if post['status'] == 'pending':
            is_on_medium = check_post_on_medium(post['content'], medium_posts)
            if is_on_medium:
                # This post is already on Medium
                post['status'] = 'replicated'
                missing_posts.append(post)  # Add to list as "replicated" (not missing)
            else:
                missing_posts.append(post)  # Actually missing
    
    return missing_posts