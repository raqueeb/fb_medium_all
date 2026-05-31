import sqlite3

try:
    conn = sqlite3.connect('comparison_bengali.db')
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = c.fetchall()
    print(f'Existing tables: {tables}')
    conn.close()
except Exception as e:
    print(f'No existing comparison database: {e}')