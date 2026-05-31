"""
Standalone script to fetch Medium post statistics via RSS.
Usage: python medium_stats.py @username
"""

import sys
import urllib.request
import xml.etree.ElementTree as ET
import re
from collections import Counter

def fetch_medium_rss(username):
    """Fetch Medium posts via RSS feed."""
    username_clean = username.replace("@", "")
    url = f"https://medium.com/feed/@{username_clean}"
    
    print(f"📡 Fetching RSS feed for @{username_clean}...")
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            content = response.read().decode('utf-8')
        
        root = ET.fromstring(content)
        
        articles = []
        for item in root.findall('.//item'):
            title = item.find('title').text if item.find('title') is not None else ""
            
            # Find content:encoded
            content_encoded = None
            for child in item:
                if 'encoded' in child.tag.lower():
                    content_encoded = child.text
                    break
            
            # Get publication date
            pub_date = None
            pub_elem = item.find('pubDate')
            if pub_elem is not None:
                pub_date = pub_elem.text
            
            articles.append({
                'title': title,
                'content': content_encoded or "",
                'pub_date': pub_date
            })
        
        return articles
        
    except Exception as e:
        print(f"❌ Error fetching RSS: {e}")
        return []

def clean_html(html):
    """Remove HTML tags from content."""
    if not html:
        return ""
    return re.sub(r'<[^>]+>', '', html)

def analyze_posts(articles):
    """Analyze Medium posts and return statistics."""
    if not articles:
        return None
    
    stats = {
        'total_posts': len(articles),
        'total_words': 0,
        'total_chars': 0,
        'avg_word_count': 0,
        'avg_char_count': 0,
        'longest_post': None,
        'shortest_post': None,
        'longest_title': None,
        'yearly_counts': Counter(),
        'monthly_counts': Counter(),
    }
    
    word_counts = []
    
    for article in articles:
        content = clean_html(article['content'])
        words = len(content.split())
        chars = len(content)
        
        word_counts.append(words)
        
        stats['total_words'] += words
        stats['total_chars'] += chars
        
        # Track longest/shortest
        if stats['longest_post'] is None or words > stats['longest_post'][1]:
            stats['longest_post'] = (article['title'], words)
        
        if stats['shortest_post'] is None or words < stats['shortest_post'][1]:
            stats['shortest_post'] = (article['title'], words)
        
        # Track longest title
        if stats['longest_title'] is None or len(article['title']) > len(stats['longest_title'][0]):
            stats['longest_title'] = (article['title'], len(article['title']))
        
        # Parse dates
        if article['pub_date']:
            try:
                # Format: "Mon, 01 Jan 2024 12:00:00 GMT"
                parts = article['pub_date'].split()
                if len(parts) >= 4:
                    year = parts[3]
                    month = parts[2]
                    stats['yearly_counts'][year] += 1
                    stats['monthly_counts'][f"{year}-{month}"] += 1
            except:
                pass
    
    # Calculate averages
    if word_counts:
        stats['avg_word_count'] = sum(word_counts) // len(word_counts)
        stats['avg_char_count'] = stats['total_chars'] // len(articles)
    
    return stats

def print_stats(stats, username):
    """Print formatted statistics."""
    print("\n" + "=" * 60)
    print(f"📊 MEDIUM STATISTICS FOR @{username}")
    print("=" * 60)
    
    print(f"\n📝 POST COUNTS")
    print(f"   Total posts:       {stats['total_posts']}")
    
    print(f"\n📏 WORD COUNTS")
    print(f"   Total words:        {stats['total_words']:,}")
    print(f"   Average words:      {stats['avg_word_count']:,}")
    print(f"   Total characters:   {stats['total_chars']:,}")
    print(f"   Average chars:      {stats['avg_char_count']:,}")
    
    print(f"\n📋 POST DETAILS")
    print(f"   Longest post:       {stats['longest_post'][0][:50]}... ({stats['longest_post'][1]} words)")
    print(f"   Shortest post:      {stats['shortest_post'][0][:50]}... ({stats['shortest_post'][1]} words)")
    print(f"   Longest title:      {stats['longest_title'][0][:60]} ({stats['longest_title'][1]} chars)")
    
    print(f"\n📅 POSTS BY YEAR")
    for year, count in sorted(stats['yearly_counts'].items()):
        print(f"   {year}:              {count} posts")
    
    print(f"\n📅 POSTS BY MONTH (last 6 months)")
    for month, count in sorted(stats['monthly_counts'].items())[-6:]:
        print(f"   {month}:             {count} posts")
    
    print("\n" + "=" * 60)

def main():
    # Default username if none provided
    default_username = "raqueeb"
    
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        username = default_username
        print(f"ℹ️ No username provided. Using default: @{username}")
        print(f"   Usage: python medium_stats.py @username\n")
    
    # Fetch articles
    articles = fetch_medium_rss(username)
    
    if not articles:
        print("❌ No articles found or error occurred.")
        sys.exit(1)
    
    # Analyze and print
    stats = analyze_posts(articles)
    print_stats(stats, username.replace("@", ""))
    
    # Also print raw count for easy access
    print(f"\n💡 QUICK ACCESS:")
    print(f"   Total posts: {stats['total_posts']}")
    print(f"   Average words per post: {stats['avg_word_count']}")

if __name__ == "__main__":
    main()