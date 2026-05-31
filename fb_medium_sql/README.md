# FB to Medium Copier - Vercel + Turso Version

## Overview

This is an alternative implementation of the FB to Medium Copier using a modern serverless architecture with Vercel for hosting and Turso for the database. This version provides real-time data synchronization, persistent storage, and better scalability compared to the static JSON + GitHub Pages version.

**Live URL:** https://your-app.vercel.app/
**Repository:** https://github.com/aiwithr/fb_medium_sql

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Vercel                                  │
│  ┌─────────────┐ ┌─────────────┐  ┌─────────────────────────┐ │
│  │ Next.js   │  │   API       │  │   Static Assets         │ │
│  │   App │  │   Routes    │  │   (CSS, JS)             │ │
│  │   (RSC)     │  │   (Edge)    │  │                         │ │
│  └──────┬──────┘  └──────┬──────┘  └─────────────────────────┘ │
└─────────┼────────────────┼──────────────────────────────────────┘
          │                │
          │                │ HTTPS
          │                │
          ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Turso                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    SQLite Database                         │ │
│  │ ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │ │
│  │  │   posts     │  │   posted    │  │   (indexes)         │ │ │
│  │  │   table │  │   table     │  │                     │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                         Edge Locations │
│  (Global replication for low-latency access)                    │
└─────────────────────────────────────────────────────────────────┘
```

## Why Vercel + Turso?

| Aspect | This Architecture | Static JSON + GitHub Pages |
|--------|-------------------|---------------------------|
| Data Storage | Turso SQLite (distributed) | JSON files in GitHub |
| Real-time Sync | Yes, across all devices | No, local storage only |
| Scalability | Auto-scales with Vercel | Limited by GitHub |
| Cold Starts | Minimal with Edge | N/A (static files) |
| Database | Full SQL capabilities | File-based only |
| Cost | Free tier available | Free |
| Setup Complexity | Requires Turso setup | Simple file hosting |

## Features

| Feature | Description |
|---------|-------------|
| **Serverless API** | API routes run on Vercel Edge for fast response times |
| **Persistent Storage** | Turso SQLite database with global edge replication |
| **Real-time Sync** | Posted status syncs across all devices instantly |
| **Filtering** | Filter by category, year, and search terms |
| **Pagination** | Efficient pagination for large datasets |
| **Modern UI** | Clean, responsive design with gradient header |
| **One-click Copy** | Copy post content to clipboard |
| **Mark as Posted** | Track which posts have been published |
| **Undo Support** | Remove posts from posted list if needed |

## Prerequisites

Before setting up this project, you need:

1. **Node.js 18+** - For running the development server
2. **Turso Account** - Free tier available at https://turso.tech
3. **Vercel Account** - Free tier available at https://vercel.com
4. **GitHub Account** - For hosting the repository

## Setup Instructions

### Step 1: Create a Turso Database

1. Go to https://app.turso.tech and sign up
2. Click "New Database"
3. Choose a name (e.g., "fb-medium")
4. Select a region closest to your users
5. Copy the database URL (format: `libsql://your-db-name.turso.io`)
6. Go to Database Settings > Authentication
7. Create an authentication token and copy it

### Step 2: Clone and Setup the Project

```bash
# Clone the repository
git clone https://github.com/aiwithr/fb_medium_sql.git
cd fb_medium_sql

# Install dependencies
npm install

# Copy environment example file
cp .env.example .env.local
```

### Step 3: Configure Environment Variables

Edit `.env.local` with your Turso credentials:

```env
TURSO_DATABASE_URL=libsql://your-database-name.turso.io
TURSO_AUTH_TOKEN=your-auth-token-here
```

### Step 4: Run Migration

```bash
# Push schema to Turso
npm run db:push

# Seed the database with posts from JSON files
npm run db:seed
```

This will:
1. Create the `posts` and `posted` tables in your Turso database
2. Load all posts from the `fb_to_medium_ghpages` folder's JSON files
3. Index the data for efficient querying

### Step 5: Test Locally

```bash
npm run dev
```

Open http://localhost:3000 to see the app running locally.

### Step 6: Deploy to Vercel

#### Option A: Using Vercel CLI

```bash
# Install Vercel CLI globally
npm install -g vercel

# Login to Vercel
vercel login

# Deploy
vercel
```

#### Option B: Using GitHub Integration

1. Push this code to a GitHub repository
2. Go to https://vercel.com and click "New Project"
3. Import your GitHub repository
4. Add environment variables:
   - `TURSO_DATABASE_URL` = your Turso database URL
   - `TURSO_AUTH_TOKEN` = your Turso auth token
5. Click "Deploy"

### Step 7: Configure Vercel Environment Variables

In your Vercel project settings, add the same environment variables:

1. Go to Project Settings > Environment Variables
2. Add `TURSO_DATABASE_URL` with your database URL
3. Add `TURSO_AUTH_TOKEN` with your auth token
4. Redeploy if needed

---

## Project Structure

```
fb_medium_sql/
|
|-- app/
|   |-- api/
|   |   |-- posts/
|   |   |   |-- route.ts          # GET posts with filtering/pagination
|   |   |   |-- [id]/route.ts # GET single post
|   |   |-- posted/
|   |   |   |-- route.ts          # GET/POST/DELETE posted records
|   |   |-- stats/
|   |   |   |-- route.ts          # GET statistics
|   |-- globals.css               # Global styles
|   |-- layout.tsx                # Root layout
|   |-- page.tsx                 # Main page (client component)
|
|-- lib/
|   |-- db/
|   |   |-- index.ts              # Drizzle client setup
|   |   |-- schema.ts             # Database schema definitions
|   |   |-- seed.ts               # Seed script for loading JSON data
|
|-- scripts/
|   |-- migrate.ts                # Migration script
|
|-- .env.example                  # Example environment variables
|-- drizzle.config.ts              # Drizzle ORM configuration
|-- next.config.mjs               # Next.js configuration
|-- package.json                  # Dependencies and scripts
|-- tsconfig.json                 # TypeScript configuration
|-- vercel.json                   # Vercel deployment config
|-- README.md                      # This documentation
```

---

## API Reference

### GET /api/posts

Fetch posts with optional filtering and pagination.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | number | 1 | Page number |
| limit | number | 50 | Posts per page |
| category | string | all | Filter by category |
| year | string | all | Filter by year |
| search | string | | Search in content |
| shortOnly | boolean | false | Show only posts under 50 words |
| showPosted | boolean | false | Include posted posts |

**Response:**
```json
{
  "posts": [
    {
      "id": 1,
      "content": "Post content...",
      "date": "2024-01-15",
      "category": "tech",
      "wordCount": 250,
      "isPosted": false
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 10000,
    "postedCount": 150,
    "pendingCount": 9850,
    "totalPages": 200
  }
}
```

### GET /api/posts/[id]

Fetch a single post by ID.

**Response:**
```json
{
  "post": {
    "id": 1,
    "content": "Post content...",
    "date": "2024-01-15",
    "category": "tech",
    "wordCount": 250
  }
}
```

### GET /api/posted

Fetch all posted records.

**Response:**
```json
{
  "posted": [
    {
      "id": 1,
      "postId": 123,
      "markedAt": "2024-01-20T10:30:00",
      "githubIssueUrl": "https://github.com/...",
      "notes": null
    }
  ]
}
```

### POST /api/posted

Mark a post as posted.

**Request Body:**
```json
{
  "postId": 123,
  "githubIssueUrl": "https://github.com/...",
  "notes": "Optional note"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Post marked as posted"
}
```

### DELETE /api/posted?postId=123

Remove a post from the posted list (undo).

**Response:**
```json
{
  "success": true,
  "message": "Post unmarked successfully"
}
```

### GET /api/stats

Fetch statistics about posts.

**Response:**
```json
{
  "total": 10000,
  "postedCount": 150,
  "pendingCount": 9850,
  "categories": ["tech", "ai_ml", "bengali", ...],
  "years": ["2024", "2023", "2022", ...]
}
```

---

## Database Schema

### posts table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Unique post ID |
| content | TEXT | Post content |
| date | TEXT | Original post date |
| category | TEXT | Category label |
| word_count | INTEGER | Word count |
| created_at | TEXT | Timestamp when imported |

### posted table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment ID |
| post_id | INTEGER | Reference to posts.id |
| marked_at | TEXT | When marked as posted |
| github_issue_url | TEXT | Optional GitHub issue link |
| notes | TEXT | Optional notes |

---

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |
| `npm run db:generate` | Generate Drizzle migrations |
| `npm run db:migrate` | Run Drizzle migrations |
| `npm run db:push` | Push schema to database |
| `npm run db:studio` | Open Drizzle Studio |
| `npm run db:seed` | Seed database from JSON files |

---

## Turso vs SQLite

Turso is a distributed SQLite database that provides:

| Feature | Traditional SQLite | Turso |
|---------|-------------------|-------|
| Hosting | Self-managed | Managed service |
| Replication | None | Multi-region edge |
| Latency | Varies |< 10ms globally |
| Consistency | Single instance | Strong eventual |
| Free Tier | N/A | 9GB storage, 500GB transfer |

### Local Development

For local development without Turso, you can use a local SQLite file:

```env
TURSO_DATABASE_URL=file:local.db
TURSO_AUTH_TOKEN=
```

---

## Troubleshooting

### "Failed to connect to database"

1. Verify your `TURSO_DATABASE_URL` is correct
2. Check that your `TURSO_AUTH_TOKEN` is valid
3. Ensure the database exists in Turso dashboard
4. Check if your IP is blocked (Turso may block some IPs)

### "Failed to fetch posts"

1. Check if the migration ran successfully
2. Verify the `posts` table has data
3. Check Vercel function logs for errors
4. Ensure environment variables are set in Vercel

### "CORS errors"

Next.js API routes allow same-origin requests by default. If you encounter CORS issues:
1. Ensure you're calling from the same domain
2. Check that no browser extensions are blocking requests

### "Pagination not working"

1. Clear browser cache
2. Check network tab for request parameters
3. Verify the API returns correct pagination metadata

---

## Deployment Checklist

Before going live, verify:

- [ ] Turso database created and accessible
- [ ] Environment variables configured in Vercel
- [ ] Migration completed successfully
- [ ] All posts loaded into database
- [ ] App tested locally
- [ ] Vercel deployment successful
- [ ] Custom domain configured (optional)
- [ ] SSL certificate active (automatic with Vercel)

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally with `npm run dev`
5. Submit a pull request

---

## License

MIT License

---

## Questions?

Open an issue at https://github.com/aiwithr/fb_medium_sql/issues

---

*Last updated: May 30, 2026*
