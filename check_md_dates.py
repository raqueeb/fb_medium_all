import sqlite3
md = sqlite3.connect('medium_posts.db')
c = md.cursor()
c.execute('SELECT id, title, date_published FROM medium_posts ORDER BY date_published LIMIT 20')
print('First 20 Medium posts by date:')
for m in c.fetchall():
    title = m[1][:40] if m[1] else "(empty)"
    date = m[2][:10] if m[2] else "NO DATE"
    print(f'  ID {m[0]}: {date} - {title}')

# Check dates
c.execute('SELECT COUNT(*) FROM medium_posts WHERE date_published IS NULL OR date_published = ""')
print(f'\nMedium posts without dates: {c.fetchone()[0]}')
