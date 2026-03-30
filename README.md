# AI Cover Letter Generator

GenAI product that generates personalized, ATS-optimized cover letters using LangChain + Ollama (llama3.2) and FAISS semantic matching — 100% local, no API keys.

---

## Features

- **4 tone styles** — Formal 🎩, Confident 💪, Casual 😊, Enthusiastic 🚀 — each with distinct voice instructions
- **FAISS semantic matching** — finds resume experience most relevant to the JD
- **JD analysis** — extracts role, company, requirements, and detected tone
- **Regenerate with feedback** — quick chips + custom text to refine the letter
- **Editable output** — full textarea to make manual adjustments
- **PDF export** — formatted preview with download
- **JD match score** — semantic similarity ring chart

---

## Architecture

```
Resume + JD
    ↓
FAISS Semantic Matching (top-8 resume↔JD pairs)
    ↓
JD Analysis (role, company, requirements, tone)
    ↓
LangChain Prompt + Ollama (llama3.2)
    → tone-specific voice instructions
    → personalized 300-380 word letter
    ↓
Match Score (FAISS cover letter ↔ JD)
    ↓
React UI: Edit → Regenerate → PDF
```

---

## Tech Stack

| Component | Technology |
|---|---|
| LLM | Ollama llama3.2 (local) |
| Orchestration | LangChain |
| Semantic Matching | FAISS + sentence-transformers |
| Backend | FastAPI + Uvicorn |
| Frontend | React 18 |
| Parsing | PyPDF, python-docx |

---

## Setup

**Terminal 1 — Ollama:**
```bash
ollama serve
# ollama pull llama3.2  (if not already pulled)
```

**Terminal 2 — Backend:**
```bash
cd cover-letter-gen/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd ..
uvicorn backend.app.main:app --reload --port 8081
```

**Terminal 3 — Frontend:**
```bash
cd cover-letter-gen/frontend
npm install && npm start  # opens http://localhost:3001
```

---

## API

```bash
# Generate cover letter
curl -X POST http://localhost:8081/api/v1/generate \
  -F "resume=@resume.pdf" \
  -F "job_description=@jd.txt" \
  -F "tone=confident" \
  -F "job_title=ML Engineer" \
  -F "company=Google"

# Regenerate with feedback
curl -X POST http://localhost:8081/api/v1/regenerate \
  -H "Content-Type: application/json" \
  -d '{"original_letter":"...", "feedback":"Make it shorter", "tone":"formal", "role":"ML Engineer", "company":"Google"}'

# Available tones
curl http://localhost:8081/api/v1/tones
```

---

## Tests

```bash
pytest tests/ -v
```
