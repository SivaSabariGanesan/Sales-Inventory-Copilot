import hashlib
import json
import logging
from typing import Optional, Dict, Any, Tuple
from backend.database.connection import get_db_connection

logger = logging.getLogger("retail_copilot.cache_service")


class CopilotCacheService:
    """Service to generate SHA-256 cache keys, store, and retrieve safe data-versioned Copilot responses."""

    @staticmethod
    def normalize_question(question: str) -> str:
        """Deterministic question normalization: trim, lowercase, collapse multiple whitespace."""
        return " ".join((question or "").strip().lower().split())

    @classmethod
    def generate_cache_key(
        cls,
        prompt_version: str,
        model: Optional[str] = None,
        normalized_question: Optional[str] = None,
        data_version: Optional[int] = None,
    ) -> str:
        """
        Generate deterministic SHA-256 cache key from prompt_version, model, normalized_question, and data_version.
        Can also be called with single argument (question) for convenience.
        """
        if model is None and normalized_question is None and data_version is None:
            from backend.services.gemini_service import GeminiService
            from backend.services.version_service import DataVersionService
            norm_q = cls.normalize_question(prompt_version)
            p_ver = GeminiService.PROMPT_VERSION
            m_name = GeminiService.get_active_model()
            d_ver = DataVersionService.get_data_version()
            raw_string = f"{p_ver}:{m_name}:{norm_q}:{d_ver}"
        else:
            raw_string = f"{str(prompt_version).strip()}:{str(model).strip()}:{str(normalized_question).strip()}:{data_version}"
        return hashlib.sha256(raw_string.encode("utf-8")).hexdigest()

    @classmethod
    def get_cached_response(
        cls,
        cache_key: str,
        current_data_version: int,
    ) -> Optional[Tuple[Dict[str, Any], int, int, int]]:
        """
        Retrieve cached response if it matches the current data version.
        Returns: (response_dict, gemini_calls, input_tokens, output_tokens) or None if MISS.
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT response_json, gemini_calls, input_tokens, output_tokens, data_version 
                    FROM copilot_cache 
                    WHERE cache_key = ?
                    """,
                    (cache_key,),
                )
                row = cursor.fetchone()
                if not row:
                    return None

                # Strict data version verification: stale data versions are never served
                if int(row["data_version"]) != current_data_version:
                    logger.debug(f"Cache entry data_version ({row['data_version']}) differs from current ({current_data_version}). Cache MISS.")
                    return None

                response_data = json.loads(row["response_json"])
                return (
                    response_data,
                    int(row["gemini_calls"]),
                    int(row["input_tokens"]),
                    int(row["output_tokens"]),
                )
        except Exception as e:
            logger.warning(f"Error reading from copilot_cache: {e}")
            return None

    @classmethod
    def store_cached_response(
        cls,
        cache_key: str,
        data_version: int,
        prompt_version: str,
        model: str,
        normalized_question: str,
        response_dict: Dict[str, Any],
        gemini_calls: int = 0,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None:
        """Persist a successful Copilot query response in the copilot_cache table."""
        try:
            response_json = json.dumps(response_dict)
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO copilot_cache 
                    (cache_key, data_version, prompt_version, model, normalized_question, response_json, gemini_calls, input_tokens, output_tokens)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(cache_key) DO UPDATE SET
                        data_version = excluded.data_version,
                        prompt_version = excluded.prompt_version,
                        model = excluded.model,
                        normalized_question = excluded.normalized_question,
                        response_json = excluded.response_json,
                        gemini_calls = excluded.gemini_calls,
                        input_tokens = excluded.input_tokens,
                        output_tokens = excluded.output_tokens,
                        created_at = CURRENT_TIMESTAMP
                    """,
                    (
                        cache_key,
                        data_version,
                        prompt_version,
                        model,
                        normalized_question,
                        response_json,
                        gemini_calls,
                        input_tokens,
                        output_tokens,
                    ),
                )
        except Exception as e:
            logger.warning(f"Error writing to copilot_cache: {e}")
