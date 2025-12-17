"""
Subscription models for RevenueCat integration.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class SubscriptionStatus(str, Enum):
    """Subscription status enum."""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    TRIALING = "trialing"


class SubscriptionInDB(BaseModel):
    """Subscription record stored in MongoDB."""
    user_id: str = Field(..., description="Firebase UID of the user")
    revenuecat_customer_id: Optional[str] = Field(None, description="RevenueCat customer ID")
    status: SubscriptionStatus = Field(default=SubscriptionStatus.EXPIRED)
    entitlements: List[str] = Field(default_factory=list, description="List of active entitlements")
    current_product_id: Optional[str] = Field(None, description="Current subscription product ID")
    expires_at: Optional[datetime] = Field(None, description="When the subscription expires")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class WebhookEventSubscriber(BaseModel):
    """Subscriber info from RevenueCat webhook."""
    original_app_user_id: str
    aliases: List[str] = Field(default_factory=list)
    entitlements: dict = Field(default_factory=dict)


class WebhookEvent(BaseModel):
    """RevenueCat webhook event payload."""
    api_version: str = Field(default="1.0")
    event: dict = Field(..., description="The event data")

    @property
    def event_type(self) -> str:
        """Get the event type."""
        return self.event.get("type", "")

    @property
    def app_user_id(self) -> str:
        """Get the app user ID (Firebase UID)."""
        return self.event.get("app_user_id", "")

    @property
    def original_app_user_id(self) -> str:
        """Get the original app user ID."""
        return self.event.get("original_app_user_id", "")

    @property
    def product_id(self) -> Optional[str]:
        """Get the product ID."""
        return self.event.get("product_id")

    @property
    def entitlement_id(self) -> Optional[str]:
        """Get the entitlement ID."""
        entitlement_ids = self.event.get("entitlement_ids", [])
        return entitlement_ids[0] if entitlement_ids else None

    @property
    def expiration_at_ms(self) -> Optional[int]:
        """Get expiration timestamp in milliseconds."""
        return self.event.get("expiration_at_ms")

    @property
    def is_trial(self) -> bool:
        """Check if this is a trial."""
        return self.event.get("period_type") == "TRIAL"


class SubscriptionStatusResponse(BaseModel):
    """API response for subscription status."""
    user_id: str
    is_pro: bool = Field(default=False, description="Whether user has active pro subscription")
    status: SubscriptionStatus = Field(default=SubscriptionStatus.EXPIRED)
    entitlements: List[str] = Field(default_factory=list)
    current_product_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    remaining_messages: Optional[int] = Field(
        None,
        description="Remaining messages this week (None if pro user)"
    )
    weekly_message_limit: int = Field(
        default=20,
        description="Weekly message limit for free users"
    )

    class Config:
        use_enum_values = True


class MessageLimitResponse(BaseModel):
    """Response for message limit check."""
    allowed: bool = Field(..., description="Whether the user can send a message")
    is_pro: bool = Field(default=False, description="Whether user has pro subscription")
    remaining_messages: Optional[int] = Field(
        None,
        description="Remaining messages this week (None if pro user)"
    )
    weekly_message_limit: int = Field(default=20)
    message: Optional[str] = Field(None, description="Error message if not allowed")
