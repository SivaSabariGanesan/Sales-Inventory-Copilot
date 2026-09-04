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
)
from backend.database.schema import init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_copilot_stockout_question():
    """Test stock-out risk query mapping to deterministic analytics."""
    res = CopilotService.process_query("Which products are at risk of running out?")
    assert res.intent == "STOCKOUT_RISK"
    assert len(res.evidence) > 0
    assert any("days" in e.metric_value.lower() for e in res.evidence)
    assert len(res.assumptions) > 0


def test_copilot_overstock_question():
    """Test overstock query mapping to deterministic overstock service."""
    res = CopilotService.process_query("Which products are overstocked or slow moving?")
    assert res.intent == "OVERSTOCK"
    assert len(res.evidence) > 0
    assert any(e.status in ("SEVERE_OVERSTOCK", "OVERSTOCK", "NO_RECENT_DEMAND", "SLOW_MOVING") for e in res.evidence)


def test_copilot_sales_spike_question():
    """Test sales spike query mapping to sales anomaly service."""
    res = CopilotService.process_query("Which products had sales spikes recently?")
    assert res.intent == "SALES_SPIKE"
    assert len(res.assumptions) > 0
    assert "7" in res.assumptions[0] or "sales" in res.assumptions[0].lower()


def test_copilot_sales_drop_question():
    """Test sales drop query mapping to sales anomaly service."""
    res = CopilotService.process_query("Which products are losing sales and dropped?")
    assert res.intent == "SALES_DROP"
    assert len(res.assumptions) > 0


def test_copilot_inventory_summary_question():
    """Test inventory summary query combining stockout and overstock evidence."""
    res = CopilotService.process_query("Give me an overall inventory summary")
    assert res.intent == "INVENTORY_SUMMARY"
    assert len(res.evidence) > 0


def test_copilot_store_specific_query():
    """Test store-specific query resolving Chennai Central."""
    with patch.object(
        GeminiService,
        "classify_intent",
        return_value=CopilotIntentClassification(
            intent=CopilotIntentEnum.STORE_ANALYSIS,
            confidence=0.95,
            filters=CopilotIntentFilters(store="Chennai Central"),
        ),
    ):
        res = CopilotService.process_query("What's happening at Chennai Central?")
        assert res.intent == "STORE_ANALYSIS"
        assert len(res.evidence) > 0
        assert all("Chennai Central" in e.store for e in res.evidence)


def test_copilot_product_specific_query():
    """Test product-specific query resolving product filter."""
    with patch.object(
        GeminiService,
        "classify_intent",
        return_value=CopilotIntentClassification(
            intent=CopilotIntentEnum.PRODUCT_ANALYSIS,
            confidence=0.95,
            filters=CopilotIntentFilters(product="Headphones"),
        ),
    ):
        res = CopilotService.process_query("How are Headphones performing?")
        assert res.intent == "PRODUCT_ANALYSIS"
        assert len(res.evidence) > 0
        assert all("Headphones" in e.product for e in res.evidence)


def test_copilot_unknown_question():
    """Test unknown / forecasting question returns clean limitation."""
    res = CopilotService.process_query("What will our sales be next year?")
    assert res.intent == "UNKNOWN"
    assert res.needs_human_review is True
    assert len(res.limitations) > 0


def test_copilot_ambiguous_question():
    """Test ambiguous question requests clarification."""
    res = CopilotService.process_query("What's happening with stock?")
    assert res.intent == "AMBIGUOUS"
    assert res.needs_human_review is True
    assert "ambiguous" in res.answer.lower() or "clarification" in res.answer.lower() or "stock-out" in res.answer.lower()


def test_copilot_empty_question():
    """Test empty query handling."""
    res = CopilotService.process_query("   ")
    assert res.intent == "UNKNOWN"
    assert "Please provide a question" in res.answer


def test_copilot_unknown_store_resolution():
    """Test unknown store filter returns safe error message."""
    with patch.object(
        GeminiService,
        "classify_intent",
        return_value=CopilotIntentClassification(
            intent=CopilotIntentEnum.STORE_ANALYSIS,
            confidence=0.9,
            filters=CopilotIntentFilters(store="NonExistentStore123"),
        ),
    ):
        res = CopilotService.process_query("Tell me about NonExistentStore123")
        assert res.needs_human_review is True
        assert "couldn't find a store" in res.answer.lower()


def test_copilot_api_endpoint():
    """Test POST /api/copilot/query FastAPI endpoint."""
    response = client.post(
        "/api/copilot/query",
        json={"question": "Which products are at risk of running out?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "intent" in data
    assert "evidence" in data
    assert "insights" in data
    assert "assumptions" in data
    assert isinstance(data["evidence"], list)
