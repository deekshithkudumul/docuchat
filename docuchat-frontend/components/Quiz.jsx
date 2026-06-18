import { useState } from "react";
const API = "http://127.0.0.1:8000";
function ScoreRing({ score }) {
  const color = score >= 9 ? "#22c55e" : score >= 7 ? "#84cc16" : score >= 5 ? "#f59e0b" : score >= 3 ? "#f97316" : "#ef4444";
  return <div className="score-ring" style={{ "--score-color": color }}><div className="score-num" style={{ color }}>{score}</div><div className="score-denom">/10</div></div>;
}
function QuestionCard({ q, docId, index, token }) {
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showHint, setShowHint] = useState(false);
  async function submit() {
    if (!answer.trim() || loading) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/chat/evaluate`, { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify({ doc_id: docId, question: q.question, student_answer: answer }) });
      setResult(await res.json());
    } catch { setResult({ score: 0, feedback: "Connection error.", correct_answer: "", encouragement: "", score_label: "Error" }); }
    finally { setLoading(false); }
  }
  function reset() { setAnswer(""); setResult(null); setShowHint(false); }
  return (
    <div className={`q-card ${result ? "evaluated" : ""}`}>
      <div className="q-header"><div className="q-rank">Q{index + 1}</div><div className="q-importance">{q.importance}</div></div>
      <div className="q-text">{q.question}</div>
      {!result ? (
        <>
          <textarea className="q-answer" value={answer} onChange={(e) => setAnswer(e.target.value)} placeholder="Type your answer here…" rows={3} />
          <div className="q-actions">
            <button className="hint-btn" onClick={() => setShowHint(!showHint)}>{showHint ? "Hide hint" : "💡 Show hint"}</button>
            <button className="submit-btn" onClick={submit} disabled={!answer.trim() || loading}>{loading ? "Evaluating…" : "Submit answer →"}</button>
          </div>
          {showHint && <div className="hint-box">💡 {q.hint}</div>}
        </>
      ) : (
        <div className="result-panel">
          <div className="result-top"><ScoreRing score={result.score} /><div className="result-labels"><div className="result-label">{result.score_label}</div><div className="result-encourage">{result.encouragement}</div></div></div>
          <div className="result-section"><div className="result-section-label">Your answer</div><div className="result-student-answer">{answer}</div></div>
          <div className="result-section"><div className="result-section-label">Feedback</div><div className="result-feedback">{result.feedback}</div></div>
          <div className="result-section correct"><div className="result-section-label">✅ Correct answer</div><div className="result-correct">{result.correct_answer}</div></div>
          <button className="ghost-btn" onClick={reset}>↺ Try again</button>
        </div>
      )}
    </div>
  );
}
export default function Quiz({ docId, token }) {
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [numQ, setNumQ] = useState(5);
  async function fetchQuiz() {
    setLoading(true); setError(null); setQuestions([]);
    try {
      const res = await fetch(`${API}/chat/quiz`, { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify({ doc_id: docId, num_questions: numQ }) });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to generate quiz");
      setQuestions(data.questions);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }
  return (
    <div className="page-wrap">
      <div className="page-header"><h1>🎓 Quiz Mode</h1><p>AI generates exam questions ranked by importance</p></div>
      {questions.length === 0 && !loading && (
        <div className="action-card">
          <div className="action-icon">🎯</div>
          <div className="action-text"><strong>Test your knowledge</strong><span>{docId}</span></div>
          <div className="quiz-controls">
            <label className="num-label">Questions:<select className="num-select" value={numQ} onChange={(e) => setNumQ(Number(e.target.value))}>{[3,5,7,10].map(n=><option key={n} value={n}>{n}</option>)}</select></label>
            <button className="primary-btn" onClick={fetchQuiz}>Generate quiz →</button>
          </div>
        </div>
      )}
      {loading && <div className="loading-card"><div className="spinner large" /><p>Generating {numQ} questions…</p></div>}
      {error && <div className="error-card">⚠ {error}</div>}
      {questions.length > 0 && (<><div className="quiz-meta"><span>{questions.length} questions • ranked by importance</span><button className="ghost-btn" onClick={fetchQuiz}>↺ New quiz</button></div><div className="questions-list">{questions.map((q,i)=><QuestionCard key={i} q={q} docId={docId} index={i} token={token}/>)}</div></>)}
    </div>
  );
}
