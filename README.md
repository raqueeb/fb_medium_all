# FB to Medium Copier - Complete Project Documentation

**Last Updated:** May 31, 2026
**Project Owner:** aiwithr, raqueeb
**Repository:** https://github.com/raqueeb/fb_medium_all

---

## Overview

This repository contains a collection of tools and applications for managing and migrating Facebook posts to Medium. The project has evolved through multiple phases and currently includes three different implementations serving different use cases.

The core problem this project solves: Facebook posts are scattered across many years and difficult to browse through the Facebook interface. This project provides tools to export, organize, browse, and copy Facebook posts for reposting on Medium.

---

## Project Structure

```
fb_medium/
|
|-- fb_to_medium_ghpages/          # GitHub Pages web application (embedded git repo)
|-- fb_medium_app/                 # Legacy Streamlit desktop application
|-- fb_medium_sql/                 # Next.js + Turso serverless version
|
|-- fb_med.py                      # Facebook JSON parser
|-- extract_fb_posts.py           # Facebook data extraction
|-- scrape_medium.py              # Medium content scraper
|-- compare_posts.py              # Post comparison utilities
|
|-- README.md                      # This documentation
|-- .gitignore                    # Git ignore rules
```

---

## Project 1: GitHub Pages Web Application

**Location:** `fb_to_medium_ghpages/`
**Live URL:** https://aiwithr.github.io/fb_medium/
**Repository:** https://github.com/aiwithr/fb_medium

### Description

A static web application hosted on GitHub Pages that allows you to browse Facebook posts and copy their content for reposting on Medium. The entire application runs in the browser with no server-side dependencies.

### Features

| Feature | Description |
|---------|-------------|
| **Clean User Interface** | Modern, responsive design that works on desktop and mobile devices |
| **Category Filtering** | Filter posts by category such as AI/ML, Tech, Tutorial, Books, Thoughts, Bengali, or Short posts |
| **Year Filtering** | Filter posts by specific year to narrow down your search |
| **One-click Copy** | Copy post content to clipboard with a single button click |
| **Safe Marking** | Multi-layer confirmation prevents accidental marking of posts |
| **GitHub Issue Tracking** | Marked posts are tracked via GitHub Issues for audit trail |
| **Free Hosting** | No server costs, no maintenance required |
| **Offline Capable** | Works without internet connection once loaded |

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Frontend | HTML5, CSS3, JavaScript (ES6) | No framework overhead, works everywhere |
| Hosting | GitHub Pages | Free, reliable, automatic SSL |
| Data Storage | JSON files | Human-readable, version-controlled |
| Tracking | GitHub Issues | Free, searchable, integrates with Actions |
| Automation | GitHub Actions | Auto-update posted_ids.json |

### Key Files

| File | Purpose |
|------|---------|
| `index.html` | Main HTML structure with gradient header |
| `styles.css` | All styling with CSS variables and responsive design |
| `app.js` | Core JavaScript logic, filtering, rendering, interactions |
| `posts_1.json` to `posts_21.json` | 21 JSON chunks containing6,287 posts |
| `posted_ids.json` | Array of post IDs marked as posted |
| `scripts/export_posts.py` | Python script to export posts from SQLite |

### Local Setup

```bash
cd fb_to_medium_ghpages
python -m http.server 8080
```

Then open your browser to http://localhost:8080

### Git Workflow

```bash
cd fb_to_medium_ghpages
git add app.js styles.css index.html
git commit -m "Description of changes"
git push
```

The site will automatically update within a few minutes after pushing.

### Safety System

The app implements a multi-layer safety system to prevent accidental loss of post tracking:

1. **Initial Click** - A confirmation dialog appears showing the post details
2. **GitHub Issue Creation** - You must click "Open GitHub Issue" to proceed
3. **Manual Refresh** - The post remains visible until you refresh the page

### Statistics

| Metric | Value |
|--------|-------|
| Total Posts | 6,287 |
| JSON Chunks | 21 |
| Total Size | ~8.05 MB |
| Posts per Chunk | ~300 |

---

## Project 2: Streamlit Desktop Application

**Location:** `fb_medium_app/`
**Type:** Desktop application (requires local Python environment)

### Description

A legacy Streamlit-based desktop application that provides more advanced features including direct Medium API integration, SQLite database storage, and Bengali content analysis.

### Features

| Feature | Description |
|--------|-------------|
| **SQLite Database** | Local storage of all posts with full-text search |
| **Medium API Integration** | Direct posting to Medium via integration tokens |
| **Bengali Dashboard** | Specialized view for Bengali content analysis |
| **Comparison Dashboard** | Compare Facebook posts with Medium posts |
| **Playwright Automation** | Automated browser-based posting |
| **File Upload** | Upload Facebook JSON exports directly |

### Key Files

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit interface |
| `simple_copier.py` | Single-page simplified copier design |
| `database.py` | SQLite database helpers |
| `medium_api.py` | Medium API integration |
| `medium_auto_post.py` | Automated posting workflow |
| `medium_playwright.py` | Playwright-based browser automation |
| `bengali_dashboard.py` | Bengali content analysis dashboard |
| `comparison_dashboard.py` | Post comparison tools |
| `requirements.txt` | Python dependencies |

### Setup

```bash
cd fb_medium_app
pip install -r requirements.txt
streamlit run app.py
```

### Configuration

The app requires:
- Medium Integration Token (entered in the sidebar)
- Facebook JSON export file (uploaded in the sidebar)
- Medium username

---

## Project 3: Next.js + Turso Serverless Version

**Location:** `fb_medium_sql/`
**Type:** Serverless web application
**Deployment:** Vercel + Turso

### Description

A modern serverless implementation using Next.js 14 for the frontend and Turso (libSQL) for the database. This version offers real-time synchronization and API-based access to posts.

### Features

| Feature | Description |
|---------|-------------|
| **API Routes** | RESTful API for post access and management |
| **Real-time Sync** | Database updates reflect immediately |
| **Serverless Architecture** | No server maintenance, scales automatically |
| **Drizzle ORM** | Type-safe database operations |
| **Responsive UI** | Modern gradient design with Tailwind CSS |

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Frontend | Next.js 14, React | Modern React framework |
| Styling | Tailwind CSS | Utility-first CSS |
| Database | Turso (libSQL) | Edge database, SQLite-compatible |
| ORM | Drizzle | Type-safe database operations |
| Deployment | Vercel | Serverless hosting |

### Key Files

| File | Purpose |
|------|---------|
| `app/page.tsx` | Main page component |
| `app/api/posts/route.ts` | GET posts with filtering/pagination |
| `app/api/posts/[id]/route.ts` | Single post operations |
| `app/api/posted/route.ts` | Posted status management |
| `app/api/stats/route.ts` | Statistics endpoint |
| `lib/db/schema.ts` | Drizzle ORM schema |
| `lib/db/index.ts` | Turso client setup |
| `lib/db/seed.ts` | Database seeding from JSON |
| `scripts/migrate.ts` | Database migration script |
| `drizzle.config.ts` | Drizzle configuration |

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/posts` | GET | List posts with filters |
| `/api/posts/[id]` | GET | Get single post |
| `/api/posted` | GET | List posted IDs |
| `/api/posted` | POST | Mark post as posted |
| `/api/posted` | DELETE | Remove from posted |
| `/api/stats` | GET | Get statistics |

### Setup

1. Create Turso database:
```bash
turso db create fb-medium
turso db show fb-medium
```

2. Install dependencies:
```bash
cd fb_medium_sql
npm install
```

3. Copy environment file:
```bash
cp .env.example .env
# Edit .env with your Turso URL and token
```

4. Run migrations:
```bash
npm run db:migrate
npm run db:seed
```

5. Start development server:
```bash
npm run dev
```

### Deployment

The project is configured for Vercel deployment. Connect your GitHub repository to Vercel and it will automatically deploy.

---

## Utility Scripts

### fb_med.py

Facebook JSON export parser with Bengali encoding fixes.

```bash
python fb_med.py --path your_facebook_activity/posts/your_posts.json
```

Features:
- Parses Facebook's JSON export format
- Fixes Mojibake encoding issues
- Stores posts in SQLite database
- Bengali content detection

### extract_fb_posts.py

Extracts posts from Facebook export files.

### scrape_medium.py

Scrapes posts from Medium RSS feed.

### compare_posts.py

Compares Facebook posts with Medium posts to find duplicates.

### Other Utility Scripts

| Script | Purpose |
|--------|---------|
| `check_compare.py` | Verify comparison results |
| `check_fb_encoding.py` | Check Facebook encoding |
| `check_overlap.py` | Find overlapping posts |
| `check_schema.py` | Validate data schemas |
| `debug_similarity.py` | Debug similarity matching |
| `find_any_match.py` | Find matching posts |
| `fix_bengali_encoding.py` | Fix Bengali text encoding |
| `medium_stats.py` | Generate Medium statistics |
| `save_bengali_results.py` | Save Bengali analysis results |
| `show_matches.py` | Display post matches |
| `test_*.py` | Various test scripts |

---

## Architecture Comparison

| Aspect | GitHub Pages | Streamlit App | Next.js + Turso |
|--------|--------------|---------------|-----------------|
| Hosting Cost | Free | Free (local) | $0 (Vercel) + $5/mo (Turso) |
| Database | JSON files | SQLite | Turso (libSQL) |
| Setup Complexity | Low | Medium | Medium |
| Real-time Sync | No | No | Yes |
| Offline Support | Yes | Yes | No |
| API Access | No | No | Yes |
| Scalability | High | N/A | High |

---

## Git Workflow

### Using the Switcher Script

A PowerShell script is provided to switch between GitHub accounts:

```powershell
.\switch.ps1           # Shows current account
.\switch.ps1 aiwithr   # Switch to aiwithr
.\switch.ps1 raqueeb   # Switch to raqueeb
```

### Cloning Repositories

```bash
# Clone with aiwithr (default)
git clone git@github.com:aiwithr/fb_medium.git

# Clone with raqueeb
git clone git@github.com:raqueeb/fb_medium_all.git
```

---

## Cost Analysis

| Component | Cost |
|-----------|------|
| GitHub Repository | $0 |
| GitHub Pages | $0 |
| GitHub Actions | $0 (2000 min/mo free) |
| Vercel | $0 ( hobby tier) |
| Turso | $0 (500MB free) |
| **TOTAL** | **$0** |

---

## Troubleshooting

### GitHub Pages App

**Problem: "Failed to load posts"**
- Verify that posts_N.json files exist in the repository root
- Check GitHub Pages is enabled in repository Settings
- Try a hard refresh (Ctrl+Shift+R)

**Problem: "GitHub Issue not updating"**
- Ensure issue title contains "[POSTED]"
- Check GitHub Actions are enabled
- Verify Actions have write permissions

### Streamlit App

**Problem: "Module not found"**
- Run `pip install -r requirements.txt`
- Ensure Python 3.8+ is installed

**Problem: "Database error"**
- Check write permissions for the database file
- Ensure SQLite is installed

### Next.js + Turso

**Problem: "Database connection failed"**
- Verify TURSO_DATABASE_URL in .env
- Check Turso authentication token
- Ensure database exists

---

## Future Enhancements

1. Add search within posts
2. Export/import posted_ids.json
3. Dark mode toggle
4. Bulk "Mark Posted" selection
5. Progress tracking dashboard
6. Mobile app version
7. Integration with other platforms

---

## License

MIT License - Use freely, no attribution required.

---

## Contact

- **GitHub (aiwithr):** https://github.com/aiwithr
- **GitHub (raqueeb):** https://github.com/raqueeb
- **Live App:** https://aiwithr.github.io/fb_medium/

---

*Last updated: May 31, 2026*
