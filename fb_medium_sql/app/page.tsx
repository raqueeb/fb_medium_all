'use client';

import { useState, useEffect, useCallback } from 'react';

// Types
interface Post {
  id: number;
  content: string;
  date: string;
  category: string | null;
  wordCount: number | null;
  isPosted: boolean;
}

interface Stats {
  total: number;
  postedCount: number;
  pendingCount: number;
  categories: string[];
  years: string[];
}

interface Pagination {
  page: number;
  limit: number;
  total: number;
  postedCount: number;
  pendingCount: number;
  totalPages: number;
}

// Categories to display
const CATEGORIES = ['all', 'short', 'bengali', 'ai_ml', 'tech', 'tutorial', 'books', 'thoughts'];

export default function Home() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [pagination, setPagination] = useState<Pagination | null>(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<number | null>(null);
  const [activeCategory, setActiveCategory] = useState('all');
  const [activeYear, setActiveYear] = useState('all');
  const [showPosted, setShowPosted] = useState(false);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);

  // Fetch posts
  const fetchPosts = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '50',
        category: activeCategory,
        year: activeYear,
        showPosted: showPosted.toString(),
 });

      if (search) {
        params.set('search', search);
      }

      const res = await fetch(`/api/posts?${params}`);
      const data = await res.json();
 setPosts(data.posts);
      setPagination(data.pagination);
    } catch (error) {
      console.error('Failed to fetch posts:', error);
    } finally {
      setLoading(false);
    }
  }, [page, activeCategory, activeYear, showPosted, search]);

  // Fetch stats
  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch('/api/stats');
      const data = await res.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  }, []);

  useEffect(() => {
    fetchPosts();
 }, [fetchPosts]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  // Copy post content
  const copyPost = async (post: Post) => {
    try {
      await navigator.clipboard.writeText(post.content);
      alert('Copied to clipboard!');
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  // Mark post as posted
  const markPosted = async (postId: number) => {
    if (!confirm('Mark this post as posted?')) return;

    try {
      const res = await fetch('/api/posted', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ postId }),
      });

      if (res.ok) {
        fetchPosts();
        fetchStats();
      }
    } catch (error) {
      console.error('Failed to mark post:', error);
    }
  };

  // Undo mark posted
  const undoMark = async (postId: number) => {
    if (!confirm('Undo marking this post?')) return;

    try {
      const res = await fetch(`/api/posted?postId=${postId}`, {
        method: 'DELETE',
      });

      if (res.ok) {
        fetchPosts();
        fetchStats();
      }
    } catch (error) {
      console.error('Failed to undo:', error);
    }
  };

  // Get category display name
  const getCategoryName = (cat: string | null) => {
    if (!cat) return 'General';
    const names: Record<string, string> = {
      all: 'All',
      short: 'Short',
      bengali: 'Bengali',
      ai_ml: 'AI/ML',
      tech: 'Tech',
      tutorial: 'Tutorial',
      books: 'Books',
      thoughts: 'Thoughts',
    };
    return names[cat] || cat;
  };

  return (
    <main>
      <header className="header">
        <div className="header-content">
          <div className="header-left">
            <div className="logo">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 11l3 3L22 4" />
                <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
              </svg>
            </div>
            <div className="header-text">
              <h1>FB to Medium Copier</h1>
              <p>Browse your Facebook posts and copy to Medium</p>
            </div>
          </div>
          {stats && (
            <div className="stats">
              <div className="stat">
                <div className="stat-value">{stats.total.toLocaleString()}</div>
                <div className="stat-label">Total</div>
              </div>
              <div className="stat">
                <div className="stat-value">{stats.postedCount.toLocaleString()}</div>
                <div className="stat-label">Posted</div>
              </div>
              <div className="stat">
                <div className="stat-value">{stats.pendingCount.toLocaleString()}</div>
                <div className="stat-label">Pending</div>
              </div>
            </div>
          )}
        </div>
      </header>

      <div className="main">
        <div className="filters">
          <div className="filter-section">
            <span className="filter-label">Category</span>
            <div className="filter-chips">
              {CATEGORIES.map((cat) => (
                <button
                  key={cat}
                  className={`chip ${activeCategory === cat ? 'active' : ''}`}
                  onClick={() => {
                    setActiveCategory(cat);
                    setPage(1);
                  }}
                >
                  {getCategoryName(cat)}
                </button>
              ))}
            </div>
          </div>

<div className="filter-section">
            <span className="filter-label">Year</span>
            <div className="filter-chips">
              <button
                className={`chip ${activeYear === 'all' ? 'active' : ''}`}
                onClick={() => {
                  setActiveYear('all');
                  setPage(1);
                }}
              >
                All Years
              </button>
              {stats?.years.map((year) => (
                <button
                  key={year}
                  className={`chip ${activeYear === year ? 'active' : ''}`}
                  onClick={() => {
                    setActiveYear(year);
                    setPage(1);
                  }}
                >
                  {year}
                </button>
              ))}
            </div>
          </div>

          <div className="filter-section">
            <span className="filter-label">Search</span>
            <input
              type="text"
              className="search-input"
              placeholder="Search posts..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
            />
          </div>

          <div className="filter-section">
            <div className="filter-chips">
              <button
                className={`chip ${showPosted ? 'active' : ''}`}
                onClick={() => setShowPosted(!showPosted)}
              >
                Posted ({stats?.postedCount || 0})
              </button>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="loading">Loading posts...</div>
        ) : posts.length === 0 ? (
          <div className="empty-state">
            <p>No posts found</p>
          </div>
        ) : (
          <>
            <div className="posts-list">
              {posts.map((post) => (
                <div
                  key={post.id}
                  className={`post-card ${selected === post.id ? 'selected' : ''} ${post.isPosted ? 'posted' : ''}`}
                  onClick={() => setSelected(post.id)}
                >
                  <div className="post-header">
                    <span className="post-date">{post.date}</span>
                    {post.category && (
                      <span className="post-category">{getCategoryName(post.category)}</span>
                    )}
                  </div>
                  <div className="post-content">
                    {post.content.substring(0, 200)}
                    {post.content.length > 200 && '...'}
                  </div>
                  <div className="post-footer">
                    <div className="post-meta">
                      <span>{post.wordCount || 0} words</span>
                      {post.isPosted && <span style={{ color: 'var(--success)' }}>Posted</span>}
                    </div>
                    <div className="post-actions">
                      <button
                        className="btn btn-primary"
                        onClick={(e) => {
                          e.stopPropagation();
                          copyPost(post);
                        }}
                      >
                        Copy Text
                      </button>
                      {post.isPosted ? (
                        <button
                          className="btn btn-secondary"
                          onClick={(e) => {
                            e.stopPropagation();
                            undoMark(post.id);
                          }}
                        >
                          Undo
                        </button>
                      ) : (
                        <button
                          className="btn btn-success"
                          onClick={(e) => {
                            e.stopPropagation();
                            markPosted(post.id);
                          }}
                        >
                          Mark Posted
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {pagination && (
              <div className="pagination">
                <button
                  className="btn btn-secondary"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Previous
                </button>
                <span className="pagination-info">
                  Page {pagination.page} of {pagination.totalPages}
                </span>
                <button
                  className="btn btn-secondary"
                  onClick={() => setPage((p) => p + 1)}
                  disabled={page >= pagination.totalPages}
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </main>
  );
}
