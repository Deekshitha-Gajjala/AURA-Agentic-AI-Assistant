import { useState } from "react";
import { loginUser, registerUser } from "../services/api";

function AuthPage({ onLogin }) {
  const [isRegistering, setIsRegistering] = useState(false);

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (!email.trim() || !password.trim()) {
      setError("Please enter your email and password.");
      return;
    }

    if (isRegistering && !username.trim()) {
      setError("Please enter a username.");
      return;
    }

    setLoading(true);

    try {
      // ============================================================
      // REGISTER
      // ============================================================

      if (isRegistering) {
        const data = await registerUser(
          username.trim(),
          email.trim(),
          password
        );

        if (!data.success) {
          throw new Error(
            data.message || "Registration failed."
          );
        }

        setSuccess(
          "Account created successfully. You can now log in."
        );

        setIsRegistering(false);
        setUsername("");
        setPassword("");

        return;
      }

      // ============================================================
      // LOGIN
      // ============================================================

      const data = await loginUser(
        email.trim(),
        password
      );

      if (!data.success) {
        throw new Error(
          data.message || "Login failed."
        );
      }

      // ============================================================
      // SAVE AUTHENTICATION DATA
      // ============================================================

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
        "aura_user",
        JSON.stringify({
          user_id: data.user_id,
          username: data.username,
          email: data.email
        })
      );

      // ============================================================
      // TELL APP THAT LOGIN IS COMPLETE
      // ============================================================

      onLogin(data);

    } catch (err) {
      console.error("AUTH ERROR:", err);

      setError(
        err.message ||
          "Something went wrong. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const switchMode = () => {
    setIsRegistering((previous) => !previous);

    setError("");
    setSuccess("");
    setUsername("");
    setPassword("");
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#ffffff",
        fontFamily:
          "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
        padding: "24px",
        boxSizing: "border-box"
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "410px"
        }}
      >
        {/* ========================================================
            BRAND
        ======================================================== */}

        <div
          style={{
            textAlign: "center",
            marginBottom: "34px"
          }}
        >
          <div
            style={{
              width: "48px",
              height: "48px",
              borderRadius: "14px",
              background: "#171717",
              color: "#ffffff",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 16px",
              fontSize: "22px",
              fontWeight: "600"
            }}
          >
            A
          </div>

          <h1
            style={{
              margin: 0,
              fontSize: "28px",
              fontWeight: "600",
              letterSpacing: "-0.5px",
              color: "#171717"
            }}
          >
            AURA
          </h1>

          <p
            style={{
              margin: "8px 0 0",
              color: "#6b7280",
              fontSize: "14px"
            }}
          >
            Research, explained.
          </p>
        </div>

        {/* ========================================================
            CARD
        ======================================================== */}

        <div
          style={{
            border: "1px solid #e5e7eb",
            borderRadius: "18px",
            padding: "30px",
            background: "#ffffff",
            boxShadow:
              "0 8px 30px rgba(0, 0, 0, 0.04)"
          }}
        >
          <h2
            style={{
              margin: "0 0 7px",
              fontSize: "21px",
              fontWeight: "600",
              color: "#171717"
            }}
          >
            {isRegistering
              ? "Create your account"
              : "Welcome back"}
          </h2>

          <p
            style={{
              margin: "0 0 24px",
              color: "#6b7280",
              fontSize: "14px"
            }}
          >
            {isRegistering
              ? "Create an account to start using AURA."
              : "Sign in to continue to AURA."}
          </p>

          {/* ======================================================
              ERROR
          ====================================================== */}

          {error && (
            <div
              style={{
                padding: "11px 13px",
                borderRadius: "10px",
                background: "#fef2f2",
                border: "1px solid #fecaca",
                color: "#b91c1c",
                fontSize: "13px",
                marginBottom: "16px"
              }}
            >
              {error}
            </div>
          )}

          {/* ======================================================
              SUCCESS
          ====================================================== */}

          {success && (
            <div
              style={{
                padding: "11px 13px",
                borderRadius: "10px",
                background: "#f0fdf4",
                border: "1px solid #bbf7d0",
                color: "#166534",
                fontSize: "13px",
                marginBottom: "16px"
              }}
            >
              {success}
            </div>
          )}

          <form onSubmit={handleSubmit}>

            {/* ====================================================
                USERNAME
            ==================================================== */}

            {isRegistering && (
              <div style={{ marginBottom: "16px" }}>
                <label
                  style={{
                    display: "block",
                    fontSize: "13px",
                    fontWeight: "500",
                    color: "#374151",
                    marginBottom: "7px"
                  }}
                >
                  Username
                </label>

                <input
                  type="text"
                  value={username}
                  onChange={(event) =>
                    setUsername(event.target.value)
                  }
                  placeholder="Your name"
                  autoComplete="username"
                  style={{
                    width: "100%",
                    height: "44px",
                    boxSizing: "border-box",
                    border: "1px solid #d1d5db",
                    borderRadius: "10px",
                    padding: "0 13px",
                    fontSize: "14px",
                    outline: "none"
                  }}
                />
              </div>
            )}

            {/* ====================================================
                EMAIL
            ==================================================== */}

            <div style={{ marginBottom: "16px" }}>
              <label
                style={{
                  display: "block",
                  fontSize: "13px",
                  fontWeight: "500",
                  color: "#374151",
                  marginBottom: "7px"
                }}
              >
                Email
              </label>

              <input
                type="email"
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
                placeholder="you@example.com"
                autoComplete="email"
                style={{
                  width: "100%",
                  height: "44px",
                  boxSizing: "border-box",
                  border: "1px solid #d1d5db",
                  borderRadius: "10px",
                  padding: "0 13px",
                  fontSize: "14px",
                  outline: "none"
                }}
              />
            </div>

            {/* ====================================================
                PASSWORD
            ==================================================== */}

            <div style={{ marginBottom: "20px" }}>
              <label
                style={{
                  display: "block",
                  fontSize: "13px",
                  fontWeight: "500",
                  color: "#374151",
                  marginBottom: "7px"
                }}
              >
                Password
              </label>

              <input
                type="password"
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
                placeholder="Enter your password"
                autoComplete={
                  isRegistering
                    ? "new-password"
                    : "current-password"
                }
                style={{
                  width: "100%",
                  height: "44px",
                  boxSizing: "border-box",
                  border: "1px solid #d1d5db",
                  borderRadius: "10px",
                  padding: "0 13px",
                  fontSize: "14px",
                  outline: "none"
                }}
              />
            </div>

            {/* ====================================================
                SUBMIT
            ==================================================== */}

            <button
              type="submit"
              disabled={loading}
              style={{
                width: "100%",
                height: "44px",
                border: "none",
                borderRadius: "10px",
                background: loading
                  ? "#6b7280"
                  : "#171717",
                color: "#ffffff",
                fontSize: "14px",
                fontWeight: "500",
                cursor: loading
                  ? "not-allowed"
                  : "pointer"
              }}
            >
              {loading
                ? "Please wait..."
                : isRegistering
                ? "Create account"
                : "Sign in"}
            </button>
          </form>

          {/* ======================================================
              SWITCH LOGIN / REGISTER
          ====================================================== */}

          <div
            style={{
              textAlign: "center",
              marginTop: "22px",
              fontSize: "13px",
              color: "#6b7280"
            }}
          >
            {isRegistering
              ? "Already have an account?"
              : "Don't have an account?"}

            <button
              type="button"
              onClick={switchMode}
              style={{
                border: "none",
                background: "transparent",
                color: "#171717",
                fontWeight: "600",
                cursor: "pointer",
                marginLeft: "5px",
                padding: 0
              }}
            >
              {isRegistering
                ? "Sign in"
                : "Create one"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AuthPage;