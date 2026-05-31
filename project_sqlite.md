# Project: Facebook → Medium Copier (SQLite + Streamlit)

**Last Updated:** May 29, 2026

---

## Overview

A lightweight web app to browse Facebook posts and copy content to Medium. Built with Python, SQLite, and Streamlit.

---

## Architecture

```
Facebook Export (JSON) → fb_med.py → SQLite Database → Streamlit App → User pastes to Medium
```

---

## Files

```
fb_medium_app/
├── app.py                    # Main Streamlit app
├── simple_copier.py          # Single-page copier
├── database.py               # SQLite helpers
├── medium_playwright.py      # Playwright automation (optional)
└── requirements.txt          # Dependencies
```

---

## Database Schema

```sql
CREATE TABLE fb_text_posts (
    id INTEGER PRIMARY KEY,
    timestamp INTEGER,
    date TEXT,
    content TEXT,
    post_type TEXT,
    word_count INTEGER,
    has_media INTEGER DEFAULT 0
);

CREATE TABLE matched_bengali_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fb_id INTEGER,
    medium_id TEXT,
    medium_url TEXT,
    similarity REAL,
    status TEXT DEFAULT 'pending'
);
```

---

## Features

| Feature | Description |
|---------|-------------|
| Post Browsing | Paginated display (10/page), filters by date/category/word count |
| Copy to Clipboard | One-click copy, keyboard shortcuts |
| Playwright Automation | Optional browser automation for auto-posting |
| Mark Posted | Updates local tracking |

---

## Setup

```bash
cd fb_medium_app
pip install -r requirements.txt
streamlit run app.py
```

---

## Migration

Moved to JSON + GitHub Pages for free hosting. See `project_json.md` for details.
