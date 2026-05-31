from curl_cffi import requests
import re
import json

url = 'https://medium.com/@raqueeb'
response = requests.get(url, impersonate='chrome')
html = response.text

# Find all post slugs
posts = re.findall(r'/@raqueeb/([a-z0-9-]{12,})', html)
unique_posts = list(set(posts))
print(f'Found {len(unique_posts)} unique posts')

# Look for window.__APOLLO_STATE__
apollo = re.search(r'window\.__APOLLO_STATE__\s*=\s*({.*?})\s*;', html, re.DOTALL)
if apollo:
    print('Apollo state found!')
    try:
        data = json.loads(apollo.group(1))
        if 'references' in data:
            refs = data['references']
            if 'Post' in refs:
                posts_data = refs['Post']
                print(f'Posts in Apollo: {len(posts_data)}')
                for pid, post in list(posts_data.items())[:3]:
                    print(f"  - {post.get('title', 'no title')} ({post.get('createdAt', 'no date')})")
    except Exception as e:
        print(f'Parse error: {e}')

print('\nFirst 10 posts from HTML:')
for slug in unique_posts[:10]:
    print(f'  - {slug}')