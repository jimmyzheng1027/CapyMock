"""Tests for JD analysis API endpoint."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from api.app import app


@pytest.fixture
def mock_profile_loader():
    """Mock ProfileLoader that returns a jd-analyzer profile."""
    profile = MagicMock()
    profile.id = "jd-analyzer"
    profile.prompt_template = "data/prompt/jd_analyzer.md"
    profile.llm.provider = "dashscope"
    profile.llm.model = "qwen-max"
    profile.llm.temperature = 0.3
    return profile


@pytest.fixture
def valid_jd_text():
    return """岗位名称：高级前端工程师
工作职责：
1. 负责公司核心产品的前端开发
2. 参与技术方案设计和评审
任职要求：
1. 3年以上前端开发经验
2. 精通 Vue/React
3. 有跨团队协作经验优先"""


@pytest.fixture
def mock_llm_response():
    return {
        "requirements": [
            {"type": "硬性要求", "text": "3年以上前端开发经验"},
            {"type": "硬性要求", "text": "精通 Vue/React"},
            {"type": "软性要求", "text": "有跨团队协作经验优先"},
        ],
        "implicit_expectations": [
            {"text": "需要能独立负责模块，暗示团队可能较小"},
        ],
        "red_flags": [
            {"text": "薪资面议且未写范围，可能预算有限", "severity": "低"},
        ],
        "suggestions": [
            "准备 2-3 个独立负责模块的案例",
            "熟悉该公司的技术栈和产品线",
        ],
    }


class TestJdAnalyzeEndpoint:
    """Tests for POST /api/jd/analyze."""

    @pytest.mark.asyncio
    async def test_analyze_jd_success(
        self, mock_profile_loader, valid_jd_text, mock_llm_response
    ):
        """Successful JD analysis returns four-dimension JSON."""
        mock_llm = MagicMock()
        mock_result = MagicMock()
        mock_result.text = json.dumps(mock_llm_response)
        mock_result.error = None
        mock_llm.chat = AsyncMock(return_value=mock_result)

        with (
            patch("api.jd_analysis.ProfileLoader") as MockLoader,
            patch("api.jd_analysis.LLMFactory.create", return_value=mock_llm),
            patch("builtins.open", MagicMock()),
        ):
            MockLoader.return_value.load_all.return_value = None
            MockLoader.return_value.get.return_value = mock_profile_loader

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/api/jd/analyze", json={"text": valid_jd_text}
                )

        assert resp.status_code == 200
        data = resp.json()
        assert "requirements" in data
        assert "implicit_expectations" in data
        assert "red_flags" in data
        assert "suggestions" in data
        assert len(data["requirements"]) == 3
        assert data["requirements"][0]["type"] == "硬性要求"

    @pytest.mark.asyncio
    async def test_analyze_jd_empty_text(self):
        """Empty text returns 422 (Pydantic validation)."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/jd/analyze", json={"text": ""})

        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_analyze_jd_llm_error(self, mock_profile_loader, valid_jd_text):
        """LLM call failure returns 502."""
        mock_llm = MagicMock()
        mock_result = MagicMock()
        mock_result.text = ""
        mock_result.error = "Rate limit exceeded"
        mock_llm.chat = AsyncMock(return_value=mock_result)

        with (
            patch("api.jd_analysis.ProfileLoader") as MockLoader,
            patch("api.jd_analysis.LLMFactory.create", return_value=mock_llm),
            patch("builtins.open", MagicMock()),
        ):
            MockLoader.return_value.load_all.return_value = None
            MockLoader.return_value.get.return_value = mock_profile_loader

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/api/jd/analyze", json={"text": valid_jd_text}
                )

        assert resp.status_code == 502

    @pytest.mark.asyncio
    async def test_analyze_jd_invalid_json(
        self, mock_profile_loader, valid_jd_text
    ):
        """LLM returning non-JSON returns 500."""
        mock_llm = MagicMock()
        mock_result = MagicMock()
        mock_result.text = "This is not JSON"
        mock_result.error = None
        mock_llm.chat = AsyncMock(return_value=mock_result)

        with (
            patch("api.jd_analysis.ProfileLoader") as MockLoader,
            patch("api.jd_analysis.LLMFactory.create", return_value=mock_llm),
            patch("builtins.open", MagicMock()),
        ):
            MockLoader.return_value.load_all.return_value = None
            MockLoader.return_value.get.return_value = mock_profile_loader

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/api/jd/analyze", json={"text": valid_jd_text}
                )

        assert resp.status_code == 500
