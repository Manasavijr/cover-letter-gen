"""
Cover Letter Generator using LangChain + Ollama.
Supports 4 tones with specific voice/style instructions.
"""
import logging
from typing import List

from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate

from backend.app.core.config import settings

logger = logging.getLogger(__name__)
_llm: OllamaLLM = None

TONE_INSTRUCTIONS = {
    "formal": {
        "label": "Formal",
        "emoji": "🎩",
        "instruction": (
            "Write in a formal, professional tone. Use sophisticated vocabulary. "
            "Avoid contractions (use 'I am' not 'I'm'). Structure sentences carefully. "
            "Project authority and gravitas. Suitable for finance, law, consulting, or senior roles."
        ),
    },
    "confident": {
        "label": "Confident",
        "emoji": "💪",
        "instruction": (
            "Write in a direct, assertive, confident tone. Lead with impact. "
            "Use strong action verbs. Don't hedge or over-qualify. "
            "Show conviction without arrogance. Make bold claims backed by evidence. "
            "Suitable for tech, product, and leadership roles."
        ),
    },
    "casual": {
        "label": "Casual",
        "emoji": "😊",
        "instruction": (
            "Write in a warm, approachable, conversational tone. Contractions are fine. "
            "Sound like a real person, not a robot. Show personality and genuine interest. "
            "Avoid corporate jargon. Be friendly but still professional. "
            "Suitable for startups, creative roles, and culture-first companies."
        ),
    },
    "enthusiastic": {
        "label": "Enthusiastic",
        "emoji": "🚀",
        "instruction": (
            "Write with genuine excitement and passion about the role and company. "
            "Show deep interest in the company's mission. Express authentic enthusiasm. "
            "Use energetic language but avoid being over-the-top or sycophantic. "
            "Make the hiring manager feel your genuine motivation. "
            "Suitable for mission-driven companies, early-stage startups, and roles you truly want."
        ),
    },
}

COVER_LETTER_PROMPT = PromptTemplate(
    input_variables=["name", "role", "company", "tone_instruction", "resume_highlights",
                     "top_matches", "requirements", "years_experience", "achievements", "education"],
    template="""You are an expert career coach and professional writer specializing in cover letters that get interviews.

TONE INSTRUCTION — follow this precisely:
{tone_instruction}

Write a cover letter for:
- Candidate: {name}
- Role: {role}
- Company: {company}

Candidate's background:
- Years of experience: {years_experience}
- Top skills: {resume_highlights}
- Education: {education}
- Key achievements: {achievements}

Most relevant experience for this role (from semantic matching):
{top_matches}

Key job requirements to address:
{requirements}

RULES — strictly follow these:
1. DO NOT use generic openers like "I am writing to express my interest" — start with something specific and compelling
2. DO NOT repeat the same phrases or skills more than once
3. Reference the company by name — show you know who they are
4. Keep it to exactly 3-4 paragraphs, ~300-380 words
5. No bullet points — flowing prose only
6. End with a confident call to action
7. Include [Your Name], [Date], [Phone], [Email] placeholders at top — do not make up real info
8. Address to "Hiring Manager" unless a name is obvious

Return ONLY the cover letter text. No explanations, no preamble, no "Here is your cover letter:"."""
)

REGENERATE_PROMPT = PromptTemplate(
    input_variables=["original_letter", "feedback", "tone_instruction", "role", "company"],
    template="""You are an expert cover letter writer. Rewrite the following cover letter based on specific feedback.

TONE INSTRUCTION — maintain this tone:
{tone_instruction}

Role: {role} at {company}

Feedback to address:
{feedback}

Original cover letter:
{original_letter}

Rewrite it to address the feedback while maintaining quality and tone.
Keep it 3-4 paragraphs, ~300-380 words, no bullet points.
Return ONLY the rewritten cover letter."""
)


def get_llm() -> OllamaLLM:
    global _llm
    if _llm is None:
        _llm = OllamaLLM(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=settings.OLLAMA_TEMPERATURE,
        )
    return _llm


def format_matches(matches: List[dict]) -> str:
    if not matches:
        return "No specific matches found — use general resume highlights."
    return "\n".join(f"- {m['resume_chunk'][:150]}" for m in matches[:5])


def format_requirements(requirements: List[str]) -> str:
    if not requirements:
        return "Use requirements from the job description context."
    return "\n".join(f"- {r}" for r in requirements[:5])


async def generate_cover_letter(
    resume_highlights: dict,
    jd_analysis: dict,
    top_matches: List[dict],
    tone: str = "confident",
) -> str:
    """Generate a personalized cover letter."""
    tone_data = TONE_INSTRUCTIONS.get(tone, TONE_INSTRUCTIONS["confident"])
    llm = get_llm()
    chain = COVER_LETTER_PROMPT | llm

    achievements_str = "\n".join(f"- {a}" for a in resume_highlights.get("achievements", [])[:3]) or "Not specified"
    skills_str = ", ".join(resume_highlights.get("top_skills", [])[:6]) or "Technical professional"

    try:
        result = await chain.ainvoke({
            "name": resume_highlights.get("name") or "the candidate",
            "role": jd_analysis.get("role", "the position"),
            "company": jd_analysis.get("company", "your company"),
            "tone_instruction": tone_data["instruction"],
            "resume_highlights": skills_str,
            "top_matches": format_matches(top_matches),
            "requirements": format_requirements(jd_analysis.get("requirements", [])),
            "years_experience": resume_highlights.get("years_experience") or "several years",
            "achievements": achievements_str,
            "education": resume_highlights.get("education") or "Not specified",
        })
        return str(result).strip()
    except Exception as e:
        logger.error(f"Cover letter generation failed: {e}")
        raise


async def regenerate_with_feedback(
    original_letter: str,
    feedback: str,
    tone: str,
    role: str,
    company: str,
) -> str:
    """Regenerate cover letter based on user feedback."""
    tone_data = TONE_INSTRUCTIONS.get(tone, TONE_INSTRUCTIONS["confident"])
    llm = get_llm()
    chain = REGENERATE_PROMPT | llm
    try:
        result = await chain.ainvoke({
            "original_letter": original_letter,
            "feedback": feedback,
            "tone_instruction": tone_data["instruction"],
            "role": role,
            "company": company,
        })
        return str(result).strip()
    except Exception as e:
        logger.error(f"Regeneration failed: {e}")
        raise
