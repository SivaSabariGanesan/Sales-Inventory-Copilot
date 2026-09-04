from typing import Optional, List, Dict, Any, Tuple
import logging

from backend.database.connection import get_db_connection
from backend.models.copilot import (
    CopilotIntentEnum,
    CopilotIntentClassification,
    CopilotResponseStatusEnum,
    EvidenceQualityEnum,
    CopilotLimitation,
    CopilotQueryResponse,
    CopilotEvidenceRecord,
)
from backend.services.gemini_service import GeminiService
from backend.services.inventory_risk_service import InventoryRiskService
from backend.services.overstock_service import OverstockService
from backend.services.sales_anomaly_service import SalesAnomalyService
from backend.services.recommendation_service import RecommendationService
from backend.services.version_service import DataVersionService
from backend.services.cache_service import CopilotCacheService
from backend.services.audit_service import AuditService
from backend.services.value_analytics_service import ValueAnalyticsService

logger = logging.getLogger("retail_copilot.copilot_service")


class CopilotService:
    """Orchestrator for natural language Copilot queries with pre-Gemini validation, caching, and audit trail."""

    @classmethod
    def process_query(cls, question: str, user_id: Optional[str] = None) -> CopilotQueryResponse:
        """
        Processes a natural-language manager question with deterministic pre-validation,
        strict refusal of unsupported capabilities, safe application caching, and audit logging.
        """
        clean_q = (question or "").strip()
        normalized_q = " ".join(clean_q.lower().split())

        data_version = DataVersionService.get_data_version()
        prompt_version = GeminiService.PROMPT_VERSION
        model = GeminiService.get_active_model()
        cache_key = CopilotCacheService.generate_cache_key(prompt_version, model, normalized_q, data_version)

        # 0. Check Safe Application & Prompt Cache
        if clean_q:
            cached_data = CopilotCacheService.get_cached_response(cache_key, data_version)
            if cached_data:
                cached_resp_dict, cached_calls, cached_in_tok, cached_out_tok = cached_data
                logger.info(f"Safe cache HIT for query: '{clean_q}' (data_version={data_version})")
                
                cached_response = CopilotQueryResponse.model_validate(cached_resp_dict)
                
                # Non-blocking audit log of cache hit
                AuditService.log_copilot_interaction(
                    question=clean_q,
                    normalized_question=normalized_q,
                    intent=cached_response.intent,
                    confidence=cached_response.confidence,
                    status=cached_response.status.value,
                    cache_hit=True,
                    cache_key=cache_key,
                    gemini_calls=0,
                    input_tokens=0,
                    output_tokens=0,
                    prompt_version=prompt_version,
                    model=model,
                    data_version=data_version,
                    user_id=user_id,
                    action_recommendation=cached_response.recommendations[0].get("recommendation") if cached_response.recommendations else None,
                    needs_human_review=cached_response.needs_human_review,
                    execution_steps=[
                        {"step_name": "Cache Verification", "status": "CACHE_HIT", "details": {"cache_key": cache_key, "data_version": data_version}}
                    ],
                )
                return cached_response

        # Initialize telemetry & execution step trail
        gemini_calls_total = 0
        input_tokens_total = 0
        output_tokens_total = 0
        execution_steps: List[Dict[str, Any]] = [
            {
                "step_name": "Input Normalization",
                "status": "COMPLETED",
                "details": {"normalized_question": normalized_q, "data_version": data_version},
            }
        ]

        if not clean_q:
            resp = CopilotQueryResponse(
                status=CopilotResponseStatusEnum.INSUFFICIENT_DATA,
                answer="Please provide a question about sales, inventory, or store performance.",
                intent=CopilotIntentEnum.UNKNOWN.value,
                confidence=1.0,
                evidence_quality=EvidenceQualityEnum.NONE,
                evidence=[],
                insights=[],
                recommendations=[],
                assumptions=[],
                limitations=[
                    CopilotLimitation(
                        type="MISSING_DATA",
                        message="Empty query received.",
                        impact="No analysis could be performed.",
                    )
                ],
                needs_human_review=False,
                clarification_question=None,
            )
            AuditService.log_copilot_interaction(
                question=clean_q,
                normalized_question=normalized_q,
                intent=resp.intent,
                confidence=resp.confidence,
                status=resp.status.value,
                cache_hit=False,
                cache_key=cache_key,
                gemini_calls=0,
                input_tokens=0,
                output_tokens=0,
                prompt_version=prompt_version,
                model=model,
                data_version=data_version,
                user_id=user_id,
                needs_human_review=False,
                execution_steps=execution_steps,
            )
            return resp

        # 1. Deterministic Domain Guardrails & Refusal Rules
        lower_q = clean_q.lower()

        # Guard A: Future Predictions & Revenue Forecasting
        if any(w in lower_q for w in ["next year", "forecast", "future sales", "predict", "predictive", "tomorrow"]):
            logger.info("Refusing unsupported prediction/forecast query.")
            resp = CopilotQueryResponse(
                status=CopilotResponseStatusEnum.UNSUPPORTED,
                answer="I can't forecast future sales or revenue with the analysis currently available.",
                intent=CopilotIntentEnum.UNKNOWN.value,
                confidence=0.98,
                evidence_quality=EvidenceQualityEnum.NONE,
                evidence=[],
                insights=["Supported topics: Stock-Out Risks, Overstock Inventory, Sales Velocity Shifts, and Action Recommendations."],
                recommendations=[],
                assumptions=[],
                limitations=[
                    CopilotLimitation(
                        type="UNSUPPORTED_CAPABILITY",
                        message="Predictive forecasting models are not currently implemented.",
                        impact="Future revenue and demand predictions cannot be calculated.",
                    )
                ],
                needs_human_review=True,
                clarification_question=None,
            )
            execution_steps.append({
                "step_name": "Guardrail Check",
                "status": "REFUSED_UNSUPPORTED",
                "details": {"reason": "Predictive future forecasting requested."},
            })
            AuditService.log_copilot_interaction(
                question=clean_q,
                normalized_question=normalized_q,
                intent=resp.intent,
                confidence=resp.confidence,
                status=resp.status.value,
                cache_hit=False,
                cache_key=cache_key,
                gemini_calls=0,
                input_tokens=0,
                output_tokens=0,
                prompt_version=prompt_version,
                model=model,
                data_version=data_version,
                user_id=user_id,
                needs_human_review=True,
                execution_steps=execution_steps,
            )
            return resp

        # Guard B: Exact Replenishment Quantities without Supplier Parameters
        if any(w in lower_q for w in ["how many units should i order", "exact order quantity", "how much to purchase", "order size"]):
            logger.info("Escalating exact order quantity to human review.")
            resp = CopilotQueryResponse(
                status=CopilotResponseStatusEnum.HUMAN_REVIEW,
                answer=(
                    "I can identify products that need replenishment and estimated days of stock remaining, "
                    "but I don't have supplier lead times, minimum order quantities (MOQ), or purchasing constraints "
                    "needed to recommend an exact order quantity."
                ),
                intent=CopilotIntentEnum.ACTION_RECOMMENDATION.value,
                confidence=0.92,
                evidence_quality=EvidenceQualityEnum.MEDIUM,
                evidence=[],
                insights=["Review supplier contracts and lead times to establish appropriate replenishment batch sizes."],
                recommendations=[],
                assumptions=["Safety stock and order sizing require supplier lead time and MOQ constraints."],
                limitations=[
                    CopilotLimitation(
                        type="MISSING_DATA",
                        message="Supplier lead time and minimum order quantity (MOQ) data are not available.",
                        impact="Exact purchase quantities cannot be deterministically computed.",
                    )
                ],
                needs_human_review=True,
                clarification_question=None,
            )
            execution_steps.append({
                "step_name": "Guardrail Check",
                "status": "ESCALATED_HUMAN_REVIEW",
                "details": {"reason": "Missing supplier lead time and MOQ constraints."},
            })
            AuditService.log_copilot_interaction(
                question=clean_q,
                normalized_question=normalized_q,
                intent=resp.intent,
                confidence=resp.confidence,
                status=resp.status.value,
                cache_hit=False,
                cache_key=cache_key,
                gemini_calls=0,
                input_tokens=0,
                output_tokens=0,
                prompt_version=prompt_version,
                model=model,
                data_version=data_version,
                user_id=user_id,
                needs_human_review=True,
                execution_steps=execution_steps,
            )
            return resp

        # Guard C: Root-Cause Questions ("Why did sales drop / fall?")
        is_cause_inquiry = any(w in lower_q for w in ["why did", "why have", "cause of", "reason for drop", "reason for spike"])

        # 2. Intent Classification (with usage instrumentation)
        classification, intent_usage = GeminiService.classify_intent_with_usage(clean_q)
        intent = classification.intent
        confidence = round(classification.confidence, 2)
        raw_filters = classification.filters

        gemini_calls_total += intent_usage["gemini_calls"]
        input_tokens_total += intent_usage["input_tokens"]
        output_tokens_total += intent_usage["output_tokens"]

        execution_steps.append({
            "step_name": "Intent Classification",
            "status": "COMPLETED",
            "details": {
                "intent": intent.value,
                "confidence": confidence,
                "gemini_calls": intent_usage["gemini_calls"],
                "input_tokens": intent_usage["input_tokens"],
                "output_tokens": intent_usage["output_tokens"],
            },
        })

        # 3. Check for Ambiguous Question
        if intent == CopilotIntentEnum.AMBIGUOUS:
            clarification = classification.clarification_needed or (
                "Would you like me to check stock-out risks, overstock/slow-moving inventory, or both?"
            )
            resp = CopilotQueryResponse(
                status=CopilotResponseStatusEnum.AMBIGUOUS,
                answer=f"Your query is ambiguous. {clarification}",
                intent=intent.value,
                confidence=confidence,
                evidence_quality=EvidenceQualityEnum.NONE,
                evidence=[],
                insights=["Please clarify whether you are evaluating imminent stock shortages or excess sitting inventory."],
                recommendations=[],
                assumptions=[],
                limitations=[
                    CopilotLimitation(
                        type="AMBIGUOUS_QUERY",
                        message="Question could refer to either stock-out risk or overstocked inventory.",
                        impact="Specific analytics model cannot be selected without manager clarification.",
                    )
                ],
                needs_human_review=True,
                clarification_question=clarification,
            )
            AuditService.log_copilot_interaction(
                question=clean_q,
                normalized_question=normalized_q,
                intent=resp.intent,
                confidence=resp.confidence,
                status=resp.status.value,
                cache_hit=False,
                cache_key=cache_key,
                gemini_calls=gemini_calls_total,
                input_tokens=input_tokens_total,
                output_tokens=output_tokens_total,
                prompt_version=prompt_version,
                model=model,
                data_version=data_version,
                user_id=user_id,
                needs_human_review=True,
                execution_steps=execution_steps,
            )
            return resp

        # 4. Check for General Unknown Intent
        if intent == CopilotIntentEnum.UNKNOWN:
            limit_msg = classification.clarification_needed or (
                "I can't reliably answer that with the data and analysis currently available in the system."
            )
            resp = CopilotQueryResponse(
                status=CopilotResponseStatusEnum.UNSUPPORTED,
                answer=limit_msg,
                intent=intent.value,
                confidence=confidence,
                evidence_quality=EvidenceQualityEnum.NONE,
                evidence=[],
                insights=["Supported topics: Stock-Out Risks, Overstock & Slow-Moving Inventory, Sales Spikes & Drops, Action Recommendations."],
                recommendations=[],
                assumptions=[],
                limitations=[
                    CopilotLimitation(
                        type="UNSUPPORTED_CAPABILITY",
                        message="The requested query falls outside supported deterministic retail analytics.",
                        impact="No analytical conclusion can be drawn.",
                    )
                ],
                needs_human_review=True,
                clarification_question=None,
            )
            AuditService.log_copilot_interaction(
                question=clean_q,
                normalized_question=normalized_q,
                intent=resp.intent,
                confidence=resp.confidence,
                status=resp.status.value,
                cache_hit=False,
                cache_key=cache_key,
                gemini_calls=gemini_calls_total,
                input_tokens=input_tokens_total,
                output_tokens=output_tokens_total,
                prompt_version=prompt_version,
                model=model,
                data_version=data_version,
                user_id=user_id,
                needs_human_review=True,
                execution_steps=execution_steps,
            )
            return resp

        # 5. Parameterized Entity Resolution against SQLite (with Disambiguation)
        store_res = cls._resolve_store(raw_filters.store)
        cat_res = cls._resolve_category(raw_filters.category)
        prod_res = cls._resolve_product(raw_filters.product)

        # Check for NOT_FOUND or AMBIGUOUS entities
        if store_res["status"] == CopilotResponseStatusEnum.NOT_FOUND:
            resp = CopilotQueryResponse(
                status=CopilotResponseStatusEnum.NOT_FOUND,
                answer=store_res["message"],
                intent=intent.value,
                confidence=confidence,
                evidence_quality=EvidenceQualityEnum.NONE,
                evidence=[],
                insights=[],
                recommendations=[],
                assumptions=[],
                limitations=[
                    CopilotLimitation(
                        type="MISSING_DATA",
                        message=f"Store '{raw_filters.store}' does not exist in the store directory.",
                        impact="Store-specific analysis cannot be performed.",
                    )
                ],
                needs_human_review=True,
                clarification_question=None,
            )
            AuditService.log_copilot_interaction(
                question=clean_q,
                normalized_question=normalized_q,
                intent=resp.intent,
                confidence=resp.confidence,
                status=resp.status.value,
                cache_hit=False,
                cache_key=cache_key,
                gemini_calls=gemini_calls_total,
                input_tokens=input_tokens_total,
                output_tokens=output_tokens_total,
                prompt_version=prompt_version,
                model=model,
                data_version=data_version,
                user_id=user_id,
                needs_human_review=True,
                execution_steps=execution_steps,
            )
            return resp

        if store_res["status"] == CopilotResponseStatusEnum.AMBIGUOUS:
            resp = CopilotQueryResponse(
                status=CopilotResponseStatusEnum.AMBIGUOUS,
                answer=store_res["message"],
                intent=intent.value,
                confidence=confidence,
                evidence_quality=EvidenceQualityEnum.NONE,
                evidence=[],
                insights=[],
                recommendations=[],
                assumptions=[],
                limitations=[],
                needs_human_review=True,
                clarification_question=store_res["message"],
            )
            AuditService.log_copilot_interaction(
                question=clean_q,
                normalized_question=normalized_q,
                intent=resp.intent,
                confidence=resp.confidence,
                status=resp.status.value,
                cache_hit=False,
                cache_key=cache_key,
                gemini_calls=gemini_calls_total,
                input_tokens=input_tokens_total,
                output_tokens=output_tokens_total,
                prompt_version=prompt_version,
                model=model,
                data_version=data_version,
                user_id=user_id,
                needs_human_review=True,
                execution_steps=execution_steps,
            )
            return resp

        if prod_res["status"] == CopilotResponseStatusEnum.NOT_FOUND:
            resp = CopilotQueryResponse(
                status=CopilotResponseStatusEnum.NOT_FOUND,
                answer=prod_res["message"],
                intent=intent.value,
                confidence=confidence,
                evidence_quality=EvidenceQualityEnum.NONE,
                evidence=[],
                insights=[],
                recommendations=[],
                assumptions=[],
                limitations=[
                    CopilotLimitation(
                        type="MISSING_DATA",
                        message=f"Product '{raw_filters.product}' does not exist in the product catalog.",
                        impact="Product-specific analysis cannot be performed.",
                    )
                ],
                needs_human_review=True,
                clarification_question=None,
            )
            AuditService.log_copilot_interaction(
                question=clean_q,
                normalized_question=normalized_q,
                intent=resp.intent,
                confidence=resp.confidence,
                status=resp.status.value,
                cache_hit=False,
                cache_key=cache_key,
                gemini_calls=gemini_calls_total,
                input_tokens=input_tokens_total,
                output_tokens=output_tokens_total,
                prompt_version=prompt_version,
                model=model,
                data_version=data_version,
                user_id=user_id,
                needs_human_review=True,
                execution_steps=execution_steps,
            )
            return resp

        if prod_res["status"] == CopilotResponseStatusEnum.AMBIGUOUS:
            resp = CopilotQueryResponse(
                status=CopilotResponseStatusEnum.AMBIGUOUS,
                answer=prod_res["message"],
                intent=intent.value,
                confidence=confidence,
                evidence_quality=EvidenceQualityEnum.NONE,
                evidence=[],
                insights=[],
                recommendations=[],
                assumptions=[],
                limitations=[],
                needs_human_review=True,
                clarification_question=prod_res["message"],
            )
            AuditService.log_copilot_interaction(
                question=clean_q,
                normalized_question=normalized_q,
                intent=resp.intent,
                confidence=resp.confidence,
                status=resp.status.value,
                cache_hit=False,
                cache_key=cache_key,
                gemini_calls=gemini_calls_total,
                input_tokens=input_tokens_total,
                output_tokens=output_tokens_total,
                prompt_version=prompt_version,
                model=model,
                data_version=data_version,
                user_id=user_id,
                needs_human_review=True,
                execution_steps=execution_steps,
            )
            return resp

        resolved_store_id = store_res.get("id")
        resolved_store_name = store_res.get("name")
        resolved_cat = cat_res.get("category")
        resolved_prod_id = prod_res.get("id")
        resolved_prod_name = prod_res.get("name")

        # 6. Dispatch to Deterministic Analytics & Evidence Validation
        evidence_dict, evidence_records, assumptions, raw_recommendations, evidence_quality, is_insufficient_data, limitation_objs = (
            cls._collect_and_validate_evidence(
                intent=intent,
                store_id=resolved_store_id,
                store_name=resolved_store_name,
                category=resolved_cat,
                product_id=resolved_prod_id,
                product_name=resolved_prod_name,
                is_cause_inquiry=is_cause_inquiry,
            )
        )

        execution_steps.append({
            "step_name": "Deterministic SQL Analytics",
            "status": "COMPLETED",
            "details": {
                "source": evidence_dict.get("source"),
                "metrics": evidence_dict.get("metrics"),
                "records_count": len(evidence_dict.get("records", [])),
                "is_insufficient_data": is_insufficient_data,
            },
        })

        # 7. Determine Final Response State
        if is_insufficient_data:
            final_status = CopilotResponseStatusEnum.INSUFFICIENT_DATA
            needs_review = True
        elif is_cause_inquiry:
            final_status = CopilotResponseStatusEnum.HUMAN_REVIEW
            needs_review = True
        else:
            final_status = CopilotResponseStatusEnum.ANSWERED
            needs_review = False

        # 8. Generate Grounded NLG Answer (with usage instrumentation)
        grounded_result, nlg_usage = GeminiService.generate_grounded_response_with_usage(
            question=clean_q,
            intent=intent,
            evidence=evidence_dict,
        )

        gemini_calls_total += nlg_usage["gemini_calls"]
        input_tokens_total += nlg_usage["input_tokens"]
        output_tokens_total += nlg_usage["output_tokens"]

        execution_steps.append({
            "step_name": "Grounded NLG Synthesis",
            "status": "COMPLETED",
            "details": {
                "gemini_calls": nlg_usage["gemini_calls"],
                "input_tokens": nlg_usage["input_tokens"],
                "output_tokens": nlg_usage["output_tokens"],
                "insights_count": len(grounded_result.get("insights", [])),
            },
        })

        answer_text = grounded_result.get("answer", "")
        if is_cause_inquiry and not is_insufficient_data:
            answer_text += (
                " Note: The available transaction data establishes the measurable sales change, "
                "but does not identify external causes such as pricing, competition, or marketing campaigns."
            )

        final_response = CopilotQueryResponse(
            status=final_status,
            answer=answer_text,
            intent=intent.value,
            confidence=confidence,
            evidence_quality=evidence_quality,
            evidence=evidence_records,
            insights=grounded_result.get("insights", []),
            recommendations=raw_recommendations,
            assumptions=assumptions,
            limitations=limitation_objs,
            needs_human_review=needs_review,
            clarification_question=None,
        )

        execution_steps.append({
            "step_name": "Response Assembly",
            "status": "COMPLETED",
            "details": {
                "final_status": final_response.status.value,
                "needs_human_review": final_response.needs_human_review,
                "evidence_count": len(evidence_records),
            },
        })

        # Save to safe cache if response is grounded and answered cleanly
        if final_status == CopilotResponseStatusEnum.ANSWERED:
            CopilotCacheService.store_cached_response(
                cache_key=cache_key,
                data_version=data_version,
                prompt_version=prompt_version,
                model=model,
                normalized_question=normalized_q,
                response_dict=final_response.model_dump(),
                gemini_calls=gemini_calls_total,
                input_tokens=input_tokens_total,
                output_tokens=output_tokens_total,
            )

        # Record audit log (non-blocking)
        action_summary = raw_recommendations[0].get("recommendation") if raw_recommendations else None
        AuditService.log_copilot_interaction(
            question=clean_q,
            normalized_question=normalized_q,
            intent=final_response.intent,
            confidence=final_response.confidence,
            status=final_response.status.value,
            cache_hit=False,
            cache_key=cache_key,
            gemini_calls=gemini_calls_total,
            input_tokens=input_tokens_total,
            output_tokens=output_tokens_total,
            prompt_version=prompt_version,
            model=model,
            data_version=data_version,
            user_id=user_id,
            action_recommendation=action_summary,
            needs_human_review=final_response.needs_human_review,
            execution_steps=execution_steps,
        )

        return final_response

    @classmethod
    def _resolve_store(cls, raw_store: Optional[str]) -> Dict[str, Any]:
        """Resolves raw store name against SQLite with disambiguation."""
        if not raw_store or not raw_store.strip():
            return {"status": CopilotResponseStatusEnum.ANSWERED, "id": None, "name": None}

        clean = raw_store.strip()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            pattern = f"%{clean.lower()}%"
            cursor.execute(
                "SELECT id, store_name, store_code FROM stores WHERE LOWER(store_name) LIKE ? OR LOWER(store_code) LIKE ?",
                (pattern, pattern),
            )
            rows = cursor.fetchall()
            if not rows:
                return {
                    "status": CopilotResponseStatusEnum.NOT_FOUND,
                    "message": f"I couldn't find a store matching '{clean}' in the available retail data.",
                }
            if len(rows) > 1 and clean.lower() not in [r["store_name"].lower() for r in rows]:
                names = [f"{r['store_name']} ({r['store_code']})" for r in rows]
                return {
                    "status": CopilotResponseStatusEnum.AMBIGUOUS,
                    "message": f"I found multiple stores matching '{clean}': {', '.join(names)}. Which store would you like to analyze?",
                }
            return {
                "status": CopilotResponseStatusEnum.ANSWERED,
                "id": rows[0]["id"],
                "name": rows[0]["store_name"],
            }

    @classmethod
    def _resolve_category(cls, raw_cat: Optional[str]) -> Dict[str, Any]:
        """Resolves category filter against SQLite."""
        if not raw_cat or not raw_cat.strip():
            return {"category": None}

        clean = raw_cat.strip()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            pattern = f"%{clean.lower()}%"
            cursor.execute(
                "SELECT DISTINCT category FROM products WHERE LOWER(category) LIKE ? LIMIT 1",
                (pattern,),
            )
            row = cursor.fetchone()
            if row:
                return {"category": row["category"]}
            return {"category": None}

    @classmethod
    def _resolve_product(cls, raw_prod: Optional[str]) -> Dict[str, Any]:
        """Resolves product name or SKU against SQLite with disambiguation."""
        if not raw_prod or not raw_prod.strip():
            return {"status": CopilotResponseStatusEnum.ANSWERED, "id": None, "name": None}

        clean = raw_prod.strip()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            pattern = f"%{clean.lower()}%"
            cursor.execute(
                "SELECT id, sku, product_name FROM products WHERE LOWER(product_name) LIKE ? OR LOWER(sku) LIKE ?",
                (pattern, pattern),
            )
            rows = cursor.fetchall()
            if not rows:
                return {
                    "status": CopilotResponseStatusEnum.NOT_FOUND,
                    "message": f"I couldn't find a product matching '{clean}' in the available retail data.",
                }

            # Check if exact match exists
            exact_matches = [r for r in rows if r["product_name"].lower() == clean.lower() or r["sku"].lower() == clean.lower()]
            if exact_matches:
                return {
                    "status": CopilotResponseStatusEnum.ANSWERED,
                    "id": exact_matches[0]["id"],
                    "name": exact_matches[0]["product_name"],
                }

            # If multiple partial matches found, return AMBIGUOUS
            if len(rows) > 1:
                names = [f"'{r['product_name']}'" for r in rows[:4]]
                return {
                    "status": CopilotResponseStatusEnum.AMBIGUOUS,
                    "message": f"I found multiple products matching '{clean}': {', '.join(names)}. Which product would you like me to analyze?",
                }

            return {
                "status": CopilotResponseStatusEnum.ANSWERED,
                "id": rows[0]["id"],
                "name": rows[0]["product_name"],
            }

    @classmethod
    def _collect_and_validate_evidence(
        cls,
        intent: CopilotIntentEnum,
        store_id: Optional[int],
        store_name: Optional[str],
        category: Optional[str],
        product_id: Optional[int],
        product_name: Optional[str],
        is_cause_inquiry: bool = False,
    ) -> Tuple[Dict[str, Any], List[CopilotEvidenceRecord], List[str], List[Dict[str, Any]], EvidenceQualityEnum, bool, List[CopilotLimitation]]:
        """
        Executes deterministic analytics, validates evidence sufficiency,
        and scores evidence quality.
        """
        evidence_records: List[CopilotEvidenceRecord] = []
        assumptions: List[str] = []
        raw_recommendations: List[Dict[str, Any]] = []
        limitation_objs: List[CopilotLimitation] = []
        evidence_dict: Dict[str, Any] = {"source": "", "metrics": {}, "records": []}
        is_insufficient_data = False
        evidence_quality = EvidenceQualityEnum.HIGH

        if is_cause_inquiry:
            limitation_objs.append(
                CopilotLimitation(
                    type="UNSUPPORTED_CAUSE",
                    message="External drivers (competitor pricing, marketing campaigns, promotions) are not available in the database.",
                    impact="The causal driver for the velocity shift cannot be definitively established.",
                )
            )

        # 1. STOCKOUT_RISK
        if intent == CopilotIntentEnum.STOCKOUT_RISK:
            res = InventoryRiskService.calculate_stockout_risks(store_id=store_id, category=category)
            filtered = res.results
            if product_id:
                filtered = [r for r in filtered if r.product_id == product_id]

            if not res.results and not product_id:
                evidence_quality = EvidenceQualityEnum.HIGH
            elif product_id and not filtered:
                # Product exists but has zero risk or healthy inventory
                pass

            assumptions.append(f"Demand velocity estimated over {res.lookback_days} calendar days of historical sales.")
            assumptions.append("High risk defined as <= 3 days of supply remaining; Medium risk defined as 3-7 days.")
            evidence_dict["source"] = "inventory_risk_service"
            evidence_dict["metrics"] = {
                "high_risk_count": res.summary.high_risk_count,
                "medium_risk_count": res.summary.medium_risk_count,
                "total_at_risk": len(filtered),
            }

            for r in filtered[:6]:
                evidence_dict["records"].append({
                    "product": r.product_name,
                    "sku": r.sku,
                    "store": r.store_name,
                    "current_stock": r.current_stock,
                    "average_daily_sales": r.average_daily_sales,
                    "days_remaining": r.estimated_days_remaining,
                    "risk_level": r.risk_level,
                })
                evidence_records.append(
                    CopilotEvidenceRecord(
                        product=r.product_name,
                        sku=r.sku,
                        category=r.category,
                        store=r.store_name,
                        metric_label="Days Remaining",
                        metric_value=f"{r.estimated_days_remaining:.1f} days",
                        status=r.risk_level,
                        details=f"Stock: {r.current_stock} units | Demand: {r.average_daily_sales:.2f}/day",
                    )
                )

        # 2. OVERSTOCK
        elif intent == CopilotIntentEnum.OVERSTOCK:
            res = OverstockService.calculate_overstock(store_id=store_id, category=category)
            filtered = res.results
            if product_id:
                filtered = [r for r in filtered if r.product_id == product_id]

            assumptions.append(f"Overstock evaluated over {res.lookback_days} calendar days of recent demand.")
            assumptions.append("Overstock defined as > 30 days of supply; Severe overstock as > 60 days.")
            evidence_dict["source"] = "overstock_service"
            evidence_dict["metrics"] = {
                "severe_overstock_count": res.summary.severe_overstock_count,
                "overstock_count": res.summary.overstock_count,
                "no_recent_demand_count": res.summary.no_recent_demand_count,
                "slow_moving_count": res.summary.slow_moving_count,
                "total_attention_items": len(filtered),
            }

            for r in filtered[:6]:
                days_str = f"{r.days_of_stock:.1f} days" if r.days_of_stock is not None else "No recent demand"
                evidence_dict["records"].append({
                    "product": r.product_name,
                    "sku": r.sku,
                    "store": r.store_name,
                    "current_stock": r.current_stock,
                    "average_daily_sales": r.average_daily_sales,
                    "days_of_stock": r.days_of_stock,
                    "status": r.status,
                })
                evidence_records.append(
                    CopilotEvidenceRecord(
                        product=r.product_name,
                        sku=r.sku,
                        category=r.category,
                        store=r.store_name,
                        metric_label="Days of Stock",
                        metric_value=days_str,
                        status=r.status,
                        details=f"Stock: {r.current_stock} units | 30d Sales: {r.recent_quantity_sold} units",
                    )
                )

        # 3. SALES SPIKES, DROPS, SIGNALS
        elif intent in (CopilotIntentEnum.SALES_SPIKE, CopilotIntentEnum.SALES_DROP, CopilotIntentEnum.SALES_SIGNALS):
            status_filter = "SPIKE" if intent == CopilotIntentEnum.SALES_SPIKE else ("DROP" if intent == CopilotIntentEnum.SALES_DROP else None)
            res = SalesAnomalyService.calculate_anomalies(store_id=store_id, category=category, status_filter=status_filter)
            filtered = res.results
            if product_id:
                filtered = [r for r in filtered if r.product_id == product_id]

            # Check for insufficient baseline demand across filtered items
            insufficient_items = [r for r in filtered if r.status == "INSUFFICIENT_BASELINE"]
            if product_id and filtered and filtered[0].status == "INSUFFICIENT_BASELINE":
                is_insufficient_data = True
                evidence_quality = EvidenceQualityEnum.LOW
                limitation_objs.append(
                    CopilotLimitation(
                        type="MISSING_DATA",
                        message=f"Baseline demand ({filtered[0].baseline_average_daily_sales:.2f}/day) is below the 2.0 units/day reliability threshold.",
                        impact="A percentage comparison cannot be reliably calculated without sufficient baseline demand.",
                    )
                )

            assumptions.append(
                f"Sales signals compare recent 7 days ({res.recent_start_date} to {res.recent_end_date}) "
                f"against 30-day baseline ({res.baseline_start_date} to {res.baseline_end_date})."
            )
            assumptions.append("Spike threshold: >= +50%; Drop threshold: <= -40%; Minimum baseline: 2.0 units/day.")
            evidence_dict["source"] = "sales_anomaly_service"
            evidence_dict["metrics"] = {
                "spike_count": res.summary.spike_count,
                "drop_count": res.summary.drop_count,
                "total_signals": len(filtered),
            }

            for r in filtered[:6]:
                pct_str = f"{r.percentage_change:+.1f}%" if r.percentage_change is not None else "Insufficient Baseline"
                evidence_dict["records"].append({
                    "product": r.product_name,
                    "sku": r.sku,
                    "store": r.store_name,
                    "recent_avg": r.recent_average_daily_sales,
                    "baseline_avg": r.baseline_average_daily_sales,
                    "change": pct_str,
                    "status": r.status,
                })
                evidence_records.append(
                    CopilotEvidenceRecord(
                        product=r.product_name,
                        sku=r.sku,
                        category=r.category,
                        store=r.store_name,
                        metric_label="Velocity Shift",
                        metric_value=pct_str,
                        status=r.status,
                        details=f"Recent: {r.recent_average_daily_sales:.2f}/day | Baseline: {r.baseline_average_daily_sales:.2f}/day",
                    )
                )

        # 4. ACTION RECOMMENDATION
        elif intent == CopilotIntentEnum.ACTION_RECOMMENDATION:
            rec_res = RecommendationService.get_recommendations(store_id=store_id, category=category)
            filtered = rec_res.results
            if product_id:
                filtered = [r for r in filtered if r.product_id == product_id]

            assumptions.append("Recommendations derived from 14-day stock-out, 30-day overstock, and 7d/30d anomaly models.")
            evidence_dict["source"] = "recommendation_service"
            evidence_dict["metrics"] = {
                "high_priority_count": rec_res.summary.high_priority_count,
                "medium_priority_count": rec_res.summary.medium_priority_count,
                "total_recommendations": len(filtered),
            }

            for r in filtered[:6]:
                raw_recommendations.append(r.model_dump())
                evidence_dict["records"].append({
                    "product": r.product_name,
                    "sku": r.sku,
                    "store": r.store_name,
                    "action": r.action.value,
                    "priority": r.priority.value,
                    "recommendation": r.recommendation,
                    "reason": r.reason,
                    "needs_human_review": r.needs_human_review,
                })
                evidence_records.append(
                    CopilotEvidenceRecord(
                        product=r.product_name,
                        sku=r.sku,
                        category=r.category,
                        store=r.store_name,
                        metric_label="Action",
                        metric_value=r.action.value.replace("_", " "),
                        status=r.priority.value,
                        details=f"{r.recommendation} ({r.reason})",
                    )
                )

        # 5. INVENTORY_VALUE
        elif intent == CopilotIntentEnum.INVENTORY_VALUE:
            inv = ValueAnalyticsService.calculate_inventory_value(store_id=store_id, category=category, product_id=product_id)
            assumptions.append("Inventory Value computed deterministically as (stock_quantity × unit_price).")
            evidence_dict["source"] = "value_analytics_service.inventory_value"
            evidence_dict["metrics"] = {
                "total_inventory_value": inv["total_inventory_value"],
                "total_stock_units": inv["total_stock_units"],
            }
            for p in inv["top_products"][:6]:
                evidence_dict["records"].append({
                    "product": p.product_name,
                    "sku": p.sku,
                    "category": p.category,
                    "unit_price": p.unit_price,
                    "total_stock": p.total_stock_quantity,
                    "inventory_value": p.inventory_value,
                })
                evidence_records.append(
                    CopilotEvidenceRecord(
                        product=p.product_name,
                        sku=p.sku,
                        category=p.category,
                        store=store_name or "All Stores",
                        metric_label="Inventory Value",
                        metric_value=f"{p.inventory_value:,.2f}",
                        status="VALUATION",
                        details=f"Stock: {p.total_stock_quantity} units @ {p.unit_price:.2f}",
                    )
                )

        # 6. REVENUE_SUMMARY
        elif intent == CopilotIntentEnum.REVENUE_SUMMARY:
            sales = ValueAnalyticsService.calculate_sales_revenue(store_id=store_id, category=category, product_id=product_id)
            assumptions.append("Sales Revenue aggregated from authoritative stored transaction revenue records.")
            evidence_dict["source"] = "value_analytics_service.sales_revenue"
            evidence_dict["metrics"] = {
                "total_sales_revenue": sales["total_sales_revenue"],
                "total_sales_units": sales["total_sales_units"],
            }
            for p in sales["top_products"][:6]:
                evidence_dict["records"].append({
                    "product": p.product_name,
                    "sku": p.sku,
                    "category": p.category,
                    "sales_units": p.total_sales_quantity,
                    "total_revenue": p.total_revenue,
                })
                evidence_records.append(
                    CopilotEvidenceRecord(
                        product=p.product_name,
                        sku=p.sku,
                        category=p.category,
                        store=store_name or "All Stores",
                        metric_label="Sales Revenue",
                        metric_value=f"{p.total_revenue:,.2f}",
                        status="TOP_REVENUE",
                        details=f"Sold: {p.total_sales_quantity} units",
                    )
                )

        # 7. OVERSTOCK_VALUE
        elif intent == CopilotIntentEnum.OVERSTOCK_VALUE:
            ov = ValueAnalyticsService.calculate_overstock_value(store_id=store_id, category=category)
            assumptions.append("Overstock Value computed as current stock × unit price for items in OVERSTOCK, SEVERE_OVERSTOCK, SLOW_MOVING, or NO_RECENT_DEMAND.")
            evidence_dict["source"] = "value_analytics_service.overstock_value"
            top_prod_dict = ov.top_contributing_product or {}
            evidence_dict["metrics"] = {
                "total_overstock_inventory_value": ov.total_overstock_inventory_value,
                "products_affected_count": ov.products_affected_count,
                "stores_affected_count": ov.stores_affected_count,
                "severe_overstock_value": ov.severe_overstock_value,
                "no_demand_value": ov.no_demand_value,
                "top_contributing_product": top_prod_dict,
            }

            if top_prod_dict:
                evidence_records.append(
                    CopilotEvidenceRecord(
                        product=top_prod_dict.get("product_name", "Top Overstock Product"),
                        sku=top_prod_dict.get("sku"),
                        category=top_prod_dict.get("category"),
                        store=store_name or "All Stores",
                        metric_label="Tied-Up Overstock Value",
                        metric_value=f"{top_prod_dict.get('tied_up_value', 0.0):,.2f}",
                        status="TIED_UP_CAPITAL",
                        details=f"{top_prod_dict.get('total_stock', 0)} units @ {top_prod_dict.get('unit_price', 0.0):.2f}",
                    )
                )

            evidence_records.append(
                CopilotEvidenceRecord(
                    product="Overstock Summary",
                    sku=None,
                    category=category or "All Categories",
                    store=store_name or "All Stores",
                    metric_label="Total Overstock Capital",
                    metric_value=f"{ov.total_overstock_inventory_value:,.2f}",
                    status="SUMMARY",
                    details=f"Affecting {ov.products_affected_count} products across {ov.stores_affected_count} stores",
                )
            )

            if ov.total_overstock_inventory_value > 0:
                raw_recommendations.append({
                    "product": top_prod_dict.get("product_name", "Overstocked Items"),
                    "recommendation": "Review replenishment schedule and explore inventory rebalancing across stores.",
                    "reason": f"Holding {ov.total_overstock_inventory_value:,.2f} in slow-moving capital.",
                    "priority": "HIGH",
                    "action": "REVIEW_INVENTORY",
                    "needs_human_review": True,
                })

        # 8. STORE_VALUE_ANALYSIS
        elif intent == CopilotIntentEnum.STORE_VALUE_ANALYSIS:
            sales = ValueAnalyticsService.calculate_sales_revenue(store_id=store_id)
            inv = ValueAnalyticsService.calculate_inventory_value(store_id=store_id)
            assumptions.append("Store value analysis evaluates total sales revenue and current inventory holding value.")
            evidence_dict["source"] = "value_analytics_service.store_value"
            evidence_dict["metrics"] = {
                "total_sales_revenue": sales["total_sales_revenue"],
                "total_inventory_value": inv["total_inventory_value"],
            }
            for s in sales["stores_revenue"][:5]:
                evidence_dict["records"].append({
                    "store": s["store_name"],
                    "store_code": s["store_code"],
                    "revenue": s["revenue"],
                    "sales_units": s["sales_units"],
                })
                evidence_records.append(
                    CopilotEvidenceRecord(
                        product=f"Store: {s['store_name']}",
                        sku=s["store_code"],
                        category="Store Revenue",
                        store=s["store_name"],
                        metric_label="Store Revenue",
                        metric_value=f"{s['revenue']:,.2f}",
                        status="STORE_REVENUE",
                        details=f"Sales: {s['sales_units']} units",
                    )
                )

        # 9. PRODUCT_VALUE_ANALYSIS
        elif intent == CopilotIntentEnum.PRODUCT_VALUE_ANALYSIS:
            sales = ValueAnalyticsService.calculate_sales_revenue(product_id=product_id)
            inv = ValueAnalyticsService.calculate_inventory_value(product_id=product_id)
            assumptions.append("Product value analysis computes total revenue generated and holding inventory valuation per SKU.")
            evidence_dict["source"] = "value_analytics_service.product_value"
            evidence_dict["metrics"] = {
                "total_sales_revenue": sales["total_sales_revenue"],
                "total_inventory_value": inv["total_inventory_value"],
            }
            for p in sales["top_products"][:5]:
                evidence_dict["records"].append({
                    "product": p.product_name,
                    "sku": p.sku,
                    "category": p.category,
                    "revenue": p.total_revenue,
                    "sales_units": p.total_sales_quantity,
                })
                evidence_records.append(
                    CopilotEvidenceRecord(
                        product=p.product_name,
                        sku=p.sku,
                        category=p.category,
                        store=store_name or "All Stores",
                        metric_label="Product Revenue",
                        metric_value=f"{p.total_revenue:,.2f}",
                        status="TOP_PRODUCT_REVENUE",
                        details=f"Units sold: {p.total_sales_quantity}",
                    )
                )

        # 10. CATEGORY_VALUE_ANALYSIS
        elif intent == CopilotIntentEnum.CATEGORY_VALUE_ANALYSIS:
            sales = ValueAnalyticsService.calculate_sales_revenue(category=category)
            inv = ValueAnalyticsService.calculate_inventory_value(category=category)
            assumptions.append("Category value analysis aggregates sales revenue and inventory capital across merchandise categories.")
            evidence_dict["source"] = "value_analytics_service.category_value"
            evidence_dict["metrics"] = {
                "total_sales_revenue": sales["total_sales_revenue"],
                "total_inventory_value": inv["total_inventory_value"],
            }
            for c in sales["category_revenue"][:5]:
                evidence_dict["records"].append({
                    "category": c["category"],
                    "revenue": c["revenue"],
                    "sales_units": c["sales_units"],
                })
                evidence_records.append(
                    CopilotEvidenceRecord(
                        product=f"Category: {c['category']}",
                        sku=None,
                        category=c["category"],
                        store=store_name or "All Stores",
                        metric_label="Category Revenue",
                        metric_value=f"{c['revenue']:,.2f}",
                        status="CATEGORY_REVENUE",
                        details=f"Units: {c['sales_units']}",
                    )
                )

        # 11. INVENTORY_SUMMARY / STORE_ANALYSIS / PRODUCT_ANALYSIS (Generic Fallback)
        else:
            stockout_res = InventoryRiskService.calculate_stockout_risks(store_id=store_id, category=category)
            overstock_res = OverstockService.calculate_overstock(store_id=store_id, category=category)

            stockout_items = [r for r in stockout_res.results if not product_id or r.product_id == product_id]
            overstock_items = [r for r in overstock_res.results if not product_id or r.product_id == product_id]

            assumptions.append("Summary combines 14-day stock-out risk model and 30-day overstock model.")
            evidence_dict["source"] = "inventory_summary"
            evidence_dict["metrics"] = {
                "stockout_risk_count": len(stockout_items),
                "high_risk_stockouts": sum(1 for r in stockout_items if r.risk_level == "HIGH"),
                "overstock_count": len(overstock_items),
                "severe_overstock_count": sum(1 for r in overstock_items if r.status == "SEVERE_OVERSTOCK"),
            }

            for r in stockout_items[:3]:
                evidence_dict["records"].append({
                    "product": r.product_name,
                    "store": r.store_name,
                    "type": "STOCKOUT_RISK",
                    "status": r.risk_level,
                    "current_stock": r.current_stock,
                    "days_remaining": r.estimated_days_remaining,
                })
                evidence_records.append(
                    CopilotEvidenceRecord(
                        product=r.product_name,
                        sku=r.sku,
                        category=r.category,
                        store=r.store_name,
                        metric_label="Stockout Risk",
                        metric_value=f"{r.estimated_days_remaining:.1f} days",
                        status=r.risk_level,
                        details=f"Stock: {r.current_stock} units",
                    )
                )

            for r in overstock_items[:3]:
                days_str = f"{r.days_of_stock:.1f} days" if r.days_of_stock is not None else "No sales"
                evidence_dict["records"].append({
                    "product": r.product_name,
                    "store": r.store_name,
                    "type": "OVERSTOCK",
                    "status": r.status,
                    "current_stock": r.current_stock,
                    "days_of_stock": r.days_of_stock,
                })
                evidence_records.append(
                    CopilotEvidenceRecord(
                        product=r.product_name,
                        sku=r.sku,
                        category=r.category,
                        store=r.store_name,
                        metric_label="Overstock Status",
                        metric_value=days_str,
                        status=r.status,
                        details=f"Stock: {r.current_stock} units",
                    )
                )

        return evidence_dict, evidence_records, assumptions, raw_recommendations, evidence_quality, is_insufficient_data, limitation_objs
