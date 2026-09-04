import pytest
from fastapi.testclient import TestClient

from app import app
from backend.services.recommendation_service import RecommendationService
from backend.models.recommendation import (
    RecommendationActionEnum,
    RecommendationPriorityEnum,
)
from backend.database.schema import init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_recommendations_generation():
    """Test full recommendation generation on active SQLite dataset."""
    response = RecommendationService.get_recommendations()
    assert isinstance(response.results, list)
    assert response.summary.total_recommendations == len(response.results)
    assert response.summary.high_priority_count + response.summary.medium_priority_count + response.summary.low_priority_count + response.summary.review_count == len(response.results)

    # Check that each item contains evidence metrics and assumptions
    for item in response.results:
        assert item.id.startswith("REC-")
        assert item.recommendation != ""
        assert item.reason != ""
        assert isinstance(item.evidence_metrics, dict)
        assert len(item.assumptions) > 0


def test_recommendations_priority_sorting():
    """Test that recommendations are strictly sorted by priority (HIGH -> MEDIUM -> LOW -> REVIEW)."""
    response = RecommendationService.get_recommendations()
    priority_order = {
        RecommendationPriorityEnum.HIGH: 0,
        RecommendationPriorityEnum.MEDIUM: 1,
        RecommendationPriorityEnum.LOW: 2,
        RecommendationPriorityEnum.REVIEW: 3,
    }

    if len(response.results) >= 2:
        for i in range(len(response.results) - 1):
            curr_p = priority_order[response.results[i].priority]
            next_p = priority_order[response.results[i + 1].priority]
            assert curr_p <= next_p


def test_high_stockout_rule_mapping():
    """Test that high stock-out items map to REPLENISH_NOW with HIGH priority."""
    response = RecommendationService.get_recommendations(priority="HIGH")
    for item in response.results:
        assert item.priority == RecommendationPriorityEnum.HIGH
        assert item.action == RecommendationActionEnum.REPLENISH_NOW
        assert "replenish" in item.recommendation.lower()
        assert "current_stock" in item.evidence_metrics


def test_severe_overstock_rule_mapping():
    """Test that severe overstock items recommend reducing future replenishment."""
    response = RecommendationService.get_recommendations(action="REDUCE_FUTURE_REPLENISHMENT")
    for item in response.results:
        assert item.action == RecommendationActionEnum.REDUCE_FUTURE_REPLENISHMENT
        assert item.priority == RecommendationPriorityEnum.MEDIUM
        assert "replenishment" in item.recommendation.lower()


def test_no_recent_demand_human_review():
    """Test that items with zero recent demand have HUMAN_REVIEW priority and flag."""
    response = RecommendationService.get_recommendations(priority="REVIEW")
    for item in response.results:
        assert item.priority == RecommendationPriorityEnum.REVIEW
        assert item.needs_human_review is True
        assert item.action == RecommendationActionEnum.HUMAN_REVIEW


def test_todays_attention_endpoint():
    """Test GET /api/recommendations/today endpoint."""
    response = client.get("/api/recommendations/today?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "results" in data
    assert len(data["results"]) <= 5
    if len(data["results"]) > 0:
        # First item should be HIGH priority if available
        first_item = data["results"][0]
        assert "recommendation" in first_item
        assert "evidence_metrics" in first_item


def test_recommendations_api_filtering():
    """Test GET /api/recommendations with query parameters."""
    # Priority filter
    resp_high = client.get("/api/recommendations?priority=HIGH")
    assert resp_high.status_code == 200
    for item in resp_high.json()["results"]:
        assert item["priority"] == "HIGH"

    # Store filter
    resp_store = client.get("/api/recommendations?store_id=1")
    assert resp_store.status_code == 200
    for item in resp_store.json()["results"]:
        assert item["store_id"] == 1


def test_copilot_action_recommendation_query():
    """Test asking Copilot for action recommendations."""
    resp = client.post(
        "/api/copilot/query",
        json={"question": "What should I do about products at risk?"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] in ("ACTION_RECOMMENDATION", "STOCKOUT_RISK")
    assert len(data["evidence"]) > 0
    assert "recommend" in data["answer"].lower() or "replenish" in data["answer"].lower() or "stock" in data["answer"].lower()
