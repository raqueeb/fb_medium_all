import sqlite3
import difflib
from datetime import datetime, timedelta

fb_conn = sqlite3.connect('fb_posts.db')
fb_c = fb_conn.cursor()

md_conn = sqlite3.connect('medium_posts.db')
md_c = md_conn.cursor()

# Get Medium posts from 2014 onwards
md_c.execute("SELECT id, title, body, date_published FROM medium_posts WHERE date_published >= '2014-01-01' LIMIT 5")
md_samples = md_c.fetchall()

print("Manual search for similar FB posts:\n")
for md in md_samples:
    md_id, md_title, md_body, md_date = md
    md_text = f"{md_title or ''} {md_body or ''}".strip()
    md_date_fmt = md_date[:10] if md_date else "N/A"
    
    print(f"Medium post: {md_date_fmt} - {md_title[:50] if md_title else 'EMPTY'}...")
    print(f"  Content preview: {md_text[:80]}...")
    print()
    
    # Search FB posts around same date (±7 days)
    if md_date:
        search_date = datetime.strptime(md_date[:10], "%Y-%m-%d")
        date_lower = (search_date - timedelta(days=7)).strftime("%Y-%m-%d")
        date_upper = (search_date + timedelta(days=7)).strftime("%Y-%m-%d")
        
        fb_c.execute("""
            SELECT content, date FROM fb_text_posts 
            WHERE date >= ? AND date <= ? AND content IS NOT NULL
            LIMIT 5
        """, (f"{date_lower}%", f"{date_upper}%"))
        
        fb_nearby = fb_c.fetchall()
        if fb_nearby:
            print(f"  FB posts within ±7 days:")
            for fb in fb_nearby:
                fb_text = fb[0] or ""
                sim = difflib.SequenceMatcher(None, md_text.lower(), fb_text.lower()).ratio()
                print(f"    {fb[1][:10]}: similarity={sim:.1%}")
                if sim > 0.3:
                    print(f"    MATCH! ({sim:.1%})")
        else:
            print(f"  No FB posts found in date range")
    print("-" * 60)

fb_conn.close()
md_conn.close()