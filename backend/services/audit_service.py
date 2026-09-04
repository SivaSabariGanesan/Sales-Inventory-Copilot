import json
import logging
from typing import Optional, List, Dict, Any, Tuple
from backend.database.connection import get_db_connection
from backend.models.audit import AuditLogItem, AuditLogDetail, AuditLogsResponse, GeminiUsageResponse
from backend.services.version_service import DataVersionService

logger = logging.getLogger("retail_copilot.audit_service")


class AuditService:
    """Service to record, query, and aggregate Copilot audit trails and Gemini usage telemetry."""

    @classmethod
    def log_copilot_interaction(
        cls,
        question: str,
        normalized_question: str,
        intent: str,
        confidence: float,
        status: str,
        cache_hit: bool,
        cache_key: Optional[str],
        gemini_calls: int,
        input_tokens: int,
        output_tokens: int,
        prompt_version: str,
        model: str,
        data_version: int,
        user_id: Optional[str] = None,
        action_recommendation: Optional[str] = None,
        needs_human_review: bool = False,
        execution_steps: Optional[List[Dict[str, Any]]] = None,
        error_message: Optional[str] = None,
        estimated_cost: Optional[float] = None,
    ) -> Optional[int]:
        """
        Record a complete Copilot query audit log in SQLite.
        Guaranteed non-blocking: catches all exceptions so Copilot requests never fail due to audit logging.
        """
        try:
            steps_json = json.dumps(execution_steps or [])
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO audit_logs (
                        user_id, question, normalized_question, intent, confidence, status,
                        cache_hit, cache_key, gemini_calls, input_tokens, output_tokens,
                        estimated_cost, action_recommendation, needs_human_review,
                        prompt_version, model, data_version, execution_steps, error_message
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        question,
                        normalized_question,
                        intent,
                        confidence,
                        status,
                        1 if cache_hit else 0,
                        cache_key,
                        gemini_calls,
                        input_tokens,
                        output_tokens,
                        estimated_cost,
                        action_recommendation,
                        1 if needs_human_review else 0,
                        prompt_version,
                        model,
                        data_version,
                        steps_json,
                        error_message,
                    ),
                )
                log_id = cursor.lastrowid
                return log_id
        except Exception as e:
            logger.error(f"Failed to record audit log safely: {e}", exc_info=True)
            return None

    @classmethod
    def get_audit_logs(
        cls,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        intent: Optional[str] = None,
        status: Optional[str] = None,
        cache_hit: Optional[bool] = None,
        needs_human_review: Optional[bool] = None,
    ) -> AuditLogsResponse:
        """Query paginated and filtered audit logs."""
        page = max(1, page)
        page_size = max(1, min(100, page_size))
        offset = (page - 1) * page_size

        where_clauses = []
        params = []

        if search and search.strip():
            where_clauses.append("(question LIKE ? OR normalized_question LIKE ? OR intent LIKE ? OR action_recommendation LIKE ?)")
            term = f"%{search.strip()}%"
            params.extend([term, term, term, term])

        if intent and intent.strip() and intent.strip().upper() != "ALL":
            where_clauses.append("intent = ?")
            params.append(intent.strip().upper())

        if status and status.strip() and status.strip().upper() != "ALL":
            where_clauses.append("status = ?")
            params.append(status.strip().upper())

        if cache_hit is not None:
            where_clauses.append("cache_hit = ?")
            params.append(1 if cache_hit else 0)

        if needs_human_review is not None:
            where_clauses.append("needs_human_review = ?")
            params.append(1 if needs_human_review else 0)

        where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Count total matching rows
            cursor.execute(f"SELECT COUNT(*) FROM audit_logs {where_str}", params)
            total_count = cursor.fetchone()[0]

            # Query page
            query = f"""
                SELECT id, timestamp, user_id, question, normalized_question, intent,
                       confidence, status, cache_hit, cache_key, gemini_calls,
                       input_tokens, output_tokens, estimated_cost, action_recommendation,
                       needs_human_review, prompt_version, model, data_version, error_message
                FROM audit_logs
                {where_str}
                ORDER BY timestamp DESC, id DESC
                LIMIT ? OFFSET ?
            """
            cursor.execute(query, params + [page_size, offset])
            rows = cursor.fetchall()

        logs = []
        for r in rows:
            in_tok = int(r["input_tokens"] or 0)
            out_tok = int(r["output_tokens"] or 0)
            logs.append(
                AuditLogItem(
                    id=r["id"],
                    timestamp=str(r["timestamp"]),
                    user_id=r["user_id"],
                    question=r["question"],
                    normalized_question=r["normalized_question"],
                    intent=r["intent"],
                    confidence=float(r["confidence"] or 1.0),
                    status=r["status"],
                    cache_hit=bool(r["cache_hit"]),
                    cache_key=r["cache_key"],
                    gemini_calls=int(r["gemini_calls"] or 0),
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    total_tokens=in_tok + out_tok,
                    estimated_cost=r["estimated_cost"],
                    action_recommendation=r["action_recommendation"],
                    needs_human_review=bool(r["needs_human_review"]),
                    prompt_version=r["prompt_version"] or "v1.2.0",
                    model=r["model"] or "gemini-2.5-flash",
                    data_version=int(r["data_version"] or 1),
                    error_message=r["error_message"],
                )
            )

        total_pages = max(1, (total_count + page_size - 1) // page_size) if total_count > 0 else 1

        return AuditLogsResponse(
            total_count=total_count,
            total=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            logs=logs,
        )

    @classmethod
    def get_audit_log_by_id(cls, audit_id: int) -> Optional[AuditLogDetail]:
        """Fetch single audit log detail with full execution step history."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, timestamp, user_id, question, normalized_question, intent,
                       confidence, status, cache_hit, cache_key, gemini_calls,
                       input_tokens, output_tokens, estimated_cost, action_recommendation,
                       needs_human_review, prompt_version, model, data_version,
                       execution_steps, error_message
                FROM audit_logs
                WHERE id = ?
                """,
                (audit_id,),
            )
            r = cursor.fetchone()
            if not r:
                return None

        in_tok = int(r["input_tokens"] or 0)
        out_tok = int(r["output_tokens"] or 0)
        steps = []
        parsed_evidence = None
        copilot_response = None
        fallback_reason = r["error_message"]

        if r["execution_steps"]:
            try:
                steps = json.loads(r["execution_steps"])
                for s in steps:
                    if s.get("step") == "evidence_retrieval" and "evidence" in s.get("details", {}):
                        parsed_evidence = s["details"]["evidence"]
                    if s.get("step") == "nlg_synthesis" and "response_preview" in s.get("details", {}):
                        copilot_response = s["details"]["response_preview"]
            except Exception:
                steps = []

        return AuditLogDetail(
            id=r["id"],
            timestamp=str(r["timestamp"]),
            user_id=r["user_id"],
            question=r["question"],
            normalized_question=r["normalized_question"],
            intent=r["intent"],
            confidence=float(r["confidence"] or 1.0),
            status=r["status"],
            cache_hit=bool(r["cache_hit"]),
            cache_key=r["cache_key"],
            gemini_calls=int(r["gemini_calls"] or 0),
            input_tokens=in_tok,
            output_tokens=out_tok,
            total_tokens=in_tok + out_tok,
            estimated_cost=r["estimated_cost"],
            action_recommendation=r["action_recommendation"],
            needs_human_review=bool(r["needs_human_review"]),
            prompt_version=r["prompt_version"] or "v1.2.0",
            model=r["model"] or "gemini-2.5-flash",
            data_version=int(r["data_version"] or 1),
            execution_steps=steps,
            parsed_execution_steps=steps,
            parsed_evidence=parsed_evidence,
            copilot_response=copilot_response,
            fallback_reason=fallback_reason,
            error_message=r["error_message"],
        )

    @classmethod
    def get_usage_metrics(cls) -> GeminiUsageResponse:
        """Aggregate Gemini usage, token telemetry, and caching performance across all audit records."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total_requests,
                    SUM(gemini_calls) as total_calls,
                    SUM(CASE WHEN cache_hit = 1 THEN 1 ELSE 0 END) as cache_hits,
                    SUM(CASE WHEN cache_hit = 0 THEN 1 ELSE 0 END) as cache_misses,
                    SUM(input_tokens) as total_in_tokens,
                    SUM(output_tokens) as total_out_tokens
                FROM audit_logs
                """
            )
            row = cursor.fetchone()

            # Active cached entries count
            cursor.execute("SELECT COUNT(*) FROM copilot_cache")
            active_caches = cursor.fetchone()[0]

        total_reqs = int(row["total_requests"] or 0)
        total_calls = int(row["total_calls"] or 0)
        hits = int(row["cache_hits"] or 0)
        misses = int(row["cache_misses"] or 0)
        in_tokens = int(row["total_in_tokens"] or 0)
        out_tokens = int(row["total_out_tokens"] or 0)
        total_tokens = in_tokens + out_tokens

        hit_rate = round((hits / total_reqs * 100), 1) if total_reqs > 0 else 0.0
        current_data_ver = DataVersionService.get_data_version()

        return GeminiUsageResponse(
            total_copilot_requests=total_reqs,
            total_interactions=total_reqs,
            total_gemini_calls=total_calls,
            cache_hits=hits,
            total_cache_hits=hits,
            cache_misses=misses,
            cache_hit_rate=hit_rate,
            cache_hit_rate_pct=hit_rate,
            total_input_tokens=in_tokens,
            total_output_tokens=out_tokens,
            total_tokens=total_tokens,
            active_cached_entries=active_caches,
            estimated_cost_display="Cost unavailable",
            cost_note="Live Gemini billing API is unavailable; exact verified token counts are tracked.",
            data_version=current_data_ver,
            current_data_version=current_data_ver,
        )
