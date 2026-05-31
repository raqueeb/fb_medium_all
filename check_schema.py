import sqlite3
conn = sqlite3.connect('fb_posts.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", c.fetchall())
c.execute("PRAGMA table_info(fb_text_posts)")
print("fb_text_posts columns:")
for col in c.fetchall():
    print(f"  {col}")