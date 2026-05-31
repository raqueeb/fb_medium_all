"""
Fetch all Medium posts for a user by scraping the profile page.
"""
import urllib.request
import re
import json

def fetch_all_medium_posts(username):
    """Fetch ALL Medium posts by scraping the profile page."""
    username_clean = username.replace("@", "")
    
    all_posts = []
    seen_slugs = set()
    
    # Try both the base URL and pagination
    for page in range(1, 50):
        if page == 1:
            url = f"https://medium.com/@{username_clean}"
        else:
            url = f"https://medium.com/@{username_clean}?page={page}"
        
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            })
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8', errors='ignore')
            
            # Extract post links - Medium uses relative links like /@username/slug
            rel_pattern = rf'href="/@{re.escape(username_clean)}/([a-z0-9-]+)"'
            abs_pattern = rf'href="https://medium\.com/@{re.escape(username_clean)}/([a-z0-9-]+)'
            
            found_on_page = 0
            
            for pattern in [rel_pattern, abs_pattern]:
                for match in re.finditer(pattern, html):
                    slug = match.group(1)
                    if slug and slug not in seen_slugs:
                        seen_slugs.add(slug)
                        all_posts.append({
                            'slug': slug,
                            'url': f"https://medium.com/@{username_clean}/{slug}"
                        })
                        found_on_page += 1
            
            # If no new posts found, we've reached the end
            if found_on_page == 0 and page > 1:
                break
                
            print(f"Page {page}: found {found_on_page} new posts (total: {len(all_posts)})")
            
        except Exception as e:
            print(f"Error on page {page}: {e}")
            break
    
    return all_posts

if __name__ == "__main__":
    username = input("Enter Medium username (without @): ").strip() or "raqueeb"
    
    print(f"Fetching all posts for @{username}...")
    posts = fetch_all_medium_posts(username)
    
    print(f"\n✅ Total posts found: {len(posts)}")
    print("\nPosts:")
    for i, post in enumerate(posts, 1):
        print(f"{i:3}. {post['slug']}")