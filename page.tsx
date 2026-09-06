 "use client";
import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home(){
  const [pdf,setPdf]=useState<File|null>(null);
  const [img,setImg]=useState<File|null>(null);
  const [pdfStatus,setPdfStatus]=useState("");
  const [loading,setLoading]=useState(false);
  const [result,setResult]=useState<any>(null);
  const [error,setError]=useState("");

  async function uploadPDF(){
    if(!pdf) return;
    setError(""); setPdfStatus("Indexing PDF...");
    const fd=new FormData(); fd.append("file",pdf);
    try{
      const r=await fetch(`${API}/api/upload-pdf`,{method:"POST",body:fd});
      const d=await r.json(); if(!r.ok) throw new Error(d.detail||"Upload failed");
      setPdfStatus(`✓ ${d.filename} — ${d.pages} pages indexed`);
    }catch(e:any){setPdfStatus("");setError(e.message)}
  }
  async function ask(){
    if(!img){setError("Please select a question image.");return}
    setError("");setResult(null);setLoading(true);
    const fd=new FormData(); fd.append("file",img);
    try{
      const r=await fetch(`${API}/api/ask-image`,{method:"POST",body:fd});
      const d=await r.json(); if(!r.ok) throw new Error(d.detail||"Something went wrong");
      setResult(d);
    }catch(e:any){setError(e.message)}finally{setLoading(false)}
  }
  return <main>
    <header><div className="brand"><span className="logo">⌁</span><div><b>PDF Question Agent</b><small>AI answers from your document</small></div></div><span className="pill">RAG + Vision</span></header>
    <section className="hero"><div className="badge">DOCUMENT Q&A</div><h1>Ask your PDF<br/><em>anything.</em></h1><p>Upload your study material, then send a photo of a question. The agent reads the image and answers from your PDF.</p></section>
    <section className="grid">
      <div className="card"><div className="step">01</div><h2>Upload source PDF</h2><p className="muted">Your PDF becomes the agent's knowledge base.</p>
        <label className="drop"><input type="file" accept=".pdf" onChange={e=>setPdf(e.target.files?.[0]||null)}/><span className="icon">📄</span><strong>{pdf?pdf.name:"Choose a PDF"}</strong><small>PDF up to 25 MB</small></label>
        <button onClick={uploadPDF} disabled={!pdf} className="btn">{pdfStatus?"Indexed ✓":"Index PDF →"}</button>
        {pdfStatus&&<div className="success">{pdfStatus}</div>}
      </div>
      <div className="card"><div className="step">02</div><h2>Upload question image</h2><p className="muted">Take a photo or upload a screenshot of the question.</p>
        <label className="drop"><input type="file" accept="image/*" onChange={e=>setImg(e.target.files?.[0]||null)}/><span className="icon">🖼️</span><strong>{img?img.name:"Choose question image"}</strong><small>JPG, PNG, WEBP up to 10 MB</small></label>
        <button onClick={ask} disabled={!img||loading} className="btn">{loading?"Thinking...":"Get Answer →"}</button>
      </div>
    </section>
    {error&&<div className="error">{error}</div>}
    {result&&<section className="answer"><div className="answerTop"><span className="badge">ANSWER</span><span>Source-grounded</span></div><h3>Extracted question</h3><div className="question">{result.question}</div><h3>Answer</h3><div className="answerText">{result.answer}</div><h3>Relevant PDF pages</h3><div className="sources">{result.sources.map((s:any,i:number)=><div className="source" key={i}><b>Page {s.page}</b><span>{s.text}</span></div>)}</div></section>}
    <footer>Built for study notes, textbooks, manuals and document-based Q&A.</footer>
  </main>
}