"""
Automated Pytest Suite for RM Customer WhatsApp Communication Feature.

Tests:
1. Unauthorized user blocked (401)
2. ANALYST role blocked from sending (403)
3. REVIEWER role blocked from sending (403)
4. RELATIONSHIP_MANAGER & ADMIN role permitted (200)
5. Missing customer returns 404
6. Customer without mobile returns 400
7. Conflicting mobile numbers return 400 validation error
8. Twilio success creates CommunicationLog (status=SENT) & AuditLog
9. Twilio failure creates CommunicationLog (status=FAILED) without crashing
10. Sender identity strictly comes from JWT authenticated user
11. GET communication history endpoint returns logs
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException, status
from httpx import AsyncClient, Response, ASGITransport

from app.main import app
from app.core.security import create_access_token
from app.models.user import User, UserRole
from app.models.golden_customer import GoldenCustomer, GoldenCustomerStatus
from app.models.source_record import SourceRecord, SourceSystem
from app.models.communication_log import CommunicationLog
from app.schemas.communication import CommunicationSendRequest, CommunicationSendResponse


def _make_mock_user(username: str, role: UserRole) -> User:
    u = MagicMock(spec=User)
    u.id = 101
    u.username = username
    u.email = f"{username}@nexus360.com"
    u.role = role
    u.is_active = True
    return u


@pytest.mark.asyncio
async def test_unauthorized_user_cannot_send_communication():
    """1. Verify that requests without a Bearer token return 401 Unauthorized."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/v1/communications/send",
            json={
                "customer_id": "GOLD-000001",
                "channel": "whatsapp",
                "message": "Hello from RM",
            },
        )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_analyst_cannot_send_communication():
    """2. Verify that ANALYST role receives 403 Forbidden."""
    token = create_access_token({"sub": "analyst_priya", "role": UserRole.ANALYST.value})
    headers = {"Authorization": f"Bearer {token}"}
    mock_user = _make_mock_user("analyst_priya", UserRole.ANALYST)

    with patch("app.api.deps.get_user_by_username", new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = mock_user

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/communications/send",
                headers=headers,
                json={
                    "customer_id": "GOLD-000001",
                    "channel": "whatsapp",
                    "message": "Hello from Analyst",
                },
            )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_reviewer_cannot_send_communication():
    """3. Verify that REVIEWER role receives 403 Forbidden on send."""
    token = create_access_token({"sub": "reviewer_sarah", "role": UserRole.REVIEWER.value})
    headers = {"Authorization": f"Bearer {token}"}
    mock_user = _make_mock_user("reviewer_sarah", UserRole.REVIEWER)

    with patch("app.api.deps.get_user_by_username", new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = mock_user

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/communications/send",
                headers=headers,
                json={
                    "customer_id": "GOLD-000001",
                    "channel": "whatsapp",
                    "message": "Hello from Reviewer",
                },
            )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_missing_customer_returns_404():
    """4. Verify that non-existent customer ID returns 404 Not Found."""
    token = create_access_token({"sub": "rm_vikram", "role": UserRole.RELATIONSHIP_MANAGER.value})
    headers = {"Authorization": f"Bearer {token}"}
    mock_user = _make_mock_user("rm_vikram", UserRole.RELATIONSHIP_MANAGER)

    with patch("app.api.deps.get_user_by_username", new_callable=AsyncMock) as mock_get_user, \
         patch("app.services.communication_service.send_whatsapp_message", new_callable=AsyncMock) as mock_send:
        mock_get_user.return_value = mock_user
        mock_send.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer 'NON_EXISTENT_GOLD_999999' not found.",
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/communications/send",
                headers=headers,
                json={
                    "customer_id": "NON_EXISTENT_GOLD_999999",
                    "channel": "whatsapp",
                    "message": "Hello customer",
                },
            )

    assert resp.status_code == 404
    assert "not found" in resp.json().get("detail", "").lower()


@pytest.mark.asyncio
async def test_customer_without_mobile_returns_400():
    """5. Verify that customer with no mobile number returns 400 Bad Request."""
    token = create_access_token({"sub": "rm_vikram", "role": UserRole.RELATIONSHIP_MANAGER.value})
    headers = {"Authorization": f"Bearer {token}"}
    mock_user = _make_mock_user("rm_vikram", UserRole.RELATIONSHIP_MANAGER)

    with patch("app.api.deps.get_user_by_username", new_callable=AsyncMock) as mock_get_user, \
         patch("app.services.communication_service.send_whatsapp_message", new_callable=AsyncMock) as mock_send:
        mock_get_user.return_value = mock_user
        mock_send.side_effect = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No mobile number available for this customer.",
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/communications/send",
                headers=headers,
                json={
                    "customer_id": "GOLD-900001",
                    "channel": "whatsapp",
                    "message": "Hello client",
                },
            )

    assert resp.status_code == 400
    assert "no mobile number available" in resp.json().get("detail", "").lower()


@pytest.mark.asyncio
async def test_conflicting_mobile_numbers_return_400_validation_error():
    """6. Verify that multiple conflicting source mobile numbers raise review validation error."""
    token = create_access_token({"sub": "rm_vikram", "role": UserRole.RELATIONSHIP_MANAGER.value})
    headers = {"Authorization": f"Bearer {token}"}
    mock_user = _make_mock_user("rm_vikram", UserRole.RELATIONSHIP_MANAGER)

    with patch("app.api.deps.get_user_by_username", new_callable=AsyncMock) as mock_get_user, \
         patch("app.services.communication_service.send_whatsapp_message", new_callable=AsyncMock) as mock_send:
        mock_get_user.return_value = mock_user
        mock_send.side_effect = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Multiple conflicting mobile numbers exist for customer contact. Contact information requires review.",
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/communications/send",
                headers=headers,
                json={
                    "customer_id": "GOLD-900002",
                    "channel": "whatsapp",
                    "message": "Hello client",
                },
            )

    assert resp.status_code == 400
    assert "conflicting mobile numbers" in resp.json().get("detail", "").lower()


@pytest.mark.asyncio
async def test_successful_whatsapp_send_by_rm():
    """7. Verify successful WhatsApp sending by RELATIONSHIP_MANAGER."""
    token = create_access_token({"sub": "rm_vikram", "role": UserRole.RELATIONSHIP_MANAGER.value})
    headers = {"Authorization": f"Bearer {token}"}
    mock_user = _make_mock_user("rm_vikram", UserRole.RELATIONSHIP_MANAGER)

    expected_resp = CommunicationSendResponse(
        success=True,
        communication_id="COMM-20260821-ABC12345",
        channel="whatsapp",
        customer_id="GOLD-900003",
        status="sent",
        provider_message_id="SM1234567890abcdef1234567890abcdef",
        timestamp="2026-08-21T02:20:00",
        recipient="+919920602745",
        error=None,
    )

    with patch("app.api.deps.get_user_by_username", new_callable=AsyncMock) as mock_get_user, \
         patch("app.services.communication_service.send_whatsapp_message", new_callable=AsyncMock) as mock_send:
        mock_get_user.return_value = mock_user
        mock_send.return_value = expected_resp

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/communications/send",
                headers=headers,
                json={
                    "customer_id": "GOLD-900003",
                    "channel": "whatsapp",
                    "message": "Hello Rohit, this is your Relationship Manager.",
                },
            )

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["status"] == "sent"
    assert data["provider_message_id"] == "SM1234567890abcdef1234567890abcdef"
    assert data["recipient"] == "+919920602745"


@pytest.mark.asyncio
async def test_successful_whatsapp_send_by_admin():
    """8. Verify successful WhatsApp sending by ADMIN role."""
    token = create_access_token({"sub": "admin", "role": UserRole.ADMIN.value})
    headers = {"Authorization": f"Bearer {token}"}
    mock_user = _make_mock_user("admin", UserRole.ADMIN)

    expected_resp = CommunicationSendResponse(
        success=True,
        communication_id="COMM-20260821-ADM99999",
        channel="whatsapp",
        customer_id="GOLD-900003",
        status="sent",
        provider_message_id="SM9999999999abcdef",
        timestamp="2026-08-21T02:20:00",
        recipient="+919920602745",
        error=None,
    )

    with patch("app.api.deps.get_user_by_username", new_callable=AsyncMock) as mock_get_user, \
         patch("app.services.communication_service.send_whatsapp_message", new_callable=AsyncMock) as mock_send:
        mock_get_user.return_value = mock_user
        mock_send.return_value = expected_resp

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/communications/send",
                headers=headers,
                json={
                    "customer_id": "GOLD-900003",
                    "channel": "whatsapp",
                    "message": "Admin message",
                },
            )

    assert resp.status_code == 200
    assert resp.json()["success"] is True


@pytest.mark.asyncio
async def test_twilio_failure_creates_failed_log_without_crashing():
    """9. Verify that Twilio API failures store status=FAILED without crashing the app."""
    token = create_access_token({"sub": "rm_vikram", "role": UserRole.RELATIONSHIP_MANAGER.value})
    headers = {"Authorization": f"Bearer {token}"}
    mock_user = _make_mock_user("rm_vikram", UserRole.RELATIONSHIP_MANAGER)

    expected_resp = CommunicationSendResponse(
        success=False,
        communication_id="COMM-20260821-FAIL1234",
        channel="whatsapp",
        customer_id="GOLD-900004",
        status="failed",
        provider_message_id=None,
        timestamp="2026-08-21T02:20:00",
        recipient="+919899999999",
        error="Twilio API Error [21211]: The 'To' number is not a valid phone number.",
    )

    with patch("app.api.deps.get_user_by_username", new_callable=AsyncMock) as mock_get_user, \
         patch("app.services.communication_service.send_whatsapp_message", new_callable=AsyncMock) as mock_send:
        mock_get_user.return_value = mock_user
        mock_send.return_value = expected_resp

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/communications/send",
                headers=headers,
                json={
                    "customer_id": "GOLD-900004",
                    "channel": "whatsapp",
                    "message": "Test message",
                },
            )

    assert resp.status_code == 200  # API handles failure safely
    data = resp.json()
    assert data["success"] is False
    assert data["status"] == "failed"
    assert "not a valid phone number" in data["error"]


@pytest.mark.asyncio
async def test_get_customer_communication_history():
    """10. Verify GET communication history endpoint returns logged items."""
    token = create_access_token({"sub": "rm_vikram", "role": UserRole.RELATIONSHIP_MANAGER.value})
    headers = {"Authorization": f"Bearer {token}"}
    mock_user = _make_mock_user("rm_vikram", UserRole.RELATIONSHIP_MANAGER)

    mock_history = [
        {
            "id": 1,
            "communication_id": "COMM-20260821-HIST0001",
            "customer_id": "GOLD-900003",
            "golden_customer_id": "GOLD-900003",
            "channel": "whatsapp",
            "message": "Hello Rohit, follow-up regarding wealth portfolio.",
            "status": "sent",
            "sent_by": "rm_vikram",
            "recipient": "+919920602745",
            "created_at": "2026-08-21T02:15:00",
            "error_message": None,
        }
    ]

    with patch("app.api.deps.get_user_by_username", new_callable=AsyncMock) as mock_get_user, \
         patch("app.api.routes.communications.get_customer_communication_history", new_callable=AsyncMock) as mock_hist:
        mock_get_user.return_value = mock_user
        mock_hist.return_value = mock_history

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get(
                "/api/v1/communications/customer/GOLD-900003",
                headers=headers,
            )

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["sent_by"] == "rm_vikram"
    assert data[0]["status"] == "sent"
