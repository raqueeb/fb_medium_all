import sqlite3, difflib

def fix_encoding(text):
    if not text: return ''
    try:
        return text.encode('latin-1').decode('utf-8')
    except:
        return text

fb = sqlite3.connect('fb_posts.db')
fc = fb.cursor()
md = sqlite3.connect('medium_posts.db')
mc = md.cursor()

# Check first 5 FB posts content
fc.execute('SELECT id, date, content FROM fb_text_posts LIMIT 5')
print('First 5 FB posts:')
for p in fc.fetchall():
    content = fix_encoding(p[2] or '')
    print(f'  FB {p[0]}: {p[1][:10]} - {content[:80]}')

# Check first 5 MD posts content  
mc.execute('SELECT id, title, body FROM medium_posts LIMIT 5')
print()
print('First 5 Medium posts:')
for p in mc.fetchall():
    print(f'  MD {p[0]}: {p[1] or "(empty)"[:30]} - {(p[2] or "")[:50]}')

# Check date ranges
fc.execute('SELECT MIN(date), MAX(date) FROM fb_text_posts')
print()
print(f'FB date range: {fc.fetchone()}')

mc.execute('SELECT MIN(date_published), MAX(date_published) FROM medium_posts')
print(f'MD date range: {mc.fetchone()}')