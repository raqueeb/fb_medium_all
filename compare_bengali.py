# Clean one-by-one comparison: FB Bengali text vs MD Bengali text
# Only compare posts from the SAME date
import sqlite3
import re
from difflib import SequenceMatcher

def fix_encoding(text):
    """Fix double-encoded Bengali text from Facebook."""
    if not text:
        return ""
    try:
        return text.encode('latin-1').decode('utf-8')
    except:
        return text

def clean_text(text):
    """Remove English and keep only Bengali text."""
    if not text:
        return ""
    # Remove URLs
    text = re.sub(r'http\S+', '', text)
    # Keep only Bengali characters and punctuation
    bengali_only = re.sub(r'[^\u0980-\u09FF\u2000-\u206F\s,।?!]', ' ', text)
    # Normalize whitespace
    bengali_only = ' '.join(bengali_only.split())
    return bengali_only.strip()

bengali = re.compile(r'[\u0980-\u09FF]')

fb = sqlite3.connect('fb_posts.db')
md = sqlite3.connect('medium_posts.db')

matches = []

# Get all Medium posts with Bengali content
mc = md.cursor()
mc.execute("SELECT id, title, body, date_published FROM medium_posts")
medium_posts = mc.fetchall()

print(f"Found {len(medium_posts)} Medium posts")

for md_post in medium_posts:
    md_id, md_title, md_body, md_date = md_post
    
    # Extract date from Medium post
    if not md_date or len(md_date) < 10:
        continue
    md_date_only = md_date[:10]  # YYYY-MM-DD
    
    # Get Bengali text from Medium post
    md_full = f"{md_title or ''} {md_body or ''}".strip()
    md_bengali = clean_text(md_full)
    
    if not md_bengali or len(md_bengali) < 20:
        continue
    
    # Find FB posts from the SAME date
    fc = fb.cursor()
    fc.execute("""
        SELECT id, date, content 
        FROM fb_text_posts 
        WHERE date LIKE ? 
        AND content IS NOT NULL
    """, (f"{md_date_only}%",))
    fb_posts_on_date = fc.fetchall()
    
    if not fb_posts_on_date:
        continue
    
    best_match = None
    best_sim = 0
    
    for fb_post in fb_posts_on_date:
        fb_id, fb_date, fb_content = fb_post
        
        # Fix encoding
        fb_text = fix_encoding(fb_content or "")
        
        # Skip if no Bengali content
        if not bengali.search(fb_text):
            continue
        
        # Clean to Bengali only
        fb_bengali = clean_text(fb_text)
        if not fb_bengali or len(fb_bengali) < 20:
            continue
        
        # Calculate similarity on Bengali text only
        sim = SequenceMatcher(None, fb_bengali, md_bengali).ratio()
        
        if sim > best_sim:
            best_sim = sim
            best_match = {
                'fb_id': fb_id,
                'fb_date': fb_date,
                'fb_text': fb_text[:100],
                'md_text': md_full[:100]
            }
    
    if best_match and best_sim >= 0.70:  # 70% threshold for high confidence
        matches.append({
            'fb_id': best_match['fb_id'],
            'fb_date': best_match['fb_date'],
            'md_id': md_id,
            'md_date': md_date_only,
            'similarity': best_sim,
            'fb_text': best_match['fb_text'],
            'md_title': md_title[:50] if md_title else "(empty)"
        })
        print(f"✓ MATCH: FB {best_match['fb_id']} ({best_match['fb_date'][:10]}) ↔ MD {md_id} ({md_date_only}) | {best_sim:.1%}")

fb.close()
md.close()

print("\n" + "=" * 60)
print(f"RESULTS: {len(matches)} matches found (≥70% similarity)")
print("=" * 60)

for m in sorted(matches, key=lambda x: x['similarity'], reverse=True):
    print(f"  FB {m['fb_id']} ↔ MD {m['md_id']}: {m['similarity']:.1%} | {m['md_title']}")