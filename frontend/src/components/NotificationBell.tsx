import { useState } from "react";
import { useNotifications } from "../hooks/useNotifications";

export function NotificationBell() {
  const { notifications, connected } = useNotifications();
  const [open, setOpen] = useState(false);

  return (
    <div className="notification-bell">
      <button type="button" onClick={() => setOpen((prev) => !prev)}>
        🔔 {notifications.length > 0 && <span className="badge">{notifications.length}</span>}
        {!connected && <span className="dot dot--offline" title="disconnected" />}
      </button>
      {open && (
        <ul className="notification-bell__dropdown">
          {notifications.length === 0 && <li className="empty">No new notifications</li>}
          {notifications.map((n) => (
            <li key={n.id}>
              <strong>{n.actor}</strong> {n.notification_type}d your post
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
