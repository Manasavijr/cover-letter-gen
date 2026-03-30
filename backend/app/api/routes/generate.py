"""Core cover letter generation endpoints."""
import logging
import time

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.schemas.schemas import CoverLetterResponse, RegenerateRequest
from backend.ml.generator import (
    TONE_INSTRUCTIONS, generate_cover_letter, regenerate_with_feedback
)
from backend.ml.matcher import compute_match_score, find_top_matches
from backend.ml.parser import analyze_jd, extract_resume_highlights, extract_text

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate", response_model=CoverLetterResponse)
async def generate(
    resume: UploadFile = File(...),
    job_description: UploadFile = File(...),
    tone: str = Form(default="confident"),
    job_title: str = Form(default=""),
    company: str = Form(default=""),
):
    """
    Generate a personalized cover letter.
    1. Parse resume + JD
    2. FAISS semantic matching
    3. LangChain + Ollama generation with tone control
    4. Score cover letter against JD
    """
    t0 = time.perf_counter()

    if tone not in TONE_INSTRUCTIONS:
        raise HTTPException(status_code=400, detail=f"Invalid tone. Choose from: {list(TONE_INSTRUCTIONS.keys())}")

    resume_content = await resume.read()
    jd_content = await job_description.read()

    resume_text = extract_text(resume_content, resume.filename or "resume.txt")
    jd_text = extract_text(jd_content, job_description.filename or "jd.txt")

    if not resume_text:
        raise HTTPException(status_code=400, detail="Could not extract text from resume.")
    if not jd_text:
        raise HTTPException(status_code=400, detail="Could not extract text from job description.")

    # Parse
    resume_highlights = extract_resume_highlights(resume_text)
    jd_analysis = analyze_jd(jd_text)

    # Override with user inputs if provided
    if job_title:
        jd_analysis["role"] = job_title
    if company:
        jd_analysis["company"] = company

    # FAISS matching
    logger.info("Running FAISS semantic matching...")
    top_matches = find_top_matches(jd_text, resume_text)

    # Generate
    logger.info(f"Generating cover letter (tone={tone})...")
    try:
        cover_letter = await generate_cover_letter(resume_highlights, jd_analysis, top_matches, tone)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"LLM generation failed: {str(e)}")

    # Score
    match_score = compute_match_score(jd_text, cover_letter)
    latency = (time.perf_counter() - t0) * 1000
    tone_data = TONE_INSTRUCTIONS[tone]

    return CoverLetterResponse(
        cover_letter=cover_letter,
        match_score=match_score,
        tone_used=tone,
        tone_label=tone_data["label"],
        tone_emoji=tone_data["emoji"],
        top_matches=top_matches[:5],
        jd_role=jd_analysis["role"],
        jd_company=jd_analysis["company"],
        candidate_name=resume_highlights.get("name", ""),
        model_used=settings.OLLAMA_MODEL,
        latency_ms=round(latency, 2),
    )


@router.post("/regenerate")
async def regenerate(req: RegenerateRequest):
    """Regenerate cover letter based on user feedback."""
    if req.tone not in TONE_INSTRUCTIONS:
        raise HTTPException(status_code=400, detail="Invalid tone.")
    t0 = time.perf_counter()
    try:
        letter = await regenerate_with_feedback(
            req.original_letter, req.feedback, req.tone, req.role, req.company
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
    latency = (time.perf_counter() - t0) * 1000
    tone_data = TONE_INSTRUCTIONS[req.tone]
    return {
        "cover_letter": letter,
        "tone_used": req.tone,
        "tone_label": tone_data["label"],
        "tone_emoji": tone_data["emoji"],
        "latency_ms": round(latency, 2),
    }


@router.get("/tones")
async def get_tones():
    """Return available tone options."""
    return {
        k: {"label": v["label"], "emoji": v["emoji"]}
        for k, v in TONE_INSTRUCTIONS.items()
    }
