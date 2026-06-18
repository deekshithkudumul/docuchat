import { useState, useRef } from "react";
const API = "http://127.0.0.1:8000";
export default function Upload({ onUploaded, docId, token }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [info, setInfo] = useState(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef();
  async function handleFile(file) {
    if (!file || !file.name.endsWith(".pdf")) { setError("Only PDF files are supported."); return; }
    setError(null); setInfo(null); setLoading(true);
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await fetch(`${API}/upload/`, { method: "POST", headers: { Authorization: `Bearer ${token}` }, body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Upload failed");
      setInfo(`${data.chunks_stored} chunks from ${data.num_pages} page(s)`);
      onUploaded(data.filename);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }
  function onDrop(e) { e.preventDefault(); setDragging(false); handleFile(e.dataTransfer.files[0]); }
  return (
    <div className="upload-section">
      <div className="upload-label">Document</div>
      <div className={`dropzone ${dragging ? "dragging" : ""} ${docId ? "has-doc" : ""}`}
        onClick={() => inputRef.current.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)} onDrop={onDrop}>
        <input ref={inputRef} type="file" accept=".pdf" style={{ display: "none" }} onChange={(e) => handleFile(e.target.files[0])} />
        {loading ? <div className="upload-loading"><div className="spinner" /><span>Processing…</span></div>
          : docId ? <div className="upload-done"><span className="upload-check">✓</span><span>Upload new PDF</span></div>
          : <div className="upload-prompt"><span className="upload-arrow">↑</span><span>Drop PDF or click</span></div>}
      </div>
      {info && <div className="upload-info">✓ {info}</div>}
      {error && <div className="upload-error">⚠ {error}</div>}
    </div>
  );
}
