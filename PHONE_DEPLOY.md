# Phone-only deployment (easy version)

You do NOT need a computer. You need a GitHub account, a Render account, a Vercel account, and an OpenAI API key.

## A. Put the project on GitHub
1. Download and extract the ZIP on your phone.
2. Open github.com in Chrome and create a new repository named `pdf-question-agent`.
3. Open the repository -> Add file -> Upload files.
4. Upload the CONTENTS of the `pdf-question-agent` folder (not the outer folder itself).
5. Commit changes.

## B. Deploy the backend
1. Open render.com and sign in with GitHub.
2. New + -> Web Service.
3. Select `pdf-question-agent`.
4. Root Directory: `backend`
5. Build Command: `pip install -r requirements.txt`
6. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
7. Add Environment Variable:
   OPENAI_API_KEY = your OpenAI API key
8. Create Web Service.
9. Copy the Render URL, e.g. https://your-app.onrender.com

## C. Deploy the website
1. Open vercel.com and sign in with GitHub.
2. Add New -> Project -> import `pdf-question-agent`.
3. Root Directory: `frontend`
4. Add Environment Variable:
   NEXT_PUBLIC_API_URL = your Render URL
5. Deploy.
6. Open the Vercel URL on your phone.

## D. Use it
Upload the PDF first and wait for "Indexed". Then upload the question image and press "Get Answer".

IMPORTANT:
- Keep the OpenAI key only in Render Environment Variables. Never put it in frontend code or GitHub.
- The demo backend keeps the active PDF index in memory. A backend restart clears it. For a permanent multi-user production app, add a database/object storage/vector DB.
