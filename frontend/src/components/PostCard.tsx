import { useState } from "react";
import { api } from "../api/client";
import type { Post } from "../types";

interface PostCardProps {
  post: Post;
  onChanged: () => void;
}

export function PostCard({ post, onChanged }: PostCardProps) {
  const [commentText, setCommentText] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const toggleLike = async () => {
    if (post.is_liked) {
      await api.unlikePost(post.id);
    } else {
      await api.likePost(post.id);
    }
    onChanged();
  };

  const submitComment = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!commentText.trim()) return;
    setSubmitting(true);
    try {
      await api.createComment(post.id, commentText.trim());
      setCommentText("");
      onChanged();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <article className="post-card">
      <header className="post-card__header">
        <span className="post-card__author">{post.author.username}</span>
        <time className="post-card__time">{new Date(post.created_at).toLocaleString()}</time>
      </header>
      <p className="post-card__content">{post.content}</p>
      <div className="post-card__actions">
        <button type="button" onClick={toggleLike} className={post.is_liked ? "liked" : ""}>
          {post.is_liked ? "♥" : "♡"} {post.likes_count}
        </button>
        <span>{post.comments_count} comments</span>
      </div>
      <ul className="post-card__comments">
        {post.comments.map((comment) => (
          <li key={comment.id}>
            <strong>{comment.author.username}</strong>: {comment.content}
          </li>
        ))}
      </ul>
      <form className="post-card__comment-form" onSubmit={submitComment}>
        <input
          value={commentText}
          onChange={(event) => setCommentText(event.target.value)}
          placeholder="Write a comment..."
        />
        <button type="submit" disabled={submitting}>
          Send
        </button>
      </form>
    </article>
  );
}
