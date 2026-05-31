"""Check RSS pagination options."""
import urllib.request
import xml.etree.ElementTree as ET

username = 'raqueeb'
url = f'https://medium.com/feed/@{username}'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

with urllib.request.urlopen(req, timeout=15) as resp:
    content = resp.read().decode()

root = ET.fromstring(content)

# Check for atom:link with pagination
print('Atom links:')
for link in root.findall('.//{http://www.w3.org/2005/Atom}link'):
    print(f"  href={link.get('href')}, rel={link.get('rel')}")

# Try fetching with ?source=rss-archive or similar
urls_to_try = [
    f'https://medium.com/feed/@{username}?source=rss',
    f'https://medium.com/feed/@{username}/latest',
    f'https://medium.superfeedr.com/?url=https://medium.com/@{username}/feed',
]

for test_url in urls_to_try:
    req2 = urllib.request.Request(test_url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req2, timeout=10) as resp:
            root2 = ET.fromstring(resp.read())
            items = root2.findall('.//item')
            print(f'{test_url[:60]}: {len(items)} items')
    except Exception as e:
        print(f'{test_url[:60]}: Error - {e}')