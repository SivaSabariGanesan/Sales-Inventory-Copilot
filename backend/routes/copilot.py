from fastapi import APIRouter, HTTPException
import logging

from backend.models.copilot import CopilotQueryRequest, CopilotQueryResponse
from backend.services.copilot_service import CopilotService

logger = logging.getLogger("retail_copilot.routes.copilot")

router = APIRouter(prefix="/api/copilot", tags=["AI Copilot"])


@router.post("/query", response_model=CopilotQueryResponse)
async def query_copilot(request: CopilotQueryRequest):
    """
    Process natural language questions from retail managers,
    extracting intent, mapping to deterministic analytics,
    and returning grounded answers with full numerical evidence.
    """
    try:
        response = CopilotService.process_query(request.question)
        return response
    except Exception as e:
        logger.error(f"Error processing copilot query: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error processing Copilot query: {str(e)}",
        )
