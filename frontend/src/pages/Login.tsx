import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api, ApiError } from "../api/client";

export function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await api.login(username, password);
      navigate("/feed");
    } catch (err) {
      setError(err instanceof ApiError ? "Invalid username or password." : "Login failed.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <h1>SocialPulse</h1>
      <form onSubmit={submit} className="auth-form">
        <input placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
        <input
          placeholder="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={submitting}>
          Log in
        </button>
      </form>
      <p>
        No account? <Link to="/register">Register</Link>
      </p>
    </div>
  );
}
