import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import { CreatePostModal } from "../components/CreatePostModal";
import { PostCard } from "../components/PostCard";
import type { Post } from "../types";

export function Feed() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const fetchFeed = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.feed();
      setPosts(data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFeed();
  }, [fetchFeed]);

  return (
    <div className="feed">
      <div className="feed__header">
        <h1>Feed</h1>
        <button type="button" onClick={() => setShowCreateModal(true)}>
          + Create Post
        </button>
      </div>

      {showCreateModal && (
        <CreatePostModal onClose={() => setShowCreateModal(false)} onCreated={fetchFeed} />
      )}

      <div className="feed__list">
        {loading && <p>Loading...</p>}
        {!loading && posts.length === 0 && (
          <p className="empty">Your feed is empty. Follow someone to see their posts here.</p>
        )}
        {posts.map((post) => (
          <PostCard key={post.id} post={post} onChanged={fetchFeed} />
        ))}
      </div>
    </div>
  );
}
