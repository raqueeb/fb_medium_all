import sqlite3
import json

# Check fb_posts.db
print("=== fb_posts.db ===")
conn = sqlite3.connect('fb_posts.db')
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print("Tables:", tables)
for t in tables:
    cursor = conn.execute(f"PRAGMA table_info({t})")
    cols = [(r[1], r[2]) for r in cursor.fetchall()]
    print(f"  {t}: {cols}")
    if t == 'fb_text_posts':
        count = conn.execute("SELECT COUNT(*) FROM fb_text_posts").fetchone()[0]
        print(f"    Rows: {count}")
conn.close()

# Check comparison_bengali.db
print("\n=== comparison_bengali.db ===")
conn = sqlite3.connect('comparison_bengali.db')
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print("Tables:", tables)
for t in tables:
    cursor = conn.execute(f"PRAGMA table_info({t})")
    cols = [(r[1], r[2]) for r in cursor.fetchall()]
    print(f"  {t}: {cols}")
    count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"    Rows: {count}")
conn.close()