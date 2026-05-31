import sqlite3
conn = sqlite3.connect('fb_posts.db')
c = conn.cursor()
c.execute("SELECT id, date, content FROM fb_text_posts WHERE date LIKE '2014-09-06%'")
print("FB posts from 2014-09-06:")
for r in c.fetchall():
    print(f"ID {r[0]}: {r[1]}")
    print(f"Content: {r[2][:300] if r[2] else 'EMPTY'}")
    print()
conn.close()