import { NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { posts, posted } from '@/lib/db/schema';
import { count, sql, distinct } from 'drizzle-orm';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    // Get total posts count
    const totalResult = await db.select({ count: count() }).from(posts);
    const total = totalResult[0]?.count || 0;

    // Get posted count
    const postedResult = await db.select({ count: count() }).from(posted);
    const postedCount = postedResult[0]?.count || 0;

    // Get unique categories
    const categoriesResult = await db
      .select({ category: posts.category })
      .from(posts)
      .where(sql`${posts.category} IS NOT NULL`)
      .groupBy(posts.category);

    const categories = categoriesResult.map(r => r.category).filter(Boolean);

    // Get year range
    const yearResult = await db
      .select({
        minYear: sql<string>`MIN(${posts.date})`,
        maxYear: sql<string>`MAX(${posts.date})`,
      })
      .from(posts);

    const years: string[] = [];
    if (yearResult[0]?.minYear) {
      const minYear = parseInt(yearResult[0].minYear.substring(0, 4));
      const maxYear = parseInt(yearResult[0].maxYear.substring(0, 4));
      for (let y = maxYear; y >= minYear; y--) {
        years.push(y.toString());
      }
    }

    return NextResponse.json({
      total,
      postedCount,
      pendingCount: total - postedCount,
      categories,
      years,
    });
  } catch (error) {
    console.error('Error fetching stats:', error);
    return NextResponse.json(
      { error: 'Failed to fetch stats' },
      { status: 500 }
    );
  }
}
