from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CopilotIntentEnum(str, Enum):
    STOCKOUT_RISK = "STOCKOUT_RISK"
    OVERSTOCK = "OVERSTOCK"
    SALES_SPIKE = "SALES_SPIKE"
    SALES_DROP = "SALES_DROP"
    SALES_SIGNALS = "SALES_SIGNALS"
    INVENTORY_SUMMARY = "INVENTORY_SUMMARY"
    STORE_ANALYSIS = "STORE_ANALYSIS"
    PRODUCT_ANALYSIS = "PRODUCT_ANALYSIS"
    ACTION_RECOMMENDATION = "ACTION_RECOMMENDATION"
    REVENUE_SUMMARY = "REVENUE_SUMMARY"
    INVENTORY_VALUE = "INVENTORY_VALUE"
    STORE_VALUE_ANALYSIS = "STORE_VALUE_ANALYSIS"
    PRODUCT_VALUE_ANALYSIS = "PRODUCT_VALUE_ANALYSIS"
    CATEGORY_VALUE_ANALYSIS = "CATEGORY_VALUE_ANALYSIS"
    OVERSTOCK_VALUE = "OVERSTOCK_VALUE"
    AMBIGUOUS = "AMBIGUOUS"
    UNKNOWN = "UNKNOWN"


class CopilotResponseStatusEnum(str, Enum):
    ANSWERED = "ANSWERED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"
    NOT_FOUND = "NOT_FOUND"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    ERROR = "ERROR"


class EvidenceQualityEnum(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


class CopilotLimitation(BaseModel):
    type: str  # "MISSING_DATA", "UNSUPPORTED_CAPABILITY", "AMBIGUOUS_QUERY", "UNSUPPORTED_CAUSE", "UNSUPPORTED_QUANTITY"
    message: str
    impact: str


class CopilotIntentFilters(BaseModel):
    store: Optional[str] = None
    category: Optional[str] = None
    product: Optional[str] = None


class CopilotIntentClassification(BaseModel):
    intent: CopilotIntentEnum = CopilotIntentEnum.UNKNOWN
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    filters: CopilotIntentFilters = Field(default_factory=CopilotIntentFilters)
    time_period: Optional[str] = None
    clarification_needed: Optional[str] = None


class CopilotQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500, description="Natural language question from manager")


class CopilotEvidenceRecord(BaseModel):
    product: str
    sku: Optional[str] = None
    category: Optional[str] = None
    store: str
    metric_label: str
    metric_value: str
    status: str
    details: Optional[str] = None


class CopilotQueryResponse(BaseModel):
    status: CopilotResponseStatusEnum = CopilotResponseStatusEnum.ANSWERED
    answer: str
    intent: str
    confidence: float
    evidence_quality: EvidenceQualityEnum = EvidenceQualityEnum.HIGH
    evidence: List[CopilotEvidenceRecord] = Field(default_factory=list)
    insights: List[str] = Field(default_factory=list)
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    limitations: List[CopilotLimitation] = Field(default_factory=list)
    needs_human_review: bool = False
    clarification_question: Optional[str] = None
