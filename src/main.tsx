import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { Activity, FileText, LockKeyhole, Search, ShieldCheck, Upload, X } from "lucide-react";
import "./styles.css";

const API = "http://127.0.0.1:8765";
type Source = { chunk: { document_name: string; text: string }; score: number };
type Document = { id: string; name: string; chunks: number };

function App() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("Ask a question over your local evidence base.");
  const [sources, setSources] = useState<Source[]>([]);
  const [status, setStatus] = useState("Connecting to local vault");
  const [busy, setBusy] = useState(false);

  const refresh = () => fetch(`${API}/api/documents`).then((r) => r.json()).then(setDocuments).then(() => setStatus("Local vault ready")).catch(() => setStatus("Start the local API to connect"));
  useEffect(() => { refresh(); }, []);
  const upload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]; if (!file) return; setBusy(true); setStatus(`Indexing ${file.name}`);
    const body = new FormData(); body.append("file", file);
    await fetch(`${API}/api/documents`, { method: "POST", body }); setBusy(false); await refresh();
  };
  const ask = async (event: React.FormEvent) => {
    event.preventDefault(); if (!query.trim()) return; setBusy(true);
    const response = await fetch(`${API}/api/query`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query }) });
    const data = await response.json(); setAnswer(data.answer); setSources(data.sources ?? []); setBusy(false);
  };
  const clear = async () => { await fetch(`${API}/api/documents`, { method: "DELETE" }); setDocuments([]); setSources([]); setAnswer("Ask a question over your local evidence base."); };
  return <main className="app-shell">
    <aside className="sidebar"><div className="brand"><div className="mark"><LockKeyhole size={20} /></div><div><strong>VaultRAG</strong><span>private intelligence</span></div></div>
      <div className="side-label">WORKSPACE</div><div className="nav active"><Activity size={16} /> Evidence desk</div><div className="nav"><ShieldCheck size={16} /> Privacy controls <span className="dot" /></div>
      <div className="sidebar-bottom"><div className="secure"><span className="pulse" /> Local-only mode<strong>Nothing leaves this device</strong></div><button className="clear" onClick={clear}><X size={14} /> Clear vault</button></div>
    </aside>
    <section className="content"><header><div><div className="eyebrow">SECURE RESEARCH CONSOLE</div><h1>Evidence desk</h1></div><div className="connection"><span className="pulse" /> {status}</div></header>
      <div className="metrics"><div><span>Documents</span><strong>{documents.length.toString().padStart(2, "0")}</strong></div><div><span>Indexed passages</span><strong>{documents.reduce((sum, item) => sum + item.chunks, 0).toString().padStart(2, "0")}</strong></div><div><span>Cloud exposure</span><strong className="green">0 bytes</strong></div></div>
      <div className="workspace"><section className="query-panel"><div className="panel-heading"><div><span className="section-kicker">LOCAL REASONING</span><h2>Ask your evidence</h2></div><span className="protected"><ShieldCheck size={14} /> masked before inference</span></div>
        <form onSubmit={ask} className="query-form"><Search size={19} /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="What do the records say about..." /><button disabled={busy} type="submit">{busy ? "Working" : "Search"}</button></form>
        <div className="answer"><div className="answer-label">LOCAL RESPONSE</div><p>{answer}</p>{sources.length > 0 && <div className="sources">{sources.map((source, i) => <article key={i}><div><FileText size={15} /><strong>{source.chunk.document_name}</strong></div><span>{Math.round(source.score * 100)}% match</span><p>{source.chunk.text}</p></article>)}</div>}</div>
      </section><aside className="library"><div className="panel-heading"><div><span className="section-kicker">SOURCE LIBRARY</span><h2>Evidence base</h2></div><label className="upload"><Upload size={15} /> Add<input type="file" accept=".txt,.md,.pdf,.docx" onChange={upload} /></label></div>{documents.length === 0 ? <div className="empty"><FileText size={25} /><p>Your vault is empty</p><span>Drop a document here to begin local indexing.</span></div> : <div className="doc-list">{documents.map((doc) => <div className="doc" key={doc.id}><div className="file-icon"><FileText size={17} /></div><div><strong>{doc.name}</strong><span>{doc.chunks} passages indexed</span></div></div>)}</div>}<div className="privacy-note"><ShieldCheck size={18} /><div><strong>Privacy boundary active</strong><span>PII is replaced with deterministic pseudo-tokens before context reaches a model.</span></div></div></aside></div>
    </section>
  </main>;
}
createRoot(document.getElementById("root")!).render(<App />);
