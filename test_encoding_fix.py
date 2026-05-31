import sqlite3
import difflib

fb_conn = sqlite3.connect('fb_posts.db')
fb_c = fb_conn.cursor()

md_conn = sqlite3.connect('medium_posts.db')
md_c = md_conn.cursor()

# Get sample Medium post
md_c.execute("SELECT id, title, body, date_published FROM medium_posts WHERE date_published LIKE '2014-09-06%'")
md = md_c.fetchone()
md_text = f"{md[1] or ''} {md[2] or ''}".strip()
print("Medium text (proper Bengali):")
print(md_text[:200])
print()

# Get FB post with garbled encoding
fb_c.execute("SELECT id, content FROM fb_text_posts WHERE id = 2784")
fb = fb_c.fetchone()
fb_garbled = fb[1] or ""

# Try to decode the garbled text
try:
    fb_fixed = fb_garbled.encode('latin-1').decode('utf-8')
    print("FB text (after encoding fix):")
    print(fb_fixed[:200])
except:
    print("Could not fix encoding")
    fb_fixed = fb_garbled

# Calculate similarity
sim_garbled = difflib.SequenceMatcher(None, md_text.lower(), fb_garbled.lower()).ratio()
sim_fixed = difflib.SequenceMatcher(None, md_text.lower(), fb_fixed.lower()).ratio()

print(f"\nSimilarity with garbled FB text: {sim_garbled:.1%}")
print(f"Similarity with fixed FB text: {sim_fixed:.1%}")

fb_conn.close()
md_conn.close()