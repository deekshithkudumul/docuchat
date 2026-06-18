import { useState, useEffect } from "react";
import AuthPage from "./AuthPage";
import Upload from "./components/Upload";
import Chat from "./components/Chat";
import Summarize from "./components/Summarize";
import Quiz from "./components/Quiz";

const TABS = ["Chat", "Summarize", "Quiz"];

export default function App() {
  const [user, setUser] = useState(null);
  const [docId, setDocId] = useState(null);
  const [activeTab, setActiveTab] = useState("Chat");
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("dc_token");
    const name = localStorage.getItem("dc_name");
    if (token && name) setUser({ name, token });
    setChecking(false);
  }, []);

  function handleLogin(userData) {
    setUser(userData);
  }

  function logout() {
    localStorage.removeItem("dc_token");
    localStorage.removeItem("dc_name");
    setUser(null);
    setDocId(null);
  }

  if (checking) return null;
  if (!user) return <AuthPage onLogin={handleLogin} />;

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">📄</div>
          <div>
            <div className="brand-name">DocuChat</div>
            <div className="brand-sub">AI Document Assistant</div>
          </div>
        </div>

        <Upload onUploaded={setDocId} docId={docId} token={user.token} />

        {docId && (
          <nav className="nav">
            <div className="nav-label">Features</div>
            {TABS.map((tab) => (
              <button
                key={tab}
                className={`nav-btn ${activeTab === tab ? "active" : ""}`}
                onClick={() => setActiveTab(tab)}
              >
                <span className="nav-icon">
                  {tab === "Chat" ? "💬" : tab === "Summarize" ? "📝" : "🎓"}
                </span>
                {tab}
              </button>
            ))}
          </nav>
        )}

        {docId && (
          <div className="doc-badge">
            <div className="doc-badge-label">Active document</div>
            <div className="doc-badge-name" title={docId}>
              📄 {docId.length > 24 ? docId.slice(0, 24) + "…" : docId}
            </div>
            <button className="doc-clear" onClick={() => setDocId(null)}>Change document</button>
          </div>
        )}

        <div className="user-bar">
          <div className="user-avatar">{user.name[0].toUpperCase()}</div>
          <div className="user-info">
            <div className="user-name">{user.name}</div>
          </div>
          <button className="logout-btn" onClick={logout} title="Logout">↩</button>
        </div>
      </aside>

      <main className="main">
        {!docId ? (
          <div className="empty-state">
            <div className="empty-icon">📂</div>
            <h2>Upload a document to get started</h2>
            <p>Supports any PDF — textbooks, notes, reports, resumes.</p>
          </div>
        ) : (
          <>
            {activeTab === "Chat" && <Chat docId={docId} token={user.token} />}
            {activeTab === "Summarize" && <Summarize docId={docId} token={user.token} />}
            {activeTab === "Quiz" && <Quiz docId={docId} token={user.token} />}
          </>
        )}
      </main>
    </div>
  );
}
