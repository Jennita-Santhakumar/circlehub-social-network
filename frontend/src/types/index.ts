export interface UserProfile {
  bio: string;
  avatar: string | null;
  followers_count: number;
  following_count: number;
}

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  profile: UserProfile;
}

export interface Comment {
  id: number;
  post: number;
  author: User;
  content: string;
  created_at: string;
}

export interface Post {
  id: number;
  author: User;
  content: string;
  image: string | null;
  likes_count: number;
  comments_count: number;
  comments: Comment[];
  is_liked: boolean;
  created_at: string;
  updated_at: string;
}

export interface Follow {
  id: number;
  follower: User;
  following: User;
  created_at: string;
}

export type NotificationType = "like" | "comment" | "follow" | "mention";

export interface Notification {
  id: number;
  recipient: number;
  actor: User;
  notification_type: NotificationType;
  post: number | null;
  is_read: boolean;
  created_at: string;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface AuthTokens {
  access: string;
  refresh: string;
}
