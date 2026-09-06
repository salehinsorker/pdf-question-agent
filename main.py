import os, base64, uuid, re
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    print("WARNING: OPENAI_API_KEY is not set.")
client = OpenAI(api_key=API_KEY) if API_KEY else None

app = FastAPI(title="PDF Question Agent API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Single active PDF per server process, suitable for a personal/demo app.
state = {"pdf_name": None, "chunks": [], "vectorizer": None, "matrix": None}

def chunk_page(text: str, page: int, size: int = 1400, overlap: int = 220):
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    out, start = [], 0
    while start < len(text):
        end = min(len(text), start + size)
        part = text[start:end].strip()
        if part:
            out.append({"text": part, "page": page})
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return out

@app.get("/api/health")
def health():
    return {"ok": True, "pdf_loaded": bool(state["chunks"]), "pdf_name": state["pdf_name"]}

@app.post("/api/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Please upload a PDF file.")
    data = await file.read()
    if len(data) > 25 * 1024 * 1024:
        raise HTTPException(413, "PDF is too large. Maximum is 25 MB.")
    path = UPLOAD_DIR / f"{uuid.uuid4()}.pdf"
    path.write_bytes(data)
    try:
        reader = PdfReader(str(path))
        chunks = []
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            chunks.extend(chunk_page(text, i))
        if not chunks:
            raise HTTPException(422, "No readable text was found. This may be a scanned PDF; OCR is needed.")
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1,2), max_features=50000)
        matrix = vectorizer.fit_transform([c["text"] for c in chunks])
        state.update({"pdf_name": file.filename, "chunks": chunks, "vectorizer": vectorizer, "matrix": matrix})
        return {"message": "PDF indexed successfully.", "filename": file.filename, "pages": len(reader.pages), "chunks": len(chunks)}
    finally:
        try: path.unlink()
        except Exception: pass

async def read_image(file: UploadFile):
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, "Image is too large. Maximum is 10 MB.")
    mime = file.content_type or "image/jpeg"
    if mime not in {"image/jpeg","image/png","image/webp","image/gif"}:
        raise HTTPException(400, "Please upload JPG, PNG, WEBP, or GIF.")
    return mime, content

def retrieve(question: str, k=5):
    if not state["chunks"]:
        raise HTTPException(400, "Upload a PDF first.")
    qv = state["vectorizer"].transform([question])
    scores = cosine_similarity(qv, state["matrix"]).ravel()
    idx = scores.argsort()[::-1][:k]
    return [{"page": state["chunks"][i]["page"], "text": state["chunks"][i]["text"], "score": float(scores[i])} for i in idx]

def vision_extract(mime, data):
    if not client:
        raise HTTPException(500, "OPENAI_API_KEY is not configured.")
    b64 = base64.b64encode(data).decode()
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_VISION_MODEL","gpt-4o-mini"),
        temperature=0,
        messages=[{
            "role":"user",
            "content":[
                {"type":"text","text":"Read this question image exactly. Return only the question text, including answer choices if present. Do not answer it."},
                {"type":"image_url","image_url":{"url":f"data:{mime};base64,{b64}"}}
            ]
        }]
    )
    return resp.choices[0].message.content.strip()

@app.post("/api/ask-image")
async def ask_image(file: UploadFile = File(...)):
    mime, data = await read_image(file)
    question = vision_extract(mime, data)
    sources = retrieve(question, 6)
    context = "\n\n".join([f"[PDF page {s['page']}]\n{s['text']}" for s in sources])
    prompt = f"""You are a document question-answering assistant.
Answer the user's question using ONLY the provided PDF context.
If the context does not contain enough information, say: "I couldn't find enough information in the uploaded PDF."
Do not invent facts. If it is an MCQ, give the selected option and a concise explanation.
Mention the relevant PDF page number(s).

QUESTION:
{question}

PDF CONTEXT:
{context}
"""
    if not client:
        raise HTTPException(500, "OPENAI_API_KEY is not configured.")
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_ANSWER_MODEL","gpt-4o-mini"),
        temperature=0.1,
        messages=[
            {"role":"system","content":"You answer strictly from supplied document context."},
            {"role":"user","content":prompt}
        ]
    )
    answer = resp.choices[0].message.content.strip()
    return {
        "question": question,
        "answer": answer,
        "sources": [{"page": s["page"], "text": s["text"][:500]} for s in sources if s["score"] > 0]
    }
