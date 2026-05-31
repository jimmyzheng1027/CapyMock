"""JD analysis API endpoint."""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agent.llm.factory import LLMFactory
from agent.profile_loader import ProfileLoader
from config.settings import settings

router = APIRouter(tags=["jd-analysis"])


class JdAnalyzeRequest(BaseModel):
    """Request body for JD analysis."""

    text: str = Field(..., min_length=1, description="Job description text")


@router.post("/jd/analyze")
async def analyze_jd(body: JdAnalyzeRequest):
    """Analyze a job description and return structured insights."""
    profile_loader = ProfileLoader("config/agents")
    profile_loader.load_all()
    profile = profile_loader.get("jd-analyzer")

    if not profile:
        raise HTTPException(500, "jd-analyzer profile not found")

    # Load prompt template
    with open(profile.prompt_template, encoding="utf-8") as f:
        prompt = f.read()

    # Create LLM
    llm = LLMFactory.create(
        profile.llm.provider,
        {
            "api_key": settings.get_api_key(profile.llm.provider),
            "model": profile.llm.model,
            "temperature": profile.llm.temperature,
        },
    )

    # Call LLM
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": body.text},
    ]

    result = await llm.chat(messages)

    if result.error:
        raise HTTPException(502, f"LLM error: {result.error}")

    if not result.text:
        raise HTTPException(502, "LLM returned empty response")

    # Parse JSON
    try:
        data = json.loads(result.text)
    except json.JSONDecodeError:
        raise HTTPException(500, f"LLM returned invalid JSON: {result.text[:200]}")

    return data
