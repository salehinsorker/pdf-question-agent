# PDF Question Agent

A website that lets you upload one PDF as the source, upload a question image, extract the question with a vision model, retrieve relevant PDF passages, and generate an answer with source pages.

## Requirements
- Node.js 20+
- Python 3.10+
- An OpenAI API key

## 1. Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# put your OPENAI_API_KEY in .env
uvicorn main:app --reload --port 8000
```

## 2. Frontend
In another terminal:
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

The frontend expects the backend at `http://localhost:8000`. You can override it with:
`NEXT_PUBLIC_API_URL=http://localhost:8000`

## How it works
1. Upload a PDF. The backend extracts text page-by-page and builds a local TF-IDF retrieval index.
2. Upload a question image.
3. The vision model reads the image.
4. The backend retrieves relevant PDF passages and asks the model to answer only from those passages.
5. The UI shows the answer, extracted question, and source pages.

## Notes
- This version intentionally uses a simple local TF-IDF index, so there is no separate vector database to configure.
- Scanned/image-only PDFs need OCR support to extract their text. This starter version detects when extracted text is too sparse and reports that OCR is needed.
- For production, add authentication, persistent storage, rate limiting, file-size limits, HTTPS, and a persistent vector database.
