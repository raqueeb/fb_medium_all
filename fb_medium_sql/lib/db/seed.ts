import { db } from './index';
import { posts, posted } from './schema';

async function seed() {
  console.log('Seeding database...');

  // Load posts from the JSON files in the parent directory
  const fs = await import('fs');
  const path = await import('path');

  const postsDir = path.join(process.cwd(), '..', 'fb_to_medium_ghpages');
  const jsonFiles = fs.readdirSync(postsDir)
    .filter(f => f.startsWith('posts_') && f.endsWith('.json'))
    .sort();

  let totalPosts = 0;

  for (const file of jsonFiles) {
    const filePath = path.join(postsDir, file);
    const content = fs.readFileSync(filePath, 'utf-8');
    const postsData = JSON.parse(content);

    for (const post of postsData) {
      await db.insert(posts).values({
        id: post.id,
        content: post.content || '',
        date: post.date || '',
        category: post.category || null,
        wordCount: post.word_count || null,
      });
      totalPosts++;
    }
    console.log(`Loaded ${postsData.length} posts from ${file}`);
  }

  console.log(`Total posts loaded: ${totalPosts}`);
  console.log('Seeding complete!');
}

seed().catch(console.error);
