from typing import Optional, List, Dict, Any
import logging

from backend.database.connection import get_db_connection
from backend.models.copilot import (
    CopilotIntentEnum,
    CopilotIntentClassification,
    CopilotQueryResponse,
    CopilotEvidenceRecord,
)
from backend.services.gemini_service import GeminiService
from backend.services.inventory_risk_service import InventoryRiskService
from backend.services.overstock_service import OverstockService
from backend.services.sales_anomaly_service import SalesAnomalyService

logger = logging.getLogger("retail_copilot.copilot_service")


class CopilotService:
    """Orchestrator for natural language Copilot queries mapped to deterministic analytics."""

    @classmethod
    def process_query(cls, question: str) -> CopilotQueryResponse:
        """
        End-to-end processing of a natural-language manager question:
        1. Validate question
        2. Classify intent (via Gemini / rules)
        3. Resolve filters against SQLite
        4. Execute deterministic analytics (Features 1, 2, 3)
        5. Compile normalized factual evidence
        6. Generate grounded response (via Gemini / rules)
        """
        clean_q = (question or "").strip()
        if not clean_q:
            return CopilotQueryResponse(
                answer="Please provide a question about sales, inventory, or store performance.",
                intent=CopilotIntentEnum.UNKNOWN.value,
                confidence=1.0,
                evidence=[],
                insights=[],
                assumptions=[],
                limitations=["Empty query received."],
                needs_human_review=False,
            )

        # 1. Intent understanding
        classification: CopilotIntentClassification = GeminiService.classify_intent(clean_q)
        intent = classification.intent
        confidence = round(classification.confidence, 2)
        raw_filters = classification.filters

        # 2. Check for Ambiguous / Unknown / Clarification
        if intent == CopilotIntentEnum.AMBIGUOUS:
            clarification = classification.clarification_needed or (
                "Do you want me to check stock-out risks, overstock/slow-moving inventory, or both?"
            )
            return CopilotQueryResponse(
                answer=f"Your query is ambiguous. {clarification}",
                intent=intent.value,
                confidence=confidence,
                evidence=[],
                insights=["Please specify whether you are evaluating low-stock risks or excess inventory."],
                assumptions=[],
                limitations=["Ambiguous intent."],
                needs_human_review=True,
            )

        if intent == CopilotIntentEnum.UNKNOWN:
            limit_msg = classification.clarification_needed or (
                "I can't reliably answer that with the data and analysis currently available in the system."
            )
            return CopilotQueryResponse(
                answer=limit_msg,
                intent=intent.value,
                confidence=confidence,
                evidence=[],
                insights=["Supported topics: Stock-Out Risks, Overstock & Slow-Moving Inventory, Sales Spikes & Drops."],
                assumptions=[],
                limitations=["Unsupported capability or future prediction request."],
                needs_human_review=True,
            )

        # 3. Parameterized Filter Resolution against SQLite
        resolved_store_id, resolved_store_name, store_error = cls._resolve_store(raw_filters.store)
        resolved_cat, cat_error = cls._resolve_category(raw_filters.category)
        resolved_prod_id, resolved_prod_name, prod_error = cls._resolve_product(raw_filters.product)

        # Handle filter resolution errors
        resolution_errors = [err for err in (store_error, cat_error, prod_error) if err]
        if resolution_errors:
            return CopilotQueryResponse(
                answer=" ".join(resolution_errors),
                intent=intent.value,
                confidence=confidence,
                evidence=[],
                insights=["Check the store name, category, or product SKU and try again."],
                assumptions=[],
                limitations=resolution_errors,
                needs_human_review=True,
            )

        # 4. Dispatch to Deterministic Analytics & Extract Evidence
        evidence_dict, evidence_records, assumptions = cls._collect_deterministic_evidence(
            intent=intent,
            store_id=resolved_store_id,
            store_name=resolved_store_name,
            category=resolved_cat,
            product_id=resolved_prod_id,
            product_name=resolved_prod_name,
        )

        # 5. Generate Grounded NLG Answer
        grounded_result = GeminiService.generate_grounded_response(
            question=clean_q,
            intent=intent,
            evidence=evidence_dict,
        )

        return CopilotQueryResponse(
            answer=grounded_result.get("answer", ""),
            intent=intent.value,
            confidence=confidence,
            evidence=evidence_records,
            insights=grounded_result.get("insights", []),
            assumptions=assumptions,
            limitations=grounded_result.get("limitations", []),
            needs_human_review=grounded_result.get("needs_human_review", False),
        )

    @classmethod
    def _resolve_store(cls, raw_store: Optional[str]):
        """Resolves raw store name against SQLite database using parameterized LIKE."""
        if not raw_store or not raw_store.strip():
            return None, None, None

        with get_db_connection() as conn:
            cursor = conn.cursor()
            pattern = f"%{raw_store.strip().lower()}%"
            cursor.execute(
                "SELECT id, store_name FROM stores WHERE LOWER(store_name) LIKE ? OR LOWER(store_code) LIKE ? LIMIT 1",
                (pattern, pattern),
            )
            row = cursor.fetchone()
            if row:
                return row["id"], row["store_name"], None
            return None, None, f"I couldn't find a store matching '{raw_store}' in the database."

    @classmethod
    def _resolve_category(cls, raw_cat: Optional[str]):
        """Resolves raw category against SQLite database."""
        if not raw_cat or not raw_cat.strip():
            return None, None

        with get_db_connection() as conn:
            cursor = conn.cursor()
            pattern = f"%{raw_cat.strip().lower()}%"
            cursor.execute(
                "SELECT DISTINCT category FROM products WHERE LOWER(category) LIKE ? LIMIT 1",
                (pattern,),
            )
            row = cursor.fetchone()
            if row:
                return row["category"], None
            return None, f"I couldn't find a product category matching '{raw_cat}' in the database."

    @classmethod
    def _resolve_product(cls, raw_prod: Optional[str]):
        """Resolves raw product name or SKU against SQLite database."""
        if not raw_prod or not raw_prod.strip():
            return None, None, None

        with get_db_connection() as conn:
            cursor = conn.cursor()
            pattern = f"%{raw_prod.strip().lower()}%"
            cursor.execute(
                "SELECT id, sku, product_name FROM products WHERE LOWER(product_name) LIKE ? OR LOWER(sku) LIKE ? LIMIT 1",
                (pattern, pattern),
            )
            row = cursor.fetchone()
            if row:
                return row["id"], row["product_name"], None
            return None, None, f"I couldn't find a product matching '{raw_prod}' in the database."

    @classmethod
    def _collect_deterministic_evidence(
        cls,
        intent: CopilotIntentEnum,
        store_id: Optional[int],
        store_name: Optional[str],
        category: Optional[str],
        product_id: Optional[int],
        product_name: Optional[str],
    ):
        """Dispatches to deterministic services and builds compact evidence records."""
        evidence_records: List[CopilotEvidenceRecord] = []
        assumptions: List[str] = []
        evidence_dict: Dict[str, Any] = {"source": "", "metrics": {}, "records": []}

        # 1. STOCKOUT_RISK
        if intent == CopilotIntentEnum.STOCKOUT_RISK:
            res = InventoryRiskService.calculate_stockout_risks(store_id=store_id, category=category)
            filtered_results = res.results
            if product_id:
                filtered_results = [r for r in filtered_results if r.product_id == product_id]

            assumptions.append(f"Demand velocity estimated over {res.lookback_days} calendar days of historical sales.")
            evidence_dict["source"] = "inventory_risk_service"
            evidence_dict["metrics"] = {
                "high_risk_count": res.summary.high_risk_count,
                "medium_risk_count": res.summary.medium_risk_count,
                "total_at_risk": len(filtered_results),
            }

            for r in filtered_results[:6]:
                rec_dict = {
                    "product": r.product_name,
                    "sku": r.sku,
                    "store": r.store_name,
                    "current_stock": r.current_stock,
                    "average_daily_sales": r.average_daily_sales,
                    "days_remaining": r.estimated_days_remaining,
                    "risk_level": r.risk_level,
                }
                evidence_dict["records"].append(rec_dict)
                evidence_records.append(
                    CopilotEvidenceRecord(
                        product=r.product_name,
                        sku=r.sku,
                        category=r.category,
                        store=r.store_name,
                        metric_label="Days Remaining",
                        metric_value=f"{r.estimated_days_remaining:.1f} days",
                        status=r.risk_level,
                        details=f"Stock: {r.current_stock} units | Daily demand: {r.average_daily_sales:.2f}/day",
                    )
                )

        # 2. OVERSTOCK / SLOW MOVING
        elif intent == CopilotIntentEnum.OVERSTOCK:
            res = OverstockService.calculate_overstock(store_id=store_id, category=category)
            filtered_results = res.results
            if product_id:
                filtered_results = [r for r in filtered_results if r.product_id == product_id]

            assumptions.append(f"Overstock evaluated over {res.lookback_days} calendar days of recent demand.")
            evidence_dict["source"] = "overstock_service"
            evidence_dict["metrics"] = {
                "severe_overstock_count": res.summary.severe_overstock_count,
                "overstock_count": res.summary.overstock_count,
                "no_recent_demand_count": res.summary.no_recent_demand_count,
                "slow_moving_count": res.summary.slow_moving_count,
                "total_attention_items": len(filtered_results),
            }

            for r in filtered_results[:6]:
                days_str = f"{r.days_of_stock:.1f} days" if r.days_of_stock is not None else "No recent sales"
                rec_dict = {
                    "product": r.product_name,
                    "sku": r.sku,
                    "store": r.store_name,
                    "current_stock": r.current_stock,
                    "average_daily_sales": r.average_daily_sales,
                    "days_of_stock": r.days_of_stock,
                    "status": r.status,
                }
                evidence_dict["records"].append(rec_dict)
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
            filtered_results = res.results
            if product_id:
                filtered_results = [r for r in filtered_results if r.product_id == product_id]

            assumptions.append(
                f"Sales signals compare recent 7 days ({res.recent_start_date} to {res.recent_end_date}) "
                f"against 30-day baseline ({res.baseline_start_date} to {res.baseline_end_date})."
            )
            evidence_dict["source"] = "sales_anomaly_service"
            evidence_dict["metrics"] = {
                "spike_count": res.summary.spike_count,
                "drop_count": res.summary.drop_count,
                "total_signals": len(filtered_results),
            }

            for r in filtered_results[:6]:
                pct_str = f"{r.percentage_change:+.1f}%" if r.percentage_change is not None else "N/A"
                rec_dict = {
                    "product": r.product_name,
                    "sku": r.sku,
                    "store": r.store_name,
                    "recent_avg": r.recent_average_daily_sales,
                    "baseline_avg": r.baseline_average_daily_sales,
                    "change": pct_str,
                    "status": r.status,
                }
                evidence_dict["records"].append(rec_dict)
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

        # 4. INVENTORY SUMMARY / STORE ANALYSIS / PRODUCT ANALYSIS
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

            # Add top stockout items
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

            # Add top overstock items
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

        return evidence_dict, evidence_records, assumptions
