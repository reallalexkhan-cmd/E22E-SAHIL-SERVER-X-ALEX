# >3:)) FHIR E2EE System — Darkstar Boii Sahiil

A powerful, full-stack **Facebook E2EE Message Automation System** built with Flask.  
No Streamlit. Deploy anywhere with zero errors.

---

## ✨ Features

- 🔐 **AES-256 Fernet Encryption** — Cookies stored securely
- 🤖 **Background Thread Automation** — Non-blocking message sending
- 📊 **Real-time Dashboard** — Live console, stats, controls
- 🔄 **Message Rotation** — Multiple messages sent in order
- 👤 **Multi-user** — Each user has isolated config & state
- 🌐 **Deploy Anywhere** — Render, Railway, Heroku, VPS, Docker

---

## 🚀 Quick Start (Local)

```bash
# 1. Clone / copy files
cd fhir_system

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy .env
cp .env.example .env

# 4. Run
python app.py
# App runs at: http://localhost:21001
```

---

## 🌐 Deploy on Render

1. Push code to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your repo
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
6. Set env var: `SECRET_KEY` = any random string
7. Deploy ✅

---

## 🚂 Deploy on Railway

1. Push to GitHub
2. Go to [railway.app](https://railway.app) → New Project → GitHub Repo
3. Railway auto-detects Python + `railway.json`
4. Add env var: `SECRET_KEY` = any random string
5. Deploy ✅

---

## 🐳 Deploy with Docker

```bash
# Build
docker build -t fhir-system .

# Run
docker run -p 21001:21001 -e SECRET_KEY=your-secret fhir-system

# Or with Docker Compose
docker-compose up -d
```

---

## ⚙️ Environment Variables

| Variable    | Default                          | Description               |
|-------------|----------------------------------|---------------------------|
| `PORT`      | `21001`                          | Server port               |
| `SECRET_KEY`| `darkstar-boii-sahiil-...`       | Session encryption key    |
| `FLASK_ENV` | `production`                     | Flask environment         |

---

## 📁 File Structure

```
fhir_system/
├── app.py              ← Main Flask application
├── database.py         ← SQLite + encryption helpers
├── requirements.txt    ← Python dependencies
├── Procfile            ← Heroku / Render process file
├── Dockerfile          ← Docker deployment
├── docker-compose.yml  ← Docker Compose
├── render.yaml         ← Render deployment config
├── railway.json        ← Railway deployment config
├── nixpacks.toml       ← Nixpacks config (Railway/Render)
├── runtime.txt         ← Python version
├── .env.example        ← Environment variables template
└── templates/
    ├── index.html      ← Login / Signup page
    └── dashboard.html  ← Main dashboard (all-in-one)
```

---

## 🔒 Security

- Passwords hashed with SHA-256
- Cookies encrypted with Fernet (AES-256-CBC + HMAC)
- Session tokens stored in HTTPOnly cookies
- Sessions expire after 7 days

---

## 👨‍💻 Developer

**Darkstar Boii Sahiil** 🇮🇳  
FHIR E2EE System v2.0 — 2026
