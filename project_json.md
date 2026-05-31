# Project: Facebook → Medium Copier (Static JSON + GitHub Pages)

**Live URL:** https://aiwithr.github.io/fb_medium/  
**Last Updated:** May 28, 2026

---

## Overview

A completely free, serverless web app to browse Facebook posts and copy to Medium. Pure HTML/CSS/JS deployed on GitHub Pages.

**No Python required. No server needed. 100% Free.**

---

## Architecture

```
fb_posts.db → export_posts.py → posts_1.json to posts_21.json → GitHub Pages → User Browser
```

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | HTML/CSS/JS | Pure web app, no server |
| **Data** | JSON files | Store in GitHub repo |
| **Hosting** | GitHub Pages | Free static hosting |
| **Automation** | GitHub Actions | Auto-update posted IDs |
| **Sync** | GitHub Issues | Track when posts are marked |

---

## Key Functions (app.js)

| Function | Purpose |
|----------|---------|
| `loadPosts()` | Fetch all 21 JSON chunks |
| `selectPost(id)` | Show post preview |
| `copyPost()` | Copy to clipboard |
| `markPosted()` | GitHub Issue workflow |

---

## "Mark Posted" Workflow

1. User clicks "Mark Posted" → Confirmation modal
2. User confirms → GitHub Issue opens (post still visible)
3. User closes issue → GitHub Action updates `posted_ids.json`
4. User refreshes → Post disappears

### GitHub Actions Workflow

| Step | Action |
|------|--------|
| 1 | User clicks "Mark Posted" → Confirmation dialog |
| 2 | User confirms → GitHub Issue opens |
| 3 | User commits in GitHub → closes Issue |
| 4 | GitHub Actions detects closed issue, extracts post ID |
| 5 | GitHub Actions appends ID to `posted_ids.json` |
| 6 | User refreshes app → post disappears |

---

## Statistics

| Metric | Value |
|--------|-------|
| Total Posts | 6,287 |
| JSON Chunks | 21 |
| Size | ~8.05 MB |
| Cost | $0 |

---

## Project Structure

```
fb_medium/
├── index.html              # Main application
├── styles.css              # Styling
├── app.js                  # Application logic
├── posts_1.json to posts_21.json  # Facebook posts data (chunked)
├── posted_ids.json         # IDs of posts marked as posted
├── README.md               # Documentation
└── .github/workflows/
    └── track_posts.yml     # GitHub Actions for automation
```

---

## Safety Features

| Guarantee | Description |
|-----------|-------------|
| Posts remain visible after browser close | Yes |
| Posts remain visible if GitHub is down | Yes |
| Posts ONLY disappear after "Mark Posted" opens Issue | Yes |
| Posts ONLY disappear after user REFRESHES app | Yes |
| Posts will NOT disappear on accidental click | Confirmation required |
| Posts will NOT disappear automatically | Manual refresh required |

---

## Recovery Procedures

| Problem | Solution |
|---------|----------|
| Post disappears unexpectedly | Reopen GitHub Issue, edit posted_ids.json |
| posted_ids.json corrupted | Rebuild from Issues or start fresh |
| Lose posts.json | Regenerate from SQLite or restore from GitHub |

---

## Deployment to GitHub Pages

1. Create GitHub repo: `fb_medium`
2. Export: `python scripts/export_posts.py`
3. Push to GitHub
4. Enable GitHub Pages: Settings → Pages → main/(root)
5. Access: `https://YOUR_USERNAME.github.io/fb_medium/`

---

## Cost: $0 Forever

---

## Date

2026-05-28
