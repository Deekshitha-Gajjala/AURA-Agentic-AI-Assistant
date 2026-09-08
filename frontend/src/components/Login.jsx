import { useState } from "react";
import { ArrowRight, Lock, Mail, Sparkles } from "lucide-react";
import { loginUser, registerUser } from "../services/api";

function Login({ onLogin }) {
  const [isRegistering, setIsRegistering] = useState(false);

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      let data;

      if (isRegistering) {
        data = await registerUser(
          username,
          email,
          password
        );

        if (data.error || data.detail) {
          throw new Error(
            data.error ||
            data.detail ||
            "Registration failed."
          );
        }

        // Automatically log in after registration
        data = await loginUser(
          email,
          password
        );
      } else {
        data = await loginUser(
          email,
          password
        );

        if (data.error || data.detail) {
          throw new Error(
            data.error ||
            data.detail ||
            "Login failed."
          );
        }
      }

      if (!data.access_token) {
        throw new Error(
          "Login succeeded but no access token was returned."
        );
      }

      localStorage.setItem(
        "aura_token",
        data.access_token
      );

      localStorage.setItem(
        "aura_username",
        data.username || username
      );

      onLogin(
        data.username || username
      );

    } catch (err) {
      setError(
        err.message ||
        "Something went wrong."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">

      <div className="auth-card">

        <div className="auth-logo">
          <div className="auth-logo-mark">
            A
          </div>

          <div>
            <div className="auth-logo-name">
              AURA
            </div>

            <div className="auth-logo-tagline">
              Research, explained.
            </div>
          </div>
        </div>

        <div className="auth-icon">
          <Sparkles
            size={21}
            strokeWidth={1.7}
          />
        </div>

        <h1>
          {isRegistering
            ? "Create your account"
            : "Welcome back"}
        </h1>

        <p className="auth-subtitle">
          {isRegistering
            ? "Start exploring information with AURA."
            : "Sign in to continue your research."}
        </p>

        <form
          className="auth-form"
          onSubmit={handleSubmit}
        >

          {isRegistering && (
            <div className="input-group">
              <label>
                Name
              </label>

              <div className="input-wrapper">
                <input
                  type="text"
                  value={username}
                  onChange={(event) =>
                    setUsername(event.target.value)
                  }
                  placeholder="Your name"
                  required
                />
              </div>
            </div>
          )}

          <div className="input-group">
            <label>
              Email
            </label>

            <div className="input-wrapper">
              <Mail
                size={16}
                strokeWidth={1.7}
              />

              <input
                type="email"
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
                placeholder="you@example.com"
                required
              />
            </div>
          </div>

          <div className="input-group">
            <label>
              Password
            </label>

            <div className="input-wrapper">
              <Lock
                size={16}
                strokeWidth={1.7}
              />

              <input
                type="password"
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
                placeholder="Enter your password"
                required
              />
            </div>
          </div>

          {error && (
            <div className="auth-error">
              {error}
            </div>
          )}

          <button
            type="submit"
            className="auth-submit"
            disabled={loading}
          >
            <span>
              {loading
                ? "Please wait..."
                : isRegistering
                  ? "Create account"
                  : "Sign in"}
            </span>

            {!loading && (
              <ArrowRight
                size={17}
                strokeWidth={1.8}
              />
            )}
          </button>

        </form>

        <div className="auth-switch">

          <span>
            {isRegistering
              ? "Already have an account?"
              : "Don't have an account?"}
          </span>

          <button
            type="button"
            onClick={() => {
              setIsRegistering(
                !isRegistering
              );
              setError("");
            }}
          >
            {isRegistering
              ? "Sign in"
              : "Create account"}
          </button>

        </div>

      </div>

    </div>
  );
}

export default Login;