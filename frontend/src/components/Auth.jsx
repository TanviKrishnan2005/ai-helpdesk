
import { useState } from "react";
import axios from "axios";
import "./Auth.css";

const API_URL = "http://127.0.0.1:8000";

function Auth({ onLogin }) {
  const [isRegistering, setIsRegistering] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (!email.trim() || !password) {
      setError("Please enter your email and password.");
      return;
    }

    if (isRegistering && !name.trim()) {
      setError("Please enter your name.");
      return;
    }

    setLoading(true);

    try {
      if (isRegistering) {
        await axios.post(`${API_URL}/auth/register`, null, {
          params: {
            name: name.trim(),
            email: email.trim(),
            password,
            role: "user",
          },
        });

        setSuccess("Account created! You can now log in.");
        setIsRegistering(false);
        setName("");
        setPassword("");
      } else {
        const formData = new URLSearchParams();
        formData.append("username", email.trim());
        formData.append("password", password);

        const response = await axios.post(
          `${API_URL}/auth/login`,
          formData,
          {
            headers: {
              "Content-Type": "application/x-www-form-urlencoded",
            },
          }
        );

        onLogin(response.data);
      }
    } catch (err) {
      const detail = err.response?.data?.detail;

      setError(
        typeof detail === "string"
          ? detail
          : "Something went wrong. Please check your details and try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-panel">
        <div className="auth-brand">
          <div className="auth-brand-icon">H</div>
          <span>Helpdesk AI</span>
        </div>

        <div className="auth-heading">
          <p className="auth-eyebrow">
            YOUR SUPPORT WORKSPACE
          </p>

          <h1>
            {isRegistering
              ? "Create your account"
              : "Welcome back"}
          </h1>

          <p className="auth-subtitle">
            {isRegistering
              ? "Get started with smarter support."
              : "Sign in to continue to your helpdesk."}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {isRegistering && (
            <div className="auth-field">
              <label htmlFor="auth-name">Full name</label>
              <input
                id="auth-name"
                type="text"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Enter your name"
                autoComplete="name"
                required
              />
            </div>
          )}

          <div className="auth-field">
            <label htmlFor="auth-email">Email address</label>
            <input
              id="auth-email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
              autoComplete="email"
              required
            />
          </div>

          <div className="auth-field">
            <label htmlFor="auth-password">Password</label>
            <input
              id="auth-password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter your password"
              autoComplete={
                isRegistering ? "new-password" : "current-password"
              }
              minLength={isRegistering ? 8 : undefined}
              required
            />
            {isRegistering && (
              <span className="auth-hint">
                Use at least 8 characters.
              </span>
            )}
          </div>

          {error && (
            <p className="auth-message auth-error" role="alert">
              {error}
            </p>
          )}

          {success && (
            <p className="auth-message auth-success" role="status">
              {success}
            </p>
          )}

          <button
            type="submit"
            className="auth-submit"
            disabled={loading}
          >
            {loading
              ? "Please wait..."
              : isRegistering
                ? "Create account"
                : "Sign in"}
          </button>
        </form>

        <div className="auth-switch">
          {isRegistering
            ? "Already have an account?"
            : "New to Helpdesk AI?"}

          <button
            type="button"
            onClick={() => {
              setIsRegistering(!isRegistering);
              setError("");
              setSuccess("");
            }}
          >
            {isRegistering ? "Sign in" : "Create account"}
          </button>
        </div>

        <p className="auth-footer">
          AI-powered support · Simple, organised, reliable
        </p>
      </div>
    </div>
  );
}

export default Auth;
