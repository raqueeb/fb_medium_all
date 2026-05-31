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
    if not text:
        return ""
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'www\.\S+', '', text)
    bengali_chars = []
    for c in text:
        if '\u0980' <= c <= '\u09FF':
            bengali_chars.append(c)
        else:
            bengali_chars.append(' ')
    text = ''.join(bengali_chars)
    text = ' '.join(text.split())
    return text.strip()

fb = sqlite3.connect('fb_posts.db')
md = sqlite3.connect('medium_posts.db')

print("Loading Medium posts...")
mc = md.cursor()
mc.execute("SELECT id, title, body, date_published FROM medium_posts")
medium_posts = mc.fetchall()

print("Loading FB posts...")
fc = fb.cursor()
fc.execute("SELECT id, date, content FROM fb_text_posts WHERE content IS NOT NULL")
all_fb = fc.fetchall()

print(f"Medium posts: {len(medium_posts)}")
print(f"FB posts: {len(all_fb)}")

print("\nPre-processing FB posts...")
fb_bengali_posts = []
for fb_id, fb_date, fb_content in all_fb:
    fb_text = fix_encoding(fb_content or "")
    fb_clean = clean_bengali_only(fb_text)
    if fb_clean and len(fb_clean) >= 20:
        fb_bengali_posts.append((fb_id, fb_date, fb_text, fb_clean))

print(f"FB posts with Bengali: {len(fb_bengali_posts)}")

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
    
    for fb_id, fb_date, fb_text, fb_clean in fb_bengali_posts:
        if len(fb_clean) < 20 or len(md_clean) < 20:
            continue
        sim = SequenceMatcher(None, fb_clean, md_clean).ratio()
        if sim > best_sim:
            best_sim = sim
            best_fb_id = fb_id
            best_fb_date = fb_date
            best_fb_text = fb_text
    
    if best_fb_id and best_sim >= 0.50:
        all_matches.append({
            'fb_id': best_fb_id,
            'fb_date': best_fb_date,
            'md_id': md_id,
            'md_title': md_title,
            'md_date': md_date[:10] if md_date else None,
            'similarity': best_sim,
            'fb_text': best_fb_text,
            'md_text': md_full
        })
        print(f"MD {md_id}: FB {best_fb_id} | {best_sim:.1%} | {md_title[:40]}")

comp_conn = sqlite3.connect('comparison_bengali.db')
comp_c = comp_conn.cursor()

comp_c.execute('DELETE FROM matched_bengali_posts')
comp_c.execute('DELETE FROM unmatched_bengali_posts')

matched_fb_ids = set()

for m in all_matches:
    matched_fb_ids.add(m['fb_id'])
    comp_c.execute('''
        INSERT INTO matched_bengali_posts 
        (fb_id, fb_date, fb_content, md_id, md_title, md_content, md_date, similarity, matched_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, date('now'))
    ''', (m['fb_id'], m['fb_date'], m['fb_text'], m['md_id'], m['md_title'], m['md_text'], m['md_date'], m['similarity']))

md_ids_matched = set(m['md_id'] for m in all_matches)
for md_id, md_title, _, _ in medium_posts:
    if md_id not in md_ids_matched:
        comp_c.execute('INSERT INTO unmatched_bengali_posts (md_id, md_title) VALUES (?, ?)', (md_id, md_title))

comp_conn.commit()
comp_conn.close()

print("\n" + "=" * 60)
print(f"RESULTS: {len(all_matches)} matches saved")
print("=" * 60)

print(f"\nFB posts used for Medium: {len(matched_fb_ids)}")
print(f"FB posts NOT used: {len(all_fb) - len(matched_fb_ids)}")

print("\n" + "=" * 60)
print("FB posts that became Medium posts:")
print("=" * 60)
for m in sorted(all_matches, key=lambda x: x['similarity'], reverse=True):
    print(f"  FB {m['fb_id']} -> MD {m['md_id']} | {m['similarity']:.1%}")

fb.close()
md.close()
