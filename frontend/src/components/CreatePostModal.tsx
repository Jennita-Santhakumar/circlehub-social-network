import { useState } from "react";
import { api } from "../api/client";

interface CreatePostModalProps {
  onClose: () => void;
  onCreated: () => void;
}

export function CreatePostModal({ onClose, onCreated }: CreatePostModalProps) {
  const [content, setContent] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!content.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.createPost(content.trim());
      onCreated();
      onClose();
    } catch {
      setError("Failed to create post. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <div className="modal">
        <h2>Create Post</h2>
        <form onSubmit={submit}>
          <textarea
            value={content}
            onChange={(event) => setContent(event.target.value)}
            placeholder="What's happening?"
            rows={4}
            autoFocus
          />
          {error && <p className="error">{error}</p>}
          <div className="modal__actions">
            <button type="button" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" disabled={submitting}>
              Post
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
