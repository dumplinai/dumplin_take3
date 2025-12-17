"""
Subscription API endpoints for RevenueCat webhook and subscription status.
"""
import hmac
import hashlib
import logging
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Header, Depends
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.models.subscription import (
    WebhookEvent,
    SubscriptionStatusResponse,
    SubscriptionStatus,
    MessageLimitResponse,
)
from app.services.subscription_service import subscription_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["subscriptions"])


def require_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """
    Dependency to require API key for protected endpoints.
    """
    if not settings.API_KEY:
        # If no API key configured, allow all requests (development mode)
        return "dev"

    if not x_api_key or x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    return x_api_key


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Verify RevenueCat webhook signature.

    Args:
        payload: Raw request body
        signature: Signature from X-RevenueCat-Signature header

    Returns:
        True if signature is valid, False otherwise
    """
    if not settings.REVENUECAT_WEBHOOK_SECRET:
        logger.warning("REVENUECAT_WEBHOOK_SECRET not configured, skipping verification")
        return True

    expected_signature = hmac.new(
        settings.REVENUECAT_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature)


@router.post("/webhooks/revenuecat")
async def receive_revenuecat_webhook(
    request: Request,
    x_revenuecat_signature: Optional[str] = Header(None, alias="X-RevenueCat-Signature"),
):
    """
    Receive and process RevenueCat webhook events.

    This endpoint receives subscription events from RevenueCat and updates
    the subscription status in MongoDB.

    Supported event types:
    - INITIAL_PURCHASE: User subscribes for first time
    - RENEWAL: Subscription renews
    - CANCELLATION: User cancels (still active until period ends)
    - EXPIRATION: Subscription actually expires
    - BILLING_ISSUE: Payment failed
    - SUBSCRIBER_ALIAS: User ID aliasing
    """
    # Get raw body for signature verification
    body = await request.body()

    # Verify signature if configured
    if settings.REVENUECAT_WEBHOOK_SECRET and x_revenuecat_signature:
        if not verify_webhook_signature(body, x_revenuecat_signature):
            logger.warning("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        # Parse the webhook payload
        payload = await request.json()
        event = WebhookEvent(**payload)

        logger.info(f"Received webhook event: {event.event_type}")

        # Process the event
        subscription_service.handle_webhook_event(event)

        # RevenueCat expects a quick 200 response
        return JSONResponse(
            status_code=200,
            content={"status": "ok", "event_type": event.event_type}
        )

    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        # Still return 200 to prevent RevenueCat from retrying
        # Log the error for investigation
        return JSONResponse(
            status_code=200,
            content={"status": "error", "message": str(e)}
        )


@router.get("/subscriptions/status/{user_id}", response_model=SubscriptionStatusResponse)
async def get_subscription_status(
    user_id: str,
    message_count: int = 0,
    week_start_ms: Optional[int] = None,
    _api_key: str = Depends(require_api_key),
):
    """
    Get subscription status for a user.

    Args:
        user_id: Firebase UID of the user
        message_count: Current message count from frontend (optional)
        week_start_ms: Week start timestamp in milliseconds (optional)

    Returns:
        SubscriptionStatusResponse with subscription details and remaining messages
    """
    subscription = subscription_service.get_subscription_by_user_id(user_id)
    is_pro = subscription_service.is_user_pro(user_id)

    # Calculate remaining messages for free users
    remaining_messages = None
    if not is_pro:
        _, remaining_messages = subscription_service.check_message_limit(
            user_id, message_count, week_start_ms
        )

    if subscription:
        return SubscriptionStatusResponse(
            user_id=user_id,
            is_pro=is_pro,
            status=subscription.status,
            entitlements=subscription.entitlements,
            current_product_id=subscription.current_product_id,
            expires_at=subscription.expires_at,
            remaining_messages=remaining_messages,
            weekly_message_limit=settings.FREE_TIER_WEEKLY_MESSAGE_LIMIT,
        )
    else:
        # User has no subscription record - free tier
        return SubscriptionStatusResponse(
            user_id=user_id,
            is_pro=False,
            status=SubscriptionStatus.EXPIRED,
            entitlements=[],
            current_product_id=None,
            expires_at=None,
            remaining_messages=settings.FREE_TIER_WEEKLY_MESSAGE_LIMIT - message_count,
            weekly_message_limit=settings.FREE_TIER_WEEKLY_MESSAGE_LIMIT,
        )


@router.post("/subscriptions/check-message-limit/{user_id}", response_model=MessageLimitResponse)
async def check_message_limit(
    user_id: str,
    message_count: int = 0,
    week_start_ms: Optional[int] = None,
    _api_key: str = Depends(require_api_key),
):
    """
    Check if a user can send a message based on their subscription status.

    This endpoint is called before processing a chat message to enforce
    rate limiting for free users.

    Args:
        user_id: Firebase UID of the user
        message_count: Current message count from frontend
        week_start_ms: Week start timestamp in milliseconds

    Returns:
        MessageLimitResponse indicating if the message is allowed
    """
    is_pro = subscription_service.is_user_pro(user_id)
    can_send, remaining = subscription_service.check_message_limit(
        user_id, message_count, week_start_ms
    )

    if can_send:
        return MessageLimitResponse(
            allowed=True,
            is_pro=is_pro,
            remaining_messages=remaining,
            weekly_message_limit=settings.FREE_TIER_WEEKLY_MESSAGE_LIMIT,
        )
    else:
        return MessageLimitResponse(
            allowed=False,
            is_pro=False,
            remaining_messages=0,
            weekly_message_limit=settings.FREE_TIER_WEEKLY_MESSAGE_LIMIT,
            message=f"Weekly message limit of {settings.FREE_TIER_WEEKLY_MESSAGE_LIMIT} reached. Upgrade to Pro for unlimited messages.",
        )
