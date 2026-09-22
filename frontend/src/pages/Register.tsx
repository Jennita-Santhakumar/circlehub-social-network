import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api } from "../api/client";

export function Register() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await api.register({ username, email, password });
      await api.login(username, password);
      navigate("/feed");
    } catch {
      setError("Registration failed. Try a different username or a stronger password.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <h1>Create your SocialPulse account</h1>
      <form onSubmit={submit} className="auth-form">
        <input placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
        <input placeholder="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        <input
          placeholder="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={submitting}>
          Register
        </button>
      </form>
      <p>
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </div>
  );
}
