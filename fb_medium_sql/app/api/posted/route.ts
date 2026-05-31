import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { posted } from '@/lib/db/schema';
import { eq, count } from 'drizzle-orm';

export const dynamic = 'force-dynamic';

// GET - Fetch all posted records
export async function GET() {
  try {
    const allPosted = await db
      .select()
      .from(posted)
      .orderBy(posted.markedAt);

    return NextResponse.json({ posted: allPosted });
  } catch (error) {
    console.error('Error fetching posted:', error);
    return NextResponse.json(
      { error: 'Failed to fetch posted records' },
      { status: 500 }
    );
  }
}

// POST - Mark a post as posted
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { postId, githubIssueUrl, notes } = body;

    if (!postId) {
      return NextResponse.json(
        { error: 'postId is required' },
        { status: 400 }
      );
    }

    // Check if already posted
    const existing = await db
      .select()
      .from(posted)
      .where(eq(posted.postId, postId))
      .limit(1);

    if (existing.length > 0) {
      return NextResponse.json(
        { error: 'Post already marked as posted' },
        { status: 409 }
      );
    }

    // Insert new record
    const result = await db.insert(posted).values({
      postId,
      githubIssueUrl: githubIssueUrl || null,
      notes: notes || null,
    });

    return NextResponse.json({ 
      success: true, 
      message: 'Post marked as posted',
      data: result 
    });
  } catch (error) {
    console.error('Error marking post:', error);
    return NextResponse.json(
      { error: 'Failed to mark post as posted' },
      { status: 500 }
    );
  }
}

// DELETE - Remove a post from posted list (undo)
export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const postId = parseInt(searchParams.get('postId') || '0');

    if (!postId) {
      return NextResponse.json(
        { error: 'postId is required' },
        { status: 400 }
      );
    }

    await db
      .delete(posted)
      .where(eq(posted.postId, postId));

    return NextResponse.json({ 
      success: true, 
      message: 'Post unmarked successfully' 
    });
  } catch (error) {
    console.error('Error unmarking post:', error);
    return NextResponse.json(
      { error: 'Failed to unmark post' },
      { status: 500 }
    );
  }
}
