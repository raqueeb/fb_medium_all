import sqlite3

fb_conn = sqlite3.connect('fb_posts.db')
c = fb_conn.cursor()
c.execute("SELECT COUNT(*) FROM fb_text_posts WHERE date >= '2014-01-01'")
print('FB posts from 2014 onwards:', c.fetchone()[0])
c.execute("SELECT MIN(date), MAX(date) FROM fb_text_posts")
print('FB date range:', c.fetchall())
fb_conn.close()

md_conn = sqlite3.connect('medium_posts.db')
c2 = md_conn.cursor()
c2.execute("SELECT COUNT(*) FROM medium_posts")
print('Total Medium posts:', c2.fetchone()[0])
c2.execute("SELECT MIN(date_published), MAX(date_published) FROM medium_posts")
print('Medium date range:', c2.fetchall())

# Check FB posts around Medium dates
c2.execute("SELECT date_published FROM medium_posts ORDER BY date_published")
md_dates = [r[0][:10] for r in c2.fetchall()]
md_conn.close()

fb_conn = sqlite3.connect('fb_posts.db')
c = fb_conn.cursor()
print('\nChecking FB posts near Medium dates:')
for md_date in md_dates[:5]:
    c.execute("SELECT content, date FROM fb_text_posts WHERE date LIKE ? LIMIT 1", (f'{md_date[:7]}%',))
    matches = c.fetchall()
    if matches:
        print(f'  {md_date}: Found FB post - {matches[0][1][:10]}')
    else:
        print(f'  {md_date}: No FB post')
fb_conn.close()

# Check FB content types (English vs Bengali)
c2.execute("SELECT id, title, body FROM medium_posts WHERE title LIKE '%া%' OR title LIKE '%ি%' OR title LIKE '%ু%' LIMIT 3")
bengali_titles = c2.fetchall()
print('\nBengali title samples:')
for t in bengali_titles:
    print(f'  {t[1][:50] if t[1] else "EMPTY"}')
    
# Check a potential match by looking at FB posts around 2014
conn = sqlite3.connect('fb_posts.db')
c = conn.cursor()
c.execute("SELECT content, date FROM fb_text_posts WHERE date >= '2014-09-01' AND date <= '2014-09-30' LIMIT 3")
print('\nFB posts from Sept 2014:')
for p in c.fetchall():
    print(f'  {p[1][:10]}: {p[0][:50] if p[0] else "EMPTY"}...')
conn.close()
conn2.close()