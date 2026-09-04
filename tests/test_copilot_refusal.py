import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app import app
from backend.services.copilot_service import CopilotService
from backend.services.gemini_service import GeminiService
from backend.models.copilot import (
    CopilotIntentEnum,
    CopilotIntentClassification,
    CopilotIntentFilters,
    CopilotResponseStatusEnum,
    EvidenceQualityEnum,
)
from backend.database.schema import init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_missing_product_not_found():
    """Test asking about a non-existent product returns NOT_FOUND."""
    with patch.object(
        GeminiService,
        "classify_intent",
        return_value=CopilotIntentClassification(
            intent=CopilotIntentEnum.PRODUCT_ANALYSIS,
            confidence=0.9,
            filters=CopilotIntentFilters(product="NonExistentSKU9999"),
        ),
    ):
        res = CopilotService.process_query("How is NonExistentSKU9999 doing?")
        assert res.status == CopilotResponseStatusEnum.NOT_FOUND
        assert res.needs_human_review is True
        assert res.evidence_quality == EvidenceQualityEnum.NONE
        assert len(res.limitations) > 0
        assert res.limitations[0].type == "MISSING_DATA"


def test_missing_store_not_found():
    """Test asking about a non-existent store returns NOT_FOUND."""
    with patch.object(
        GeminiService,
        "classify_intent",
        return_value=CopilotIntentClassification(
            intent=CopilotIntentEnum.STORE_ANALYSIS,
            confidence=0.9,
            filters=CopilotIntentFilters(store="Mumbai Central"),
        ),
    ):
        res = CopilotService.process_query("What's happening at Mumbai Central?")
        assert res.status == CopilotResponseStatusEnum.NOT_FOUND
        assert res.needs_human_review is True
        assert "Mumbai Central" in res.answer


def test_ambiguous_question_handling():
    """Test ambiguous question returns AMBIGUOUS status with clarification."""
    res = CopilotService.process_query("What's happening with stock?")
    assert res.status == CopilotResponseStatusEnum.AMBIGUOUS
    assert res.needs_human_review is True
    assert res.clarification_question is not None
    assert "stock-out" in res.clarification_question.lower() or "overstock" in res.clarification_question.lower()


def test_unsupported_forecasting_refusal():
    """Test forecasting queries return UNSUPPORTED with clear limitation."""
    res = CopilotService.process_query("What will our revenue be next year?")
    assert res.status == CopilotResponseStatusEnum.UNSUPPORTED
    assert res.needs_human_review is True
    assert res.evidence_quality == EvidenceQualityEnum.NONE
    assert len(res.limitations) > 0
    assert res.limitations[0].type == "UNSUPPORTED_CAPABILITY"
    assert "forecast" in res.answer.lower()


def test_unsupported_exact_ordering_quantity():
    """Test exact order quantity inquiry escalates to HUMAN_REVIEW."""
    res = CopilotService.process_query("How many units should I order for Wireless Mouse?")
    assert res.status == CopilotResponseStatusEnum.HUMAN_REVIEW
    assert res.needs_human_review is True
    assert len(res.limitations) > 0
    assert any("lead time" in lim.message.lower() or "moq" in lim.message.lower() for lim in res.limitations)


def test_root_cause_inquiry_human_review():
    """Test asking 'Why did sales drop?' reports factual numbers but refuses cause attribution."""
    res = CopilotService.process_query("Why did sales drop recently?")
    assert res.status == CopilotResponseStatusEnum.HUMAN_REVIEW
    assert res.needs_human_review is True
    assert len(res.limitations) > 0
    assert any("external" in lim.message.lower() or "cause" in lim.message.lower() for lim in res.limitations)


def test_zero_sales_valid_demand_is_answered():
    """Test that zero sales over a complete window is NO_RECENT_DEMAND (ANSWERED), not INSUFFICIENT_DATA."""
    res = CopilotService.process_query("What inventory has no recent demand?")
    assert res.status == CopilotResponseStatusEnum.ANSWERED
    assert res.evidence_quality == EvidenceQualityEnum.HIGH
    assert len(res.evidence) > 0


def test_empty_query_refusal():
    """Test empty query returns INSUFFICIENT_DATA with zero evidence."""
    res = CopilotService.process_query("   ")
    assert res.status == CopilotResponseStatusEnum.INSUFFICIENT_DATA
    assert res.evidence_quality == EvidenceQualityEnum.NONE
    assert len(res.evidence) == 0


def test_api_endpoint_response_structure():
    """Test that POST /api/copilot/query includes status, evidence_quality, and limitations."""
    response = client.post(
        "/api/copilot/query",
        json={"question": "What will sales be next year?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UNSUPPORTED"
    assert data["evidence_quality"] == "NONE"
    assert data["needs_human_review"] is True
    assert isinstance(data["limitations"], list)
    assert len(data["limitations"]) > 0
