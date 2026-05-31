"""
Fetch all Medium posts using scroll-like pagination.
Medium loads posts as you scroll - we'll try to find the pagination pattern.
"""
import urllib.request
import json
import re

def fetch_medium_posts_paginated(username):
    """Fetch Medium posts with pagination simulation."""
    username_clean = username.replace("@", "")
    
    all_posts = []
    seen_slugs = set()
    
    # Try different pagination patterns
    patterns = [
        # Pattern 1: page parameter
        lambda p: f"https://medium.com/@{username_clean}?page={p}",
        # Pattern 2: offset parameter  
        lambda p: f"https://medium.com/@{username_clean}?offset={p * 10}",
        # Pattern 3: load more with state
        lambda p: f"https://medium.com/@{username_clean}?source=profile_page&page={p}",
    ]
    
    for page in range(1, 20):
        for pattern in patterns[:1]:  # Try main pattern first
            url = pattern(page)
            
            try:
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X)',
                    'Accept': 'text/html,application/xhtml+xml',
                    'X-Requested-With': 'XMLHttpRequest',
                })
                
                with urllib.request.urlopen(req, timeout=10) as resp:
                    html = resp.read().decode('utf-8', errors='ignore')
                
                # Extract posts
                pattern_str = rf'/@{username_clean}/([a-z0-9-]+)'
                found = 0
                
                for match in re.finditer(pattern_str, html):
                    slug = match.group(1)
                    if slug and slug not in seen_slugs and len(slug) > 10:
                        seen_slugs.add(slug)
                        all_posts.append({
                            'slug': slug,
                            'url': f"https://medium.com/@{username_clean}/{slug}"
                        })
                        found += 1
                
                if found == 0 and page > 1:
                    print(f"No new posts on page {page}, stopping...")
                    break
                    
                print(f"Page {page}: found {found} new posts (total: {len(all_posts)})")
                
                if len(all_posts) >= 100:  # Safety limit
                    break
                    
            except Exception as e:
                pass  # Try next pattern
        
        if len(all_posts) >= 100:
            break
    
    return all_posts

if __name__ == "__main__":
    username = "raqueeb"
    print(f"Fetching posts for @{username} with pagination...")
    
    posts = fetch_medium_posts_paginated(username)
    print(f"\n✅ Total posts found: {len(posts)}")
    for i, p in enumerate(posts[:20], 1):
        print(f"  {i}. {p['slug']}")