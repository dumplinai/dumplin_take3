"""
Chat API endpoint with subscription-based rate limiting.
"""
import logging
from typing import Optional
from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException, Header, Depends

from app.core.config import settings
from app.services.subscription_service import subscription_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


def require_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """
    Dependency to require API key for protected endpoints.
    """
    if not settings.API_KEY:
        return "dev"

    if not x_api_key or x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    return x_api_key


class ChatRequest(BaseModel):
    """Chat request model."""
    user_id: str = Field(..., description="Firebase UID of the user")
    message: str = Field(..., description="User's chat message")
    message_count: int = Field(default=0, description="Current message count this week")
    week_start_ms: Optional[int] = Field(None, description="Week start timestamp in ms")


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str = Field(..., description="AI response")
    is_pro: bool = Field(default=False, description="Whether user has pro subscription")
    remaining_messages: Optional[int] = Field(
        None,
        description="Remaining messages this week (None for pro users)"
    )


class RateLimitError(BaseModel):
    """Rate limit error response."""
    detail: str
    remaining_messages: int = 0
    weekly_limit: int
    is_pro: bool = False


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    _api_key: str = Depends(require_api_key),
):
    """
    Process a chat message with subscription-based rate limiting.

    For free users:
    - Limited to 20 messages per week
    - Returns 429 if limit exceeded

    For pro users:
    - Unlimited messages
    - remaining_messages is None in response
    """
    user_id = request.user_id
    message_count = request.message_count
    week_start_ms = request.week_start_ms

    # Check subscription and message limit
    is_pro = subscription_service.is_user_pro(user_id)
    can_send, remaining = subscription_service.check_message_limit(
        user_id, message_count, week_start_ms
    )

    if not can_send:
        logger.info(f"Rate limit exceeded for user {user_id}")
        raise HTTPException(
            status_code=429,
            detail={
                "message": f"Weekly message limit of {settings.FREE_TIER_WEEKLY_MESSAGE_LIMIT} reached. Upgrade to Pro for unlimited messages.",
                "remaining_messages": 0,
                "weekly_limit": settings.FREE_TIER_WEEKLY_MESSAGE_LIMIT,
                "is_pro": False,
            }
        )

    # Process chat message
    # NOTE: This is a placeholder - integrate with your actual chat/AI service
    logger.info(f"Processing chat for user {user_id}, is_pro: {is_pro}")

    # TODO: Replace with actual AI chat processing
    response_text = f"Received your message: {request.message[:50]}..."

    return ChatResponse(
        response=response_text,
        is_pro=is_pro,
        remaining_messages=remaining,
    )


@router.get("/chat/limit/{user_id}")
async def get_message_limit(
    user_id: str,
    message_count: int = 0,
    week_start_ms: Optional[int] = None,
    _api_key: str = Depends(require_api_key),
):
    """
    Get current message limit status for a user.

    Args:
        user_id: Firebase UID of the user
        message_count: Current message count from frontend
        week_start_ms: Week start timestamp in milliseconds

    Returns:
        Message limit status including remaining messages
    """
    is_pro = subscription_service.is_user_pro(user_id)
    can_send, remaining = subscription_service.check_message_limit(
        user_id, message_count, week_start_ms
    )

    return {
        "user_id": user_id,
        "is_pro": is_pro,
        "can_send": can_send,
        "remaining_messages": remaining,
        "weekly_limit": settings.FREE_TIER_WEEKLY_MESSAGE_LIMIT,
    }
