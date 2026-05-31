import { sql } from 'drizzle-orm';
import { text, integer, sqliteTable } from 'drizzle-orm/sqlite-core';

// Posts table - stores all Facebook posts
export const posts = sqliteTable('posts', {
  id: integer('id').primaryKey(),
  content: text('content').notNull(),
  date: text('date').notNull(),
  category: text('category'),
  wordCount: integer('word_count'),
  createdAt: text('created_at').default(sql`(datetime('now'))`),
});

// Posted table - tracks which posts have been marked as posted
export const posted = sqliteTable('posted', {
  id: integer('id').primaryKey(),
  postId: integer('post_id').notNull(),
  markedAt: text('marked_at').default(sql`(datetime('now'))`),
  githubIssueUrl: text('github_issue_url'),
  notes: text('notes'),
});

// Indexes for better query performance
export const postsCategoryIndex = sqliteTable('posts_category_index', {
  id: integer('id').primaryKey(),
  category: text('category').notNull(),
});

// Schema type exports for use in application code
export type Post = typeof posts.$inferSelect;
export type NewPost = typeof posts.$inferInsert;
export type Posted = typeof posted.$inferSelect;
export type NewPosted = typeof posted.$inferInsert;
