# FB → Medium Copier - Complete Project Documentation

**Last Updated:** May 29, 2026  
**Project Owner:** aiwithr  
**Repository:** github.com/aiwithr/fb_medium

---

## Project Evolution Summary

### Phase 1: Initial Development (2024-2025)
- Built SQLite + Streamlit app for Facebook to Medium post copying
- Created `fb_med.py` parser for Facebook JSON export
- Established database schema with 6,287 posts
- Implemented Bengali content detection and encoding fixes

### Phase 2: GitHub Pages Migration (2026-05-28)
- Transitioned from SQLite + Streamlit to static JSON + GitHub Pages
- Split posts into 21 JSON chunks (~8MB total) for performance
- SSH key configured for aiwithr GitHub account
- Deployed to: https://aiwithr.github.io/fb_medium/

### Phase 3: Bug Fixes & Accessibility (2026-05-29)
- Fixed template literal corruption (`${i}` → `posts_.json`)
- Added ARIA support, keyboard navigation, screen reader labels
- Created `.nojekyll` for GitHub Pages compatibility
- Fixed post preview not showing on selection
- Committed fixes: b32ce7c, 9e97fd1

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      LOCAL WORKFLOW                          │
│                                                             │
│  Facebook Export (JSON)                                     │
│         ↓                                                   │
│  fb_med.py (parser)                                         │
│         ↓                                                   │
│  SQLite Database (fb_posts.db)                              │
│         ↓                                                   │
│  export_posts.py → 21 JSON chunks                           │
│         ↓                                                   │
│  GitHub Repository + Pages                                   │
│         ↓                                                   │
│  User clicks "Copy" → Paste to Medium                       │
│         ↓                                                   │
│  User clicks "Mark Posted" → GitHub Issue → Refresh         │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | HTML/CSS/JS | Static web app |
| **Hosting** | GitHub Pages | Free deployment |
| **Data** | JSON chunks | 6,287 posts |
| **Tracking** | GitHub Issues | Audit trail |
| **Automation** | GitHub Actions | Auto-update |

---

## Project Structure

```
fb_medium/
├── fb_to_medium_ghpages/          # GitHub Pages deployment
│   ├── index.html                 # Main app UI
│   ├── styles.css                  # Styling
│   ├── app.js                     # Core logic
│   ├── .nojekyll                  # GitHub Pages config
│   ├── posts_1.json to posts_21.json  # 21 JSON chunks
│   ├── posted_ids.json            # Posted tracking
│   └── README.md                  # User guide
├── fb_medium_app/                 # Legacy Streamlit app
│   ├── app.py                     # Streamlit interface
│   ├── simple_copier.py           # Single-page design
│   ├── database.py                # SQLite helpers
│   └── medium_api.py             # Medium API
├── fb_posts/                      # SQLite database
├── fb_med.py                      # Facebook parser
└── medium_stats.py               # Statistics
```

---

## Key Files

### fb_med.py
Facebook JSON export parser with Bengali encoding fixes.

```bash
python fb_med.py --path your_facebook_activity/posts/your_posts.json
```

### app.js (GitHub Pages)
Core application logic:
- `loadPosts()` - Fetches all 21 JSON chunks
- `selectPost(id)` - Shows post preview
- `copyPost()` - Copy to clipboard
- `markPosted()` - GitHub Issue workflow
- `filter()` - Category/date filters

### export_posts.py
Converts SQLite to JSON chunks:

```python
# Key functions:
- fix_encoding(text)     # Bengali encoding normalization
- categorize(content)   # Auto-categorize posts
- export_chunks()       # Split into 21 JSON files
```

---

## Safety Features

### Posts NEVER Disappear Without Explicit Action

```
┌─────────────────────────────────────────────────────────────────┐
│                        SAFETY GUARANTEES                         │
│                                                                     │
│  ✅ Posts remain visible after browser close                       │
│  ✅ Posts remain visible after app restart                        │
│  ✅ Posts remain visible if GitHub is down                        │
│  ✅ Posts ONLY disappear after "Mark Posted" → GitHub Issue       │
│  ✅ Posts ONLY disappear after user manually REFRESHES            │
│                                                                     │
│  ❌ Posts will NOT disappear on page refresh                     │
│  ❌ Posts will NOT disappear on browser close                     │
│  ❌ Posts will NOT disappear if automation fails                  │
└─────────────────────────────────────────────────────────────────┘
```

### Multi-Layer Backup System

| Layer | File | Purpose |
|-------|------|---------|
| 1 | posts.json/chunks | Source of truth, never modified |
| 2 | posted_ids.json | Append-only tracking |
| 3 | GitHub Issues | Audit trail, can reopen |
| 4 | localStorage | Browser backup |

---

## Commands

### Run Local Server (Testing)
```bash
cd c:\Downloads\fb_medium\fb_to_medium_ghpages
python -m http.server 8080
```

### Push to GitHub
```bash
cd c:\Downloads\fb_medium\fb_to_medium_ghpages
git add .
git commit -m "Your message"
git push origin main
```

### Export Posts from SQLite
```bash
python scripts/export_posts.py
```

### Stop Local Server
```bash
taskkill /F /IM python.exe
```

---

## GitHub Pages Deployment

### URL
```
https://aiwithr.github.io/fb_medium/
```

### Setup Steps
1. Push files to `git@github.com:aiwithr/fb_medium.git`
2. Enable GitHub Pages: Settings → Pages → Source: main/(root)
3. Add `.nojekyll` file to root
4. Wait 2-3 minutes for deployment

---

## Bug Fixes Log

| Date | Commit | Fix |
|------|--------|-----|
| 2026-05-28 | b32ce7c | Accessibility improvements, keyboard nav |
| 2026-05-28 | eb563d9 | Added .nojekyll for GitHub Pages |
| 2026-05-29 | 9e97fd1 | Fixed empty state hiding on post selection |
| Earlier | - | Fixed `${i}` template literal corruption |

---

## Known Issues & Solutions

### Post Preview Not Showing
**Fixed in commit 9e97fd1**
- Added: `emptyState.style.display = 'none'` in `selectPost()`
- Changed inline button from `onclick` to event listener

### JSON Chunk Loading
- Uses string concatenation: `'posts_' + i + '.json'`
- Template literals were corrupting (fixed)

### Bengali Encoding
- Facebook exports use latin-1, convert to UTF-8
- Special characters: `'` `"` `"` normalized

---

## Recovery Procedures

### If Posts Disappear Unexpectedly
1. Check GitHub Issues for the post ID
2. Reopen the issue to undo marking
3. Or manually edit `posted_ids.json` in GitHub

### If Database Gets Corrupted
```bash
python fb_med.py --path your_facebook_activity/posts/your_posts.json
```

### Reset All Posted Status
Delete/empty `posted_ids.json` in GitHub, commit, refresh.

---

## Statistics

| Metric | Value |
|--------|-------|
| Total Posts | 6,287 |
| JSON Chunks | 21 |
| Total Size | ~8.05 MB |
| Posts per Chunk | ~300 |

---

## Cost Analysis

| Item | Cost |
|------|------|
| GitHub Repository | $0 |
| GitHub Pages | $0 |
| GitHub Actions | $0 (2000 min/mo free) |
| **TOTAL** | **$0** |

---

## Future Enhancements

1. [ ] Add search within posts
2. [ ] Export/import posted_ids.json
3. [ ] Dark mode toggle
4. [ ] Bulk "Mark Posted" selection
5. [ ] Progress tracking dashboard

---

## Contact

- **GitHub:** github.com/aiwithr
- **Live App:** https://aiwithr.github.io/fb_medium/

---

## License

MIT - Use freely, no attribution required.
