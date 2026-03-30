"""Unit tests for Cover Letter Generator API."""
import os
from unittest.mock import MagicMock, patch
import pytest

os.environ.setdefault("DEBUG", "true")

SAMPLE_RESUME = b"""
Manasa Vijayaraghavan | manasa@email.com
USC MS Applied Data Science | GPA 3.9

SUMMARY
Data scientist with 2+ years of experience in ML, NLP, and data engineering.

EXPERIENCE
ML Engineer Intern, Ford Motor Company (2023)
- Built multimodal emotion detection system with 87% accuracy using PyTorch and OpenCV
- Processed 500K+ sensor records using PySpark on Azure

Data Science Intern, iNextLabs (2022)
- Developed AI chatbot on Microsoft Azure, reducing support tickets by 35%
- Fine-tuned LLMs using LoRA for domain adaptation

SKILLS
Python, PyTorch, TensorFlow, PySpark, LangChain, FAISS, SQL, Azure, GCP, Docker

EDUCATION
M.S. Applied Data Science, USC, 2027 (GPA 3.9)
B.Tech Computer Science, 2023
"""

SAMPLE_JD = b"""
Senior Machine Learning Engineer — Google DeepMind

We are looking for a passionate ML engineer to join our team.

Requirements:
- 3+ years experience with Python and PyTorch or TensorFlow
- Experience with LLMs, RAG, and vector databases
- Strong MLOps and model deployment experience
- Cloud platforms: GCP or AWS
- Experience with distributed computing (Spark, Dask)
"""


@pytest.fixture
def client():
    with patch("backend.ml.matcher.get_model"):
        from backend.app.main import app
        from fastapi.testclient import TestClient
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c


def test_liveness(client):
    r = client.get("/health/live")
    assert r.status_code == 200
    assert r.json()["status"] == "alive"


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "endpoints" in r.json()


def test_get_tones(client):
    r = client.get("/api/v1/tones")
    assert r.status_code == 200
    data = r.json()
    assert "formal" in data
    assert "confident" in data
    assert "casual" in data
    assert "enthusiastic" in data


def test_parser_extract_text():
    from backend.ml.parser import extract_text
    text = extract_text(b"Hello world resume.", "resume.txt")
    assert "Hello world" in text


def test_parser_resume_highlights():
    from backend.ml.parser import extract_resume_highlights
    h = extract_resume_highlights(SAMPLE_RESUME.decode())
    assert "full" in h
    assert isinstance(h["top_skills"], list)


def test_parser_analyze_jd():
    from backend.ml.parser import analyze_jd
    jd = analyze_jd(SAMPLE_JD.decode())
    assert "role" in jd
    assert "company" in jd
    assert "requirements" in jd
    assert isinstance(jd["requirements"], list)


def test_matcher_chunk_text():
    from backend.ml.matcher import chunk_text
    chunks = chunk_text("Hello world. This is a test. Building ML models with PyTorch.")
    assert len(chunks) > 0
    assert all(isinstance(c, str) for c in chunks)


@patch("backend.ml.matcher.get_model")
def test_find_top_matches(mock_model):
    from backend.ml.matcher import find_top_matches
    import numpy as np
    m = MagicMock()
    m.encode.return_value = np.random.rand(10, 384).astype(np.float32)
    mock_model.return_value = m
    matches = find_top_matches(SAMPLE_JD.decode(), SAMPLE_RESUME.decode(), top_k=5)
    assert isinstance(matches, list)


def test_tone_instructions():
    from backend.ml.generator import TONE_INSTRUCTIONS
    assert len(TONE_INSTRUCTIONS) == 4
    for key, val in TONE_INSTRUCTIONS.items():
        assert "label" in val
        assert "emoji" in val
        assert "instruction" in val
        assert len(val["instruction"]) > 50  # not generic
