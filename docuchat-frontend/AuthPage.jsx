import { useState } from "react";

const API = "http://127.0.0.1:8000";

export default function AuthPage({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  function update(e) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  function switchMode(m) {
    setMode(m);
    setError(null);
    setForm({ name: "", email: "", password: "" });
  }

  async function submit() {
    setError(null);
    if (!form.email || !form.password) { setError("Please fill in all fields."); return; }
    if (mode === "register" && !form.name.trim()) { setError("Please enter your name."); return; }
    setLoading(true);
    try {
      let res, data;
      if (mode === "register") {
        res = await fetch(`${API}/auth/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: form.name, email: form.email, password: form.password }),
        });
      } else {
        res = await fetch(`${API}/auth/login`, {
          method: "POST",
          body: new URLSearchParams({ username: form.email, password: form.password }),
        });
      }
      data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Something went wrong.");
      localStorage.setItem("dc_token", data.access_token);
      localStorage.setItem("dc_name", data.user_name);
      onLogin({ name: data.user_name, email: data.user_email, token: data.access_token });
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const inp = { padding: "10px 14px", background: "#22263a", border: "1px solid #2e3250", borderRadius: "8px", color: "#e8eaf6", fontSize: "14px", fontFamily: "inherit", outline: "none", width: "100%" };

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#0f1117", fontFamily: "Inter, sans-serif" }}>
      <div style={{ width: "100%", maxWidth: "400px", background: "#1a1d27", border: "1px solid #2e3250", borderRadius: "12px", padding: "40px 36px" }}>

        <div style={{ textAlign: "center", marginBottom: "28px" }}>
          <div style={{ fontSize: "40px" }}>📄</div>
          <h1 style={{ color: "#e8eaf6", fontSize: "24px", margin: "8px 0 4px", fontWeight: 600 }}>DocuChat</h1>
          <p style={{ color: "#9095b8", fontSize: "13px", margin: 0 }}>AI Document Assistant</p>
        </div>

        <div style={{ display: "flex", background: "#22263a", borderRadius: "8px", padding: "4px", gap: "4px", marginBottom: "24px" }}>
          {["login", "register"].map((m) => (
            <button key={m} onClick={() => switchMode(m)} style={{ flex: 1, padding: "8px", border: "none", borderRadius: "6px", background: mode === m ? "#6c8fff" : "transparent", color: mode === m ? "#fff" : "#9095b8", fontWeight: mode === m ? 600 : 400, fontSize: "14px", cursor: "pointer", fontFamily: "inherit", textTransform: "capitalize" }}>
              {m === "login" ? "Login" : "Register"}
            </button>
          ))}
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {mode === "register" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <label style={{ fontSize: "12px", color: "#9095b8", fontWeight: 500 }}>Full Name</label>
              <input name="name" type="text" placeholder="Deekshith Reddy" value={form.name} onChange={update} style={inp} />
            </div>
          )}
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <label style={{ fontSize: "12px", color: "#9095b8", fontWeight: 500 }}>Email</label>
            <input name="email" type="email" placeholder="you@example.com" value={form.email} onChange={update} style={inp} />
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <label style={{ fontSize: "12px", color: "#9095b8", fontWeight: 500 }}>Password</label>
            <input name="password" type="password" placeholder="••••••••" value={form.password} onChange={update} onKeyDown={(e) => e.key === "Enter" && submit()} style={inp} />
          </div>

          {error && <div style={{ background: "rgba(239,68,68,.1)", border: "1px solid rgba(239,68,68,.3)", borderRadius: "6px", padding: "10px 14px", fontSize: "13px", color: "#ef4444" }}>⚠ {error}</div>}

          <button onClick={submit} disabled={loading} style={{ padding: "12px", background: loading ? "#4a5080" : "#6c8fff", color: "#fff", border: "none", borderRadius: "8px", fontSize: "15px", fontWeight: 500, cursor: loading ? "default" : "pointer", fontFamily: "inherit", marginTop: "4px" }}>
            {loading ? "Please wait…" : mode === "login" ? "Login →" : "Create account →"}
          </button>

          <p style={{ textAlign: "center", fontSize: "13px", color: "#9095b8", margin: 0 }}>
            {mode === "login" ? "No account? " : "Have an account? "}
            <span onClick={() => switchMode(mode === "login" ? "register" : "login")} style={{ color: "#6c8fff", cursor: "pointer" }}>
              {mode === "login" ? "Register" : "Login"}
            </span>
          </p>
        </div>
      </div>
    </div>
  );
}
