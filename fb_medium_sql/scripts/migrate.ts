import { createClient } from '@libsql/client';
import { drizzle } from 'drizzle-orm/libsql';
import { posts, posted } from '../lib/db/schema';
import * as fs from 'fs';
import * as path from 'path';

async function migrate() {
  console.log('Starting migration...');

  // Create Turso client
  const client = createClient({
    url: process.env.TURSO_DATABASE_URL!,
    authToken: process.env.TURSO_AUTH_TOKEN,
  });

  const db = drizzle(client);

  // Create tables
  console.log('Creating tables...');
  
  await client.execute(`
    CREATE TABLE IF NOT EXISTS posts (
      id INTEGER PRIMARY KEY,
      content TEXT NOT NULL,
      date TEXT NOT NULL,
      category TEXT,
      word_count INTEGER,
      created_at TEXT DEFAULT (datetime('now'))
    )
  `);

  await client.execute(`
    CREATE TABLE IF NOT EXISTS posted (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      post_id INTEGER NOT NULL,
      marked_at TEXT DEFAULT (datetime('now')),
      github_issue_url TEXT,
      notes TEXT
    )
  `);

  console.log('Tables created successfully');

  // Load posts from JSON files
  const postsDir = path.join(process.cwd(), '..', 'fb_to_medium_ghpages');
  const jsonFiles = fs.readdirSync(postsDir)
    .filter(f => f.startsWith('posts_') && f.endsWith('.json'))
    .sort();

  console.log(`Found ${jsonFiles.length} JSON files`);

  let totalPosts = 0;

  for (const file of jsonFiles) {
    const filePath = path.join(postsDir, file);
    const content = fs.readFileSync(filePath, 'utf-8');
    const postsData = JSON.parse(content);

    for (const post of postsData) {
      try {
        await db.insert(posts).values({
          id: post.id,
          content: post.content || '',
          date: post.date || '',
          category: post.category || null,
          wordCount: post.word_count || null,
        });
 } catch (error) {
        // Skip duplicates
        if (!String(error).includes('UNIQUE constraint failed')) {
          console.error(`Error inserting post ${post.id}:`, error);
        }
      }
      totalPosts++;
    }
    console.log(`Loaded ${postsData.length} posts from ${file}`);
  }

  console.log(`Total posts inserted: ${totalPosts}`);
  console.log('Migration complete!');

  client.close();
}

migrate().catch(console.error);
