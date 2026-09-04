from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RecommendationActionEnum(str, Enum):
    REPLENISH_NOW = "REPLENISH_NOW"
    PLAN_REPLENISHMENT = "PLAN_REPLENISHMENT"
    REDUCE_FUTURE_REPLENISHMENT = "REDUCE_FUTURE_REPLENISHMENT"
    REVIEW_INVENTORY = "REVIEW_INVENTORY"
    MONITOR_DEMAND = "MONITOR_DEMAND"
    REVIEW_SALES_SPIKE = "REVIEW_SALES_SPIKE"
    INVESTIGATE_SALES_DECLINE = "INVESTIGATE_SALES_DECLINE"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    NO_ACTION = "NO_ACTION"


class RecommendationPriorityEnum(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    REVIEW = "REVIEW"


class RecommendationItem(BaseModel):
    id: str
    product_id: int
    sku: str
    product_name: str
    category: str
    store_id: int
    store_name: str
    action: RecommendationActionEnum
    priority: RecommendationPriorityEnum
    title: str
    recommendation: str
    reason: str
    evidence_metrics: Dict[str, Any]
    assumptions: List[str]
    needs_human_review: bool = False
    confidence: str = "HIGH"  # "HIGH", "MEDIUM", "REVIEW"


class RecommendationSummary(BaseModel):
    high_priority_count: int
    medium_priority_count: int
    low_priority_count: int
    review_count: int
    total_recommendations: int


class RecommendationResponse(BaseModel):
    generated_at: str
    summary: RecommendationSummary
    results: List[RecommendationItem]


class TodaysAttentionResponse(BaseModel):
    generated_at: str
    count: int
    results: List[RecommendationItem]
