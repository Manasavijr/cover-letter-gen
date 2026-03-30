"""Document parser — PDF, DOCX, TXT."""
import io, re
from pathlib import Path


def extract_text(content: bytes, filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(content))
        text = "\n".join(p.extract_text() or "" for p in reader.pages)
    elif ext in (".docx", ".doc"):
        import docx
        doc = docx.Document(io.BytesIO(content))
        text = "\n".join(p.text for p in doc.paragraphs)
    else:
        text = content.decode("utf-8", errors="ignore")
    return re.sub(r"\s+", " ", text).strip()


def extract_resume_highlights(resume_text: str) -> dict:
    """Pull key facts from resume for cover letter personalization."""
    text = resume_text
    highlights = {
        "full": text,
        "name": "",
        "years_experience": "",
        "top_skills": [],
        "recent_role": "",
        "recent_company": "",
        "education": "",
        "achievements": [],
    }

    lines = text.split("\n") if "\n" in text else text.split(". ")

    # Try to get name from first non-empty line
    for line in lines[:5]:
        line = line.strip()
        if line and len(line.split()) <= 4 and not any(c in line for c in ["@", "linkedin", "github", "http"]):
            highlights["name"] = line
            break

    # Skills extraction
    tech_skills = ["python", "sql", "machine learning", "deep learning", "pytorch", "tensorflow",
                   "spark", "aws", "gcp", "azure", "docker", "kubernetes", "react", "fastapi",
                   "langchain", "llm", "rag", "data science", "mlops", "tableau", "power bi",
                   "java", "scala", "dbt", "airflow", "kafka", "redis", "mongodb", "postgresql"]
    text_lower = text.lower()
    highlights["top_skills"] = [s for s in tech_skills if s in text_lower][:8]

    # Recent role — look for common job title patterns
    role_patterns = [r"(senior|lead|principal|staff|junior)?\s*(data scientist|ml engineer|software engineer|data engineer|analyst|researcher)",
                     r"(machine learning|ai|data|software|research)\s*(engineer|scientist|analyst)"]
    for pattern in role_patterns:
        match = re.search(pattern, text_lower)
        if match:
            highlights["recent_role"] = match.group().title().strip()
            break

    # Years of experience
    exp_match = re.search(r"(\d+)\+?\s*years?\s*(of\s*)?(experience|exp)", text_lower)
    if exp_match:
        highlights["years_experience"] = exp_match.group(1) + "+ years"

    # Education
    edu_patterns = ["m.s.", "ms ", "m.s ", "b.s.", "bs ", "b.s ", "bachelor", "master", "phd", "ph.d"]
    for line in lines:
        if any(p in line.lower() for p in edu_patterns):
            highlights["education"] = line.strip()[:120]
            break

    # Achievements — lines with numbers/metrics
    for line in lines:
        if re.search(r"\d+[%x]|\$\d+|\d+[KMB]", line):
            clean = line.strip()
            if 20 < len(clean) < 200:
                highlights["achievements"].append(clean)
        if len(highlights["achievements"]) >= 3:
            break

    return highlights


def analyze_jd(jd_text: str) -> dict:
    """Extract key requirements, company name, role, and tone from JD."""
    text_lower = jd_text.lower()

    # Role title — first capitalized line that looks like a title
    role = ""
    for line in jd_text.split("\n")[:10]:
        line = line.strip()
        if 3 < len(line) < 80 and not line.endswith(".") and line[0].isupper():
            role = line
            break

    # Company name heuristic
    company = ""
    company_patterns = [r"at\s+([A-Z][a-zA-Z\s&,\.]+?)[\.,\n]",
                        r"join\s+([A-Z][a-zA-Z\s&,\.]+?)[\.,\n]",
                        r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+is\s+(hiring|looking|seeking)"]
    for p in company_patterns:
        m = re.search(p, jd_text)
        if m:
            company = m.group(1).strip()[:50]
            break

    # Key requirements
    req_keywords = ["required", "requirements", "qualifications", "must have", "you will", "you'll", "responsibilities"]
    requirements = []
    lines = jd_text.split("\n")
    in_req_section = False
    for line in lines:
        line_lower = line.lower().strip()
        if any(k in line_lower for k in req_keywords):
            in_req_section = True
        if in_req_section and (line.strip().startswith("•") or line.strip().startswith("-") or line.strip().startswith("*")):
            clean = line.strip().lstrip("•-* ").strip()
            if len(clean) > 10:
                requirements.append(clean)
        if len(requirements) >= 6:
            break

    # Tone detection
    formal_words = ["leverage", "strategic", "stakeholder", "collaborate", "drive", "optimize"]
    casual_words = ["excited", "passionate", "fun", "awesome", "love", "we're", "you'll"]
    formal_count = sum(1 for w in formal_words if w in text_lower)
    casual_count = sum(1 for w in casual_words if w in text_lower)
    detected_tone = "formal" if formal_count >= casual_count else "conversational"

    return {
        "role": role or "the position",
        "company": company or "your company",
        "requirements": requirements,
        "detected_tone": detected_tone,
        "full": jd_text,
    }
