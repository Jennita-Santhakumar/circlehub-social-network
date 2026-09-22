import { Navigate, Route, Routes, Link, useNavigate } from "react-router-dom";
import { NotificationBell } from "./components/NotificationBell";
import { Feed } from "./pages/Feed";
import { Login } from "./pages/Login";
import { Profile } from "./pages/Profile";
import { Register } from "./pages/Register";
import { clearTokens, getAccessToken } from "./api/client";

function isAuthenticated(): boolean {
  return Boolean(getAccessToken());
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

function NavBar() {
  const navigate = useNavigate();
  const authed = isAuthenticated();

  const logout = () => {
    clearTokens();
    navigate("/login");
  };

  if (!authed) return null;

  return (
    <nav className="navbar">
      <Link to="/feed">SocialPulse</Link>
      <div className="navbar__right">
        <Link to="/profile">Profile</Link>
        <NotificationBell />
        <button type="button" onClick={logout}>
          Log out
        </button>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <div className="app">
      <NavBar />
      <main className="app__main">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/feed"
            element={
              <ProtectedRoute>
                <Feed />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to={isAuthenticated() ? "/feed" : "/login"} replace />} />
        </Routes>
      </main>
    </div>
  );
}
