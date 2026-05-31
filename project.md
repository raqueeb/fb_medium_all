# FB → Medium Copier Project

**Last Updated:** May 29, 2026  
**Repository:** github.com/aiwithr/fb_medium

---

## Overview

A tool to sync Facebook posts to Medium with validation. Currently deployed as static HTML/JS on GitHub Pages (free hosting).

---

## Current Deployment

**Live URL:** https://aiwithr.github.io/fb_medium/

### Architecture
- SQLite → 21 JSON chunks (~8MB, 6,287 posts)
- GitHub Pages for hosting
- GitHub Issues for tracking posted posts
- localStorage for browser-side backup

---

## Project Structure

```
fb_medium/
├── fb_to_medium_ghpages/     # GitHub Pages (CURRENT)
│   ├── index.html, styles.css, app.js
│   └── posts_1.json to posts_21.json
├── fb_medium_app/            # Legacy Streamlit (deprecated)
├── fb_med.py                 # Facebook parser
└── fb_posts/                 # SQLite database
```

---

## Key Files

| File | Purpose |
|------|---------|
| `fb_med.py` | Parse Facebook JSON export |
| `app.js` | GitHub Pages app logic |
| `export_posts.py` | SQLite → JSON chunks |
| `medium_stats.py` | Statistics |

---

## Commands

```bash
# Local testing
cd c:\Downloads\fb_medium\fb_to_medium_ghpages
python -m http.server 8080

# Push to GitHub
cd c:\Downloads\fb_medium\fb_to_medium_ghpages
git add . && git commit -m "msg" && git push
```

---

## Bug Fixes

| Commit | Fix |
|--------|-----|
| 9e97fd1 | Fixed empty state hiding |
| eb563d9 | Added .nojekyll |
| b32ce7c | Accessibility improvements |

---

## Safety Features

- Posts NEVER disappear without explicit action
- Confirmation dialog before GitHub Issue
- Manual refresh required to hide posts
- Can reopen GitHub Issue to undo

---

## Statistics

| Metric | Value |
|--------|-------|
| Total Posts | 6,287 |
| JSON Chunks | 21 |
| Size | ~8.05 MB |
| Cost | $0 (free) |
