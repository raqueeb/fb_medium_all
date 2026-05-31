import urllib.request, re

# Test what works - RSS is known working
print("Testing RSS feed...")
url = 'https://medium.com/feed/@raqueeb'
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        print(f"RSS Status: {resp.status}")
except Exception as e:
    print(f"RSS Error: {e}")

# Test profile page with full User-Agent
print("\nTesting profile page...")
url = 'https://medium.com/@raqueeb'
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        posts = re.findall(r'/@raqueeb/([a-z0-9-]{12,})', html)
        print(f"Profile Status: {resp.status}")
        print(f"Total slugs found: {len(set(posts))}")
except Exception as e:
    print(f"Profile Error: {e}")