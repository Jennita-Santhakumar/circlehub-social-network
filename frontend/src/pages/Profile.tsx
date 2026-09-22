import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { User } from "../types";

export function Profile() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .me()
      .then(setUser)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading...</p>;
  if (!user) return <p>Could not load profile.</p>;

  return (
    <div className="profile">
      <h1>{user.username}</h1>
      <p>{user.email}</p>
      <p>{user.profile.bio || "No bio yet."}</p>
      <div className="profile__stats">
        <span>{user.profile.followers_count} followers</span>
        <span>{user.profile.following_count} following</span>
      </div>
    </div>
  );
}
