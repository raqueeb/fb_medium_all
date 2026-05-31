"""Test RSS2JSON API for getting all posts."""
import urllib.request
import json

username = 'raqueeb'
url = f'https://api.rss2json.com/v1/api.json?rss_url=https://medium.com/feed/@{username}'

req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
        items = data.get('items', [])
        print(f'RSS2JSON returned {len(items)} items')
        for item in items[:15]:
            title = item.get('title', 'N/A')
            link = item.get('link', '')
            slug = link.split('/')[-1].split('?')[0] if link else 'N/A'
            print(f"  - [{slug}] {title[:50]}")
except Exception as e:
    print('Error:', e)