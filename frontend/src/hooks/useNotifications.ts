import { useEffect, useRef, useState } from "react";
import { WS_BASE_URL, getAccessToken } from "../api/client";
import type { NotificationType } from "../types";

export interface LiveNotification {
  id: number;
  notification_type: NotificationType;
  actor: string;
  post_id: number | null;
  created_at: string;
}

interface UseNotificationsResult {
  notifications: LiveNotification[];
  connected: boolean;
  clear: () => void;
}

/** Connects to the Channels WebSocket consumer and appends live notifications as they arrive. */
export function useNotifications(): UseNotificationsResult {
  const [notifications, setNotifications] = useState<LiveNotification[]>([]);
  const [connected, setConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return undefined;

    const socket = new WebSocket(`${WS_BASE_URL}/ws/notifications/?token=${token}`);
    socketRef.current = socket;

    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onmessage = (event: MessageEvent<string>) => {
      const payload = JSON.parse(event.data) as { type: string; data?: LiveNotification };
      if (payload.type === "notification" && payload.data) {
        setNotifications((prev) => [payload.data as LiveNotification, ...prev]);
      }
    };

    return () => {
      socket.close();
      socketRef.current = null;
    };
  }, []);

  const clear = () => setNotifications([]);

  return { notifications, connected, clear };
}
