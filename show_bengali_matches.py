import sqlite3, re

def fix_encoding(text):
    if not text: return ''
    try:
        return text.encode('latin-1').decode('utf-8')
    except:
        return text

conn = sqlite3.connect('comparison.db')
c = conn.cursor()
c.execute('SELECT fb_id, md_id, similarity, fb_date, md_date FROM matched_posts ORDER BY similarity DESC')
bengali_pattern = re.compile(r'[\u0980-\u09FF]')

fb_conn = sqlite3.connect('fb_posts.db')
md_conn = sqlite3.connect('medium_posts.db')

print('Matches with Bengali content:')
count = 0
for row in c.fetchall():
    fb_id, md_id, sim, fb_date, md_date = row
    
    fc = fb_conn.cursor()
    fc.execute('SELECT content FROM fb_text_posts WHERE id = ?', (fb_id,))
    fb_row = fc.fetchone()
    fb_content = fix_encoding(fb_row[0]) if fb_row else ''
    
    mc = md_conn.cursor()
    mc.execute('SELECT title, body FROM medium_posts WHERE id = ?', (md_id,))
    md_row = mc.fetchone()
    md_title = md_row[0] if md_row else ''
    md_body = md_row[1] if md_row else ''
    
    if bengali_pattern.search(fb_content) or bengali_pattern.search(md_title + md_body):
        count += 1
        print(f'  FB {fb_id} ({fb_date[:10]}) -> MD {md_id} ({md_date[:10]}): {sim:.1%}')
        print(f'    FB: {fb_content[:50]}')
        print(f'    MD: {md_title[:50]}')

print(f'\nTotal Bengali matches: {count}')

fb_conn.close()
md_conn.close()