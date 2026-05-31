import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { posts, posted } from '@/lib/db/schema';
import { eq, like, and, gte, lte, count, sql } from 'drizzle-orm';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    
    // Parse query parameters
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '50');
    const category = searchParams.get('category');
    const year = searchParams.get('year');
    const search = searchParams.get('search');
    const shortOnly = searchParams.get('shortOnly') === 'true';
    const showPosted = searchParams.get('showPosted') === 'true';

    const offset = (page - 1) * limit;

    // Build where conditions
    const conditions = [];

    if (category && category !== 'all' && category !== 'short') {
      conditions.push(eq(posts.category, category));
    }

    if (shortOnly) {
      conditions.push(sql`${posts.wordCount} < 50`);
    }

    if (year && year !== 'all') {
      conditions.push(like(posts.date, `${year}%`));
    }

    if (search) {
      conditions.push(like(posts.content, `%${search}%`));
    }

    // Get total count
    const totalResult = await db.select({ count: count() }).from(posts);
    const total = totalResult[0]?.count || 0;

    // Get posted count
    const postedResult = await db.select({ count: count() }).from(posted);
    const postedCount = postedResult[0]?.count || 0;

    // Get all posted post IDs for filtering
    const postedPosts = showPosted 
      ? await db.select({ postId: posted.postId }).from(posted)
      : [];
    const postedIds = new Set(postedPosts.map(p => p.postId));

    // Fetch posts
    const allPosts = await db
      .select()
      .from(posts)
      .where(conditions.length > 0 ? and(...conditions) : undefined)
      .orderBy(sql`${posts.date} DESC`)
      .limit(limit)
      .offset(offset);

    // Filter out posted posts if showPosted is false
    const filteredPosts = showPosted 
      ? allPosts 
      : allPosts.filter(p => !postedIds.has(p.id));

    // Add isPosted flag to each post
    const postsWithStatus = filteredPosts.map(p => ({
      ...p,
      isPosted: postedIds.has(p.id),
    }));

    return NextResponse.json({
      posts: postsWithStatus,
      pagination: {
        page,
        limit,
        total,
        postedCount,
        pendingCount: total - postedCount,
        totalPages: Math.ceil(total / limit),
      },
    });
  } catch (error) {
    console.error('Error fetching posts:', error);
    return NextResponse.json(
      { error: 'Failed to fetch posts' },
      { status: 500 }
    );
  }
}
