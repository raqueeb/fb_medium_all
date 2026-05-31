import sqlite3
conn = sqlite3.connect('comparison.db')
c = conn.cursor()
c.execute('SELECT fb_id, md_id, similarity, fb_content, md_title FROM matched_posts ORDER BY similarity DESC LIMIT 10')
print('Top 10 matches by similarity:')
for row in c.fetchall():
    fb_id, md_id, sim, fb_content, md_title = row
    fb_preview = fb_content[:60] if fb_content else "(empty)"
    md_preview = md_title[:60] if md_title else "(empty)"
    print(f'  FB {fb_id} -> MD {md_id}: {sim:.1%}')
    print(f'    FB: {fb_preview}')
    print(f'    MD: {md_preview}')
    print()