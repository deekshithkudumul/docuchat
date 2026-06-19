import { useState, useRef, useEffect } from "react";
const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
function Message({ msg }) {
  if (msg.role === "user") return <div className="msg msg-user"><div className="msg-bubble">{msg.text}</div></div>;
  return (
    <div className="msg msg-bot">
      <div className="msg-avatar">AI</div>
      <div className="msg-content">
        <div className="msg-bubble">{msg.text}</div>
        {msg.highlight && (
          <div className="highlight-box">
            <div className="highlight-label">📍 Source excerpt</div>
            <blockquote className="highlight-quote">"{msg.highlight}"</blockquote>
            {msg.source_doc && <div className="highlight-source">from {msg.source_doc}</div>}
          </div>
        )}
      </div>
    </div>
  );
}
export default function Chat({ docId, token }) {
  const [messages, setMessages] = useState([{ role: "bot", text: "Hi! Ask me anything about your document." }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef();
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);
  async function send() {
    const q = input.trim();
    if (!q || loading) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text: q }]);
    setLoading(true);
    try {
      const res = await fetch(`${API}/chat/`, { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify({ question: q, doc_id: docId }) });
      const data = await res.json();
      setMessages((m) => [...m, { role: "bot", text: data.answer, highlight: data.highlight, source_doc: data.source_doc }]);
    } catch { setMessages((m) => [...m, { role: "bot", text: "Connection error. Is the server running?" }]); }
    finally { setLoading(false); }
  }
  return (
    <div className="chat-wrap">
      <div className="page-header"><h1>💬 Chat</h1><p>Ask anything about your document</p></div>
      <div className="chat-messages">
        {messages.map((m, i) => <Message key={i} msg={m} />)}
        {loading && <div className="msg msg-bot"><div className="msg-avatar">AI</div><div className="msg-bubble typing"><span /><span /><span /></div></div>}
        <div ref={bottomRef} />
      </div>
      <div className="chat-input-row">
        <input className="chat-input" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send()} placeholder="Ask a question…" disabled={loading} />
        <button className="send-btn" onClick={send} disabled={loading || !input.trim()}>Send →</button>
      </div>
    </div>
  );
}
