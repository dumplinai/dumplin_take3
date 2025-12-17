"""
Unit tests for subscription service and API endpoints.
"""
import pytest
import hmac
import hashlib
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.models.subscription import (
    SubscriptionStatus,
    SubscriptionInDB,
    WebhookEvent,
)


class TestWebhookEvent:
    """Tests for WebhookEvent model."""

    def test_parse_initial_purchase_event(self):
        """Test parsing INITIAL_PURCHASE webhook event."""
        payload = {
            "api_version": "1.0",
            "event": {
                "type": "INITIAL_PURCHASE",
                "app_user_id": "firebase_uid_123",
                "original_app_user_id": "firebase_uid_123",
                "product_id": "dumplin-pro-monthly",
                "entitlement_ids": ["pro"],
                "period_type": "NORMAL",
                "expiration_at_ms": 1735689600000,
            }
        }

        event = WebhookEvent(**payload)

        assert event.event_type == "INITIAL_PURCHASE"
        assert event.app_user_id == "firebase_uid_123"
        assert event.product_id == "dumplin-pro-monthly"
        assert event.entitlement_id == "pro"
        assert event.is_trial is False

    def test_parse_trial_event(self):
        """Test parsing event with trial period."""
        payload = {
            "api_version": "1.0",
            "event": {
                "type": "INITIAL_PURCHASE",
                "app_user_id": "firebase_uid_123",
                "original_app_user_id": "firebase_uid_123",
                "product_id": "dumplin-pro-yearly",
                "entitlement_ids": ["pro"],
                "period_type": "TRIAL",
                "expiration_at_ms": 1735689600000,
            }
        }

        event = WebhookEvent(**payload)

        assert event.is_trial is True

    def test_parse_expiration_event(self):
        """Test parsing EXPIRATION webhook event."""
        payload = {
            "api_version": "1.0",
            "event": {
                "type": "EXPIRATION",
                "app_user_id": "firebase_uid_123",
                "original_app_user_id": "firebase_uid_123",
                "product_id": "dumplin-pro-monthly",
                "entitlement_ids": [],
            }
        }

        event = WebhookEvent(**payload)

        assert event.event_type == "EXPIRATION"
        assert event.entitlement_id is None


class TestSubscriptionService:
    """Tests for SubscriptionService."""

    @pytest.fixture
    def mock_collection(self):
        """Create a mock MongoDB collection."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_collection):
        """Create SubscriptionService with mocked MongoDB."""
        with patch("app.services.subscription_service.MongoClient") as mock_client:
            mock_db = MagicMock()
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            mock_client.return_value.__getitem__ = MagicMock(return_value=mock_db)

            # Reset singleton
            from app.services.subscription_service import SubscriptionService
            SubscriptionService._instance = None

            service = SubscriptionService()
            service._collection = mock_collection
            return service

    def test_get_subscription_by_user_id_found(self, service, mock_collection):
        """Test getting subscription for existing user."""
        mock_collection.find_one.return_value = {
            "_id": "mongo_id",
            "user_id": "user_123",
            "status": "active",
            "entitlements": ["pro"],
            "current_product_id": "dumplin-pro-monthly",
            "expires_at": datetime.utcnow() + timedelta(days=30),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = service.get_subscription_by_user_id("user_123")

        assert result is not None
        assert result.user_id == "user_123"
        assert result.status == SubscriptionStatus.ACTIVE
        assert "pro" in result.entitlements

    def test_get_subscription_by_user_id_not_found(self, service, mock_collection):
        """Test getting subscription for non-existing user."""
        mock_collection.find_one.return_value = None

        result = service.get_subscription_by_user_id("nonexistent_user")

        assert result is None

    def test_is_user_pro_active_subscription(self, service, mock_collection):
        """Test is_user_pro returns True for active subscription with pro entitlement."""
        mock_collection.find_one.return_value = {
            "user_id": "user_123",
            "status": "active",
            "entitlements": ["pro"],
            "expires_at": datetime.utcnow() + timedelta(days=30),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = service.is_user_pro("user_123")

        assert result is True

    def test_is_user_pro_expired_subscription(self, service, mock_collection):
        """Test is_user_pro returns False for expired subscription."""
        mock_collection.find_one.return_value = {
            "user_id": "user_123",
            "status": "expired",
            "entitlements": [],
            "expires_at": datetime.utcnow() - timedelta(days=1),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = service.is_user_pro("user_123")

        assert result is False

    def test_is_user_pro_no_subscription(self, service, mock_collection):
        """Test is_user_pro returns False for user with no subscription record."""
        mock_collection.find_one.return_value = None

        result = service.is_user_pro("user_123")

        assert result is False

    def test_is_user_pro_cancelled_but_not_expired(self, service, mock_collection):
        """Test is_user_pro returns True for cancelled subscription still within valid period."""
        mock_collection.find_one.return_value = {
            "user_id": "user_123",
            "status": "cancelled",
            "entitlements": ["pro"],
            "expires_at": datetime.utcnow() + timedelta(days=5),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = service.is_user_pro("user_123")

        assert result is True

    def test_check_message_limit_pro_user(self, service, mock_collection):
        """Test check_message_limit allows unlimited messages for pro user."""
        mock_collection.find_one.return_value = {
            "user_id": "user_123",
            "status": "active",
            "entitlements": ["pro"],
            "expires_at": datetime.utcnow() + timedelta(days=30),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        can_send, remaining = service.check_message_limit("user_123", 100, None)

        assert can_send is True
        assert remaining is None

    def test_check_message_limit_free_user_under_limit(self, service, mock_collection):
        """Test check_message_limit allows messages for free user under limit."""
        mock_collection.find_one.return_value = None

        can_send, remaining = service.check_message_limit("user_123", 10, None)

        assert can_send is True
        assert remaining == 10  # 20 - 10 = 10

    def test_check_message_limit_free_user_at_limit(self, service, mock_collection):
        """Test check_message_limit blocks messages for free user at limit."""
        mock_collection.find_one.return_value = None

        can_send, remaining = service.check_message_limit("user_123", 20, None)

        assert can_send is False
        assert remaining == 0

    def test_check_message_limit_free_user_over_limit(self, service, mock_collection):
        """Test check_message_limit blocks messages for free user over limit."""
        mock_collection.find_one.return_value = None

        can_send, remaining = service.check_message_limit("user_123", 25, None)

        assert can_send is False
        assert remaining == 0

    def test_handle_webhook_initial_purchase(self, service, mock_collection):
        """Test handling INITIAL_PURCHASE webhook event."""
        mock_collection.find_one.return_value = None

        event = WebhookEvent(**{
            "api_version": "1.0",
            "event": {
                "type": "INITIAL_PURCHASE",
                "app_user_id": "user_123",
                "original_app_user_id": "user_123",
                "product_id": "dumplin-pro-monthly",
                "entitlement_ids": ["pro"],
                "period_type": "NORMAL",
                "expiration_at_ms": int((datetime.utcnow() + timedelta(days=30)).timestamp() * 1000),
            }
        })

        service.handle_webhook_event(event)

        # Verify update_one was called with correct data
        mock_collection.update_one.assert_called_once()
        call_args = mock_collection.update_one.call_args
        assert call_args[0][0] == {"user_id": "user_123"}
        assert call_args[0][1]["$set"]["status"] == "active"
        assert "pro" in call_args[0][1]["$set"]["entitlements"]

    def test_handle_webhook_expiration(self, service, mock_collection):
        """Test handling EXPIRATION webhook event."""
        mock_collection.find_one.return_value = {
            "user_id": "user_123",
            "status": "active",
            "entitlements": ["pro"],
        }

        event = WebhookEvent(**{
            "api_version": "1.0",
            "event": {
                "type": "EXPIRATION",
                "app_user_id": "user_123",
                "original_app_user_id": "user_123",
            }
        })

        service.handle_webhook_event(event)

        # Verify update_one was called with expired status
        mock_collection.update_one.assert_called()
        call_args = mock_collection.update_one.call_args
        assert call_args[0][1]["$set"]["status"] == "expired"
        assert call_args[0][1]["$set"]["entitlements"] == []

    def test_handle_webhook_renewal(self, service, mock_collection):
        """Test handling RENEWAL webhook event."""
        mock_collection.find_one.return_value = {
            "user_id": "user_123",
            "status": "active",
            "entitlements": ["pro"],
        }

        event = WebhookEvent(**{
            "api_version": "1.0",
            "event": {
                "type": "RENEWAL",
                "app_user_id": "user_123",
                "original_app_user_id": "user_123",
                "product_id": "dumplin-pro-monthly",
                "entitlement_ids": ["pro"],
                "expiration_at_ms": int((datetime.utcnow() + timedelta(days=30)).timestamp() * 1000),
            }
        })

        service.handle_webhook_event(event)

        mock_collection.update_one.assert_called()
        call_args = mock_collection.update_one.call_args
        assert call_args[0][1]["$set"]["status"] == "active"

    def test_handle_webhook_cancellation(self, service, mock_collection):
        """Test handling CANCELLATION webhook event."""
        mock_collection.find_one.return_value = {
            "user_id": "user_123",
            "status": "active",
            "entitlements": ["pro"],
        }

        event = WebhookEvent(**{
            "api_version": "1.0",
            "event": {
                "type": "CANCELLATION",
                "app_user_id": "user_123",
                "original_app_user_id": "user_123",
                "expiration_at_ms": int((datetime.utcnow() + timedelta(days=10)).timestamp() * 1000),
            }
        })

        service.handle_webhook_event(event)

        mock_collection.update_one.assert_called()
        call_args = mock_collection.update_one.call_args
        # Status changes to cancelled but entitlements are kept
        assert call_args[0][1]["$set"]["status"] == "cancelled"


class TestWebhookSignature:
    """Tests for webhook signature verification."""

    def test_verify_signature_valid(self):
        """Test webhook signature verification with valid signature."""
        from app.api.subscriptions import verify_webhook_signature

        secret = "test_secret"
        payload = b'{"test": "payload"}'
        signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

        with patch("app.api.subscriptions.settings") as mock_settings:
            mock_settings.REVENUECAT_WEBHOOK_SECRET = secret
            result = verify_webhook_signature(payload, signature)

        assert result is True

    def test_verify_signature_invalid(self):
        """Test webhook signature verification with invalid signature."""
        from app.api.subscriptions import verify_webhook_signature

        secret = "test_secret"
        payload = b'{"test": "payload"}'
        wrong_signature = "wrong_signature"

        with patch("app.api.subscriptions.settings") as mock_settings:
            mock_settings.REVENUECAT_WEBHOOK_SECRET = secret
            result = verify_webhook_signature(payload, wrong_signature)

        assert result is False

    def test_verify_signature_no_secret_configured(self):
        """Test webhook signature verification when no secret is configured."""
        from app.api.subscriptions import verify_webhook_signature

        payload = b'{"test": "payload"}'

        with patch("app.api.subscriptions.settings") as mock_settings:
            mock_settings.REVENUECAT_WEBHOOK_SECRET = None
            result = verify_webhook_signature(payload, "any_signature")

        # Should return True when no secret is configured (dev mode)
        assert result is True


class TestSubscriptionAPI:
    """Tests for subscription API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        return TestClient(app)

    def test_webhook_endpoint_returns_200(self, client):
        """Test webhook endpoint returns 200 for valid payload."""
        with patch("app.api.subscriptions.subscription_service") as mock_service:
            payload = {
                "api_version": "1.0",
                "event": {
                    "type": "INITIAL_PURCHASE",
                    "app_user_id": "user_123",
                    "original_app_user_id": "user_123",
                    "product_id": "dumplin-pro-monthly",
                }
            }

            response = client.post("/api/v1/webhooks/revenuecat", json=payload)

            assert response.status_code == 200
            assert response.json()["status"] == "ok"

    def test_subscription_status_endpoint(self, client):
        """Test subscription status endpoint returns correct data."""
        with patch("app.api.subscriptions.subscription_service") as mock_service:
            mock_service.get_subscription_by_user_id.return_value = SubscriptionInDB(
                user_id="user_123",
                status=SubscriptionStatus.ACTIVE,
                entitlements=["pro"],
                current_product_id="dumplin-pro-monthly",
                expires_at=datetime.utcnow() + timedelta(days=30),
            )
            mock_service.is_user_pro.return_value = True
            mock_service.check_message_limit.return_value = (True, None)

            response = client.get("/api/v1/subscriptions/status/user_123")

            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == "user_123"
            assert data["is_pro"] is True
            assert "pro" in data["entitlements"]

    def test_subscription_status_free_user(self, client):
        """Test subscription status endpoint for free user."""
        with patch("app.api.subscriptions.subscription_service") as mock_service:
            mock_service.get_subscription_by_user_id.return_value = None
            mock_service.is_user_pro.return_value = False
            mock_service.check_message_limit.return_value = (True, 15)

            response = client.get(
                "/api/v1/subscriptions/status/user_123",
                params={"message_count": 5}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["is_pro"] is False
            assert data["remaining_messages"] == 15


class TestChatRateLimiting:
    """Tests for chat endpoint rate limiting."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from main import app
        return TestClient(app)

    def test_chat_allowed_for_pro_user(self, client):
        """Test chat is allowed for pro user."""
        with patch("app.api.chat.subscription_service") as mock_service:
            mock_service.is_user_pro.return_value = True
            mock_service.check_message_limit.return_value = (True, None)

            response = client.post("/api/v1/chat", json={
                "user_id": "user_123",
                "message": "Hello",
                "message_count": 100,
            })

            assert response.status_code == 200
            data = response.json()
            assert data["is_pro"] is True
            assert data["remaining_messages"] is None

    def test_chat_allowed_for_free_user_under_limit(self, client):
        """Test chat is allowed for free user under message limit."""
        with patch("app.api.chat.subscription_service") as mock_service:
            mock_service.is_user_pro.return_value = False
            mock_service.check_message_limit.return_value = (True, 10)

            response = client.post("/api/v1/chat", json={
                "user_id": "user_123",
                "message": "Hello",
                "message_count": 10,
            })

            assert response.status_code == 200
            data = response.json()
            assert data["is_pro"] is False
            assert data["remaining_messages"] == 10

    def test_chat_blocked_for_free_user_at_limit(self, client):
        """Test chat is blocked for free user at message limit."""
        with patch("app.api.chat.subscription_service") as mock_service:
            mock_service.is_user_pro.return_value = False
            mock_service.check_message_limit.return_value = (False, 0)

            response = client.post("/api/v1/chat", json={
                "user_id": "user_123",
                "message": "Hello",
                "message_count": 20,
            })

            assert response.status_code == 429
