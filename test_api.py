"""Test Medium API endpoint for fetching all posts."""
import urllib.request
import json

username = 'raqueeb'

# Try the internal profile stream API
url = f'https://medium.com/_/api/users/{username}/profile/stream?source=profile_page'

req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X)',
    'Accept': 'application/json',
    'Referer': f'https://medium.com/@{username}',
})

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
        posts = data.get('references', {}).get('Post', {})
        print(f'Found {len(posts)} posts in API response')
        for key, post in list(posts.items())[:15]:
            title = post.get('title', 'N/A')
            slug = post.get('uniqueSlug', 'N/A')
            print(f"  - [{slug}] {title[:60]}")
except Exception as e:
    print('Error:', e)
    
    # Try alternative approach - RSS with pagination
    print("\nFalling back to RSS...")
    
import xml.etree.ElementTree as ET

rss_url = f'https://medium.com/feed/@{username}'
req2 = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req2, timeout=15) as resp:
    root = ET.fromstring(resp.read())
    
items = root.findall('.//item')
print(f'RSS returned {len(items)} posts')

for item in items:
    title = item.find('title').text if item.find('title') is not None else "Untitled"
    link = item.find('link').text if item.find('link') is not None else ""
    slug = link.split('/')[-1] if link else "N/A"
    print(f"  - [{slug}] {title[:60]}")