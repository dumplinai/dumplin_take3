"""
Subscription service for managing RevenueCat subscriptions.
Implements singleton pattern with MongoDB operations.
"""
import logging
from datetime import datetime
from typing import Optional
from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection

from app.core.config import settings
from app.models.subscription import (
    SubscriptionStatus,
    SubscriptionInDB,
    WebhookEvent,
)

logger = logging.getLogger(__name__)


class SubscriptionService:
    """
    Singleton service for subscription management.
    Handles MongoDB operations and RevenueCat webhook processing.
    """

    _instance: Optional["SubscriptionService"] = None

    def __new__(cls) -> "SubscriptionService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._client = MongoClient(settings.MONGODB_URL)
        self._db = self._client[settings.MONGODB_DB_NAME]
        self._collection: Collection = self._db["subscriptions"]

        # Create indexes
        self._collection.create_index([("user_id", ASCENDING)], unique=True)
        self._collection.create_index([("revenuecat_customer_id", ASCENDING)])

        self._initialized = True
        logger.info("SubscriptionService initialized with MongoDB")

    @property
    def collection(self) -> Collection:
        """Get the subscriptions collection."""
        return self._collection

    def get_subscription_by_user_id(self, user_id: str) -> Optional[SubscriptionInDB]:
        """
        Look up subscription status by user ID.

        Args:
            user_id: Firebase UID of the user

        Returns:
            SubscriptionInDB if found, None otherwise
        """
        doc = self._collection.find_one({"user_id": user_id})
        if doc:
            doc.pop("_id", None)
            return SubscriptionInDB(**doc)
        return None

    def upsert_subscription(self, user_id: str, data: dict) -> SubscriptionInDB:
        """
        Create or update a subscription record.

        Args:
            user_id: Firebase UID of the user
            data: Subscription data to upsert

        Returns:
            Updated SubscriptionInDB
        """
        data["user_id"] = user_id
        data["updated_at"] = datetime.utcnow()

        # If inserting new record, set created_at
        existing = self._collection.find_one({"user_id": user_id})
        if not existing:
            data["created_at"] = datetime.utcnow()

        self._collection.update_one(
            {"user_id": user_id},
            {"$set": data},
            upsert=True
        )

        return self.get_subscription_by_user_id(user_id)

    def handle_webhook_event(self, event: WebhookEvent) -> Optional[SubscriptionInDB]:
        """
        Parse webhook event and update subscription.

        Args:
            event: Parsed WebhookEvent from RevenueCat

        Returns:
            Updated SubscriptionInDB or None if event type not handled
        """
        event_type = event.event_type
        user_id = event.app_user_id or event.original_app_user_id

        if not user_id:
            logger.warning(f"Webhook event {event_type} missing user_id")
            return None

        logger.info(f"Processing webhook event: {event_type} for user: {user_id}")

        # Map event types to handlers
        handlers = {
            "INITIAL_PURCHASE": self._handle_initial_purchase,
            "RENEWAL": self._handle_renewal,
            "CANCELLATION": self._handle_cancellation,
            "EXPIRATION": self._handle_expiration,
            "BILLING_ISSUE": self._handle_billing_issue,
            "SUBSCRIBER_ALIAS": self._handle_subscriber_alias,
            "UNCANCELLATION": self._handle_uncancellation,
            "NON_RENEWING_PURCHASE": self._handle_initial_purchase,
            "SUBSCRIPTION_PAUSED": self._handle_cancellation,
            "PRODUCT_CHANGE": self._handle_product_change,
        }

        handler = handlers.get(event_type)
        if handler:
            return handler(user_id, event)
        else:
            logger.info(f"Unhandled webhook event type: {event_type}")
            return None

    def _handle_initial_purchase(
        self, user_id: str, event: WebhookEvent
    ) -> SubscriptionInDB:
        """Handle initial purchase or trial start."""
        status = SubscriptionStatus.TRIALING if event.is_trial else SubscriptionStatus.ACTIVE
        entitlements = []
        if event.entitlement_id:
            entitlements = [event.entitlement_id]

        expires_at = None
        if event.expiration_at_ms:
            expires_at = datetime.utcfromtimestamp(event.expiration_at_ms / 1000)

        data = {
            "status": status.value,
            "entitlements": entitlements,
            "current_product_id": event.product_id,
            "expires_at": expires_at,
            "revenuecat_customer_id": event.original_app_user_id,
        }

        logger.info(f"Initial purchase for user {user_id}: {status.value}")
        return self.upsert_subscription(user_id, data)

    def _handle_renewal(self, user_id: str, event: WebhookEvent) -> SubscriptionInDB:
        """Handle subscription renewal."""
        entitlements = []
        if event.entitlement_id:
            entitlements = [event.entitlement_id]

        expires_at = None
        if event.expiration_at_ms:
            expires_at = datetime.utcfromtimestamp(event.expiration_at_ms / 1000)

        data = {
            "status": SubscriptionStatus.ACTIVE.value,
            "entitlements": entitlements,
            "current_product_id": event.product_id,
            "expires_at": expires_at,
        }

        logger.info(f"Renewal for user {user_id}")
        return self.upsert_subscription(user_id, data)

    def _handle_cancellation(
        self, user_id: str, event: WebhookEvent
    ) -> SubscriptionInDB:
        """
        Handle cancellation - subscription still active until expiration.
        Status changes to CANCELLED but user keeps access until expires_at.
        """
        expires_at = None
        if event.expiration_at_ms:
            expires_at = datetime.utcfromtimestamp(event.expiration_at_ms / 1000)

        # Keep entitlements - they're still valid until expiration
        existing = self.get_subscription_by_user_id(user_id)
        entitlements = existing.entitlements if existing else []

        data = {
            "status": SubscriptionStatus.CANCELLED.value,
            "expires_at": expires_at,
            "entitlements": entitlements,
        }

        logger.info(f"Cancellation for user {user_id}, expires at: {expires_at}")
        return self.upsert_subscription(user_id, data)

    def _handle_uncancellation(
        self, user_id: str, event: WebhookEvent
    ) -> SubscriptionInDB:
        """Handle uncancellation - user reactivated their subscription."""
        entitlements = []
        if event.entitlement_id:
            entitlements = [event.entitlement_id]

        expires_at = None
        if event.expiration_at_ms:
            expires_at = datetime.utcfromtimestamp(event.expiration_at_ms / 1000)

        data = {
            "status": SubscriptionStatus.ACTIVE.value,
            "entitlements": entitlements,
            "current_product_id": event.product_id,
            "expires_at": expires_at,
        }

        logger.info(f"Uncancellation for user {user_id}")
        return self.upsert_subscription(user_id, data)

    def _handle_expiration(
        self, user_id: str, event: WebhookEvent
    ) -> SubscriptionInDB:
        """Handle subscription expiration - remove all entitlements."""
        data = {
            "status": SubscriptionStatus.EXPIRED.value,
            "entitlements": [],
            "current_product_id": None,
            "expires_at": datetime.utcnow(),
        }

        logger.info(f"Expiration for user {user_id}")
        return self.upsert_subscription(user_id, data)

    def _handle_billing_issue(
        self, user_id: str, event: WebhookEvent
    ) -> Optional[SubscriptionInDB]:
        """
        Handle billing issue - log it but don't change status yet.
        RevenueCat will send EXPIRATION if payment fails after grace period.
        """
        logger.warning(f"Billing issue for user {user_id}")
        # For MVP, we just log it. Don't change status - wait for EXPIRATION
        return self.get_subscription_by_user_id(user_id)

    def _handle_subscriber_alias(
        self, user_id: str, event: WebhookEvent
    ) -> Optional[SubscriptionInDB]:
        """Handle subscriber alias - update revenuecat_customer_id."""
        data = {
            "revenuecat_customer_id": event.original_app_user_id,
        }
        logger.info(f"Subscriber alias updated for user {user_id}")
        return self.upsert_subscription(user_id, data)

    def _handle_product_change(
        self, user_id: str, event: WebhookEvent
    ) -> SubscriptionInDB:
        """Handle product change (upgrade/downgrade)."""
        entitlements = []
        if event.entitlement_id:
            entitlements = [event.entitlement_id]

        expires_at = None
        if event.expiration_at_ms:
            expires_at = datetime.utcfromtimestamp(event.expiration_at_ms / 1000)

        data = {
            "status": SubscriptionStatus.ACTIVE.value,
            "entitlements": entitlements,
            "current_product_id": event.product_id,
            "expires_at": expires_at,
        }

        logger.info(f"Product change for user {user_id}: {event.product_id}")
        return self.upsert_subscription(user_id, data)

    def is_user_pro(self, user_id: str) -> bool:
        """
        Simple helper to check if user has active pro entitlement.

        Args:
            user_id: Firebase UID of the user

        Returns:
            True if user has active pro subscription, False otherwise
        """
        subscription = self.get_subscription_by_user_id(user_id)

        if not subscription:
            return False

        # Check if subscription is active or cancelled but not yet expired
        if subscription.status == SubscriptionStatus.EXPIRED:
            return False

        # For cancelled subscriptions, check if still within valid period
        if subscription.status == SubscriptionStatus.CANCELLED:
            if subscription.expires_at and subscription.expires_at > datetime.utcnow():
                return "pro" in subscription.entitlements
            return False

        # Active or trialing
        return "pro" in subscription.entitlements

    def check_message_limit(
        self,
        user_id: str,
        current_message_count: int,
        week_start_ms: Optional[int] = None
    ) -> tuple[bool, Optional[int]]:
        """
        Check if user can send a message based on their subscription.

        Args:
            user_id: Firebase UID
            current_message_count: Current message count from frontend
            week_start_ms: Week start timestamp from frontend (ms)

        Returns:
            Tuple of (can_send: bool, remaining_messages: Optional[int])
            remaining_messages is None for pro users
        """
        if self.is_user_pro(user_id):
            return (True, None)

        # Check if week has reset
        if week_start_ms:
            week_start = datetime.utcfromtimestamp(week_start_ms / 1000)
            now = datetime.utcnow()
            # If week start is more than 7 days ago, reset count
            if (now - week_start).days >= 7:
                current_message_count = 0

        limit = settings.FREE_TIER_WEEKLY_MESSAGE_LIMIT
        remaining = max(0, limit - current_message_count)

        return (current_message_count < limit, remaining)


# Global singleton instance
subscription_service = SubscriptionService()
