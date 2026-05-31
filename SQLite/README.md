# SQLite Database Files

This folder contains the SQLite database files used by various parts of the project.

## Files

| File | Size | Description |
|------|------|-------------|
| `fb_posts.db` | ~10.3 MB | Main Facebook posts database with full post content |
| `medium_posts.db` | ~1.5 MB | Medium posts scraped from RSS/API |
| `comparison.db` | ~10.1 MB | Comparison results between FB and Medium posts |
| `comparison_bengali.db` | ~8.2 MB | Bengali-specific comparison results |
| `social_posts.db` | 12 KB | Legacy simple posts database |
| `social_posts_fb_app.db` | 12 KB | Copy from fb_medium_app folder |

## Usage

To use any of these databases with the Streamlit app:

```bash
cd fb_medium_app
streamlit run app.py
```

The app will automatically detect and use these database files.

## Schema

### fb_posts.db

```sql
CREATE TABLE posts (
    id INTEGER PRIMARY KEY,
    post_id TEXT UNIQUE,
    text TEXT,
    created_at TIMESTAMP,
    category TEXT,
    language TEXT,
    posted BOOLEAN DEFAULT 0,
    posted_at TIMESTAMP,
    medium_url TEXT
);
```

### medium_posts.db

```sql
CREATE TABLE medium_posts (
    id INTEGER PRIMARY KEY,
    post_id TEXT UNIQUE,
    title TEXT,
    content TEXT,
    published_at TIMESTAMP,
    url TEXT
);
```

## Creating from Scratch

If you need to recreate these databases:

```bash
# Parse Facebook export
python fb_med.py --path your_facebook_activity/posts/your_posts.json

# Scrape Medium posts
python scrape_medium.py

# Compare posts
python compare_posts.py
```

## Backup

These files are tracked in Git for easy cloning and setup. To backup manually:

```bash
sqlite3 fb_posts.db ".backup fb_posts_backup.db"
```