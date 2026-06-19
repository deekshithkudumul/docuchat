import { useState } from "react";
const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
export default function Summarize({ docId, token }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  async function fetchSummary() {
    setLoading(true); setError(null); setSummary(null);
    try {
      const res = await fetch(`${API}/chat/summarize`, { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify({ doc_id: docId }) });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to summarize");
      setSummary(data.summary);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }
  function renderSummary(text) {
    return text.split("\n").map((line, i) => {
      if (!line.trim()) return <br key={i} />;
      if (line.match(/^\d+\./)) return <h3 key={i} className="sum-heading">{line}</h3>;
      if (line.startsWith("•") || line.startsWith("-") || line.startsWith("*")) return <li key={i} className="sum-bullet">{line.replace(/^[•\-\*]\s*/, "")}</li>;
      return <p key={i} className="sum-para">{line}</p>;
    });
  }
  return (
    <div className="page-wrap">
      <div className="page-header"><h1>📝 Summarize</h1><p>Get a structured summary of your entire document</p></div>
      {!summary && !loading && <div className="action-card"><div className="action-icon">📄</div><div className="action-text"><strong>Ready to summarize</strong><span>{docId}</span></div><button className="primary-btn" onClick={fetchSummary}>Summarize document →</button></div>}
      {loading && <div className="loading-card"><div className="spinner large" /><p>Reading your document…</p></div>}
      {error && <div className="error-card">⚠ {error}</div>}
      {summary && <div className="summary-card"><div className="summary-header"><span>Summary</span><button className="ghost-btn" onClick={fetchSummary}>↺ Regenerate</button></div><div className="summary-body">{renderSummary(summary)}</div></div>}
    </div>
  );
}
