# Compare ALL FB posts with ALL Medium posts - Bengali text only, no URLs, no date restriction
import sqlite3
import re
from difflib import SequenceMatcher

def fix_encoding(text):
    if not text:
        return ""
    try:
        return text.encode('latin-1').decode('utf-8')
    except:
        return text

def clean_bengali_only(text):
    """Extract only Bengali text, remove URLs, English, numbers, punctuation."""
    if not text:
        return ""
    # Remove URLs
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'www\.\S+', '', text)
    # Keep only Bengali characters and minimal punctuation
    bengali = re.compile(r'[\u0980-\u09FF]')
    chars = [c if bengali.match(c) else ' ' for c in text]
    text = ''.join(chars)
    # Normalize whitespace
    text = ' '.join(text.split())
    return text.strip()

bengali_pattern = re.compile(r'[\u0980-\u09FF]')

fb = sqlite3.connect('fb_posts.db')
md = sqlite3.connect('medium_posts.db')

# Get ALL Medium posts with Bengali
print("Loading Medium posts...")
mc = md.cursor()
mc.execute("SELECT id, title, body, date_published FROM medium_posts")
medium_posts = mc.fetchall()

# Get ALL FB posts with Bengali
print("Loading FB posts...")
fc = fb.cursor()
fc.execute("SELECT id, date, content FROM fb_text_posts WHERE content IS NOT NULL")
all_fb = fc.fetchall()

print(f"Medium posts: {len(medium_posts)}")
print(f"FB posts: {len(all_fb)}")

# Pre-process: Build list of FB posts with Bengali content
print("\nPre-processing FB posts (extracting Bengali text)...")
fb_bengali_posts = []
for fb_id, fb_date, fb_content in all_fb:
    fb_text = fix_encoding(fb_content or "")
    fb_clean = clean_bengali_only(fb_text)
    if fb_clean and len(fb_clean) >= 20:
        fb_bengali_posts.append((fb_id, fb_date, fb_text, fb_clean))

print(f"FB posts with Bengali: {len(fb_bengali_posts)}")

# For each Medium post, find the BEST matching FB post
print("\n" + "=" * 60)
print("Finding best match for each Medium post...")
print("=" * 60)

all_matches = []

for md_id, md_title, md_body, md_date in medium_posts:
    md_full = f"{md_title or ''} {md_body or ''}".strip()
    md_clean = clean_bengali_only(md_full)
    
    if not md_clean or len(md_clean) < 20:
        continue
    
    best_fb_id = None
    best_fb_date = None
    best_sim = 0
    best_fb_text = None
    
    # Compare with ALL FB posts (no date restriction!)
    for fb_id, fb_date, fb_text, fb_clean in fb_bengali_posts:
        if len(fb_clean) < 20 or len(md_clean) < 20:
            continue
        
        sim = SequenceMatcher(None, fb_clean, md_clean).ratio()
        
        if sim > best_sim:
            best_sim = sim
            best_fb_id = fb_id
            best_fb_date = fb_date
            best_fb_text = fb_text
    
    if best_fb_id and best_sim >= 0.50:  # 50% threshold
        all_matches.append({
            'fb_id': best_fb_id,
            'fb_date': best_fb_date,
            'md_id': md_id,
            'md_title': md_title,
            'md_date': md_date[:10] if md_date else None,
            'similarity': best_sim,
            'fb_text': best_fb_text[:100],
            'md_text': md_full[:100]
        })
        print(f"✓ MD {md_id}: '{md_title[:40]}' ↔ FB {best_fb_id} ({best_fb_date[:10]}) | {best_sim:.1%}")

print("\n" + "=" * 60)
print(f"RESULTS: {len(all_matches)} matches found")
print("=" * 60)

# Group by similarity
exact = [m for m in all_matches if m['similarity'] >= 0.95]
high = [m for m in all_matches if 0.80 <= m['similarity'] < 0.95]
good = [m for m in all_matches if 0.50 <= m['similarity'] < 0.80]
none = len(medium_posts) - len(all_matches)

print(f"Exact match (≥95%): {len(exact)}")
print(f"High similarity (80-94%): {len(high)}")
print(f"Good match (50-79%): {len(good)}")
print(f"No match found: {none}")

print("\n" + "=" * 60)
print("All matches sorted by similarity:")
print("=" * 60)
for m in sorted(all_matches, key=lambda x: x['similarity'], reverse=True)[:30]:
    print(f"  MD {m['md_id']} ↔ FB {m['fb_id']}: {m['similarity']:.1%} | {m['md_title'][:40]}")

fb.close()
md.close()