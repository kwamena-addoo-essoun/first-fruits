from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.models.project import Project
from app.models.timelog import TimeLog
from app.models.user import User as UserModel
from app.services.invoice_service import TimeTrackingService


def register_and_login(client):
    suffix = uuid4().hex[:8]
    username = f"tester_{suffix}"
    email = f"{username}@example.com"
    password = "Pass1234!"

    register_response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "username": username,
            "password": password,
            "company_name": "Test Co",
            "hourly_rate": 80,
        },
    )
    assert register_response.status_code == 200

    login_response = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    assert login_response.status_code == 200

    token = login_response.json().get("access_token")
    assert token
    return {"Authorization": f"Bearer {token}"}


def test_register_and_login_returns_token(client):
    headers = register_and_login(client)
    assert headers["Authorization"].startswith("Bearer ")


def test_timelog_delete_removes_log_and_rolls_back_project_totals(client):
    headers = register_and_login(client)

    create_project_response = client.post(
        "/api/projects/",
        headers=headers,
        json={
            "name": "Project Alpha",
            "description": "Testing timelog delete flow",
            "hourly_rate": 100,
        },
    )
    assert create_project_response.status_code == 200
    project = create_project_response.json()

    start_time = datetime.now(UTC) - timedelta(hours=2)
    end_time = datetime.now(UTC)

    create_timelog_response = client.post(
        "/api/timelog/",
        headers=headers,
        json={
            "project_id": project["id"],
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "description": "Initial test log",
        },
    )
    assert create_timelog_response.status_code == 200
    timelog = create_timelog_response.json()

    projects_after_create = client.get("/api/projects/", headers=headers)
    assert projects_after_create.status_code == 200
    current_project = next(p for p in projects_after_create.json() if p["id"] == project["id"])
    assert current_project["total_hours"] > 0
    assert current_project["total_earned"] > 0

    delete_timelog_response = client.delete(f"/api/timelog/{timelog['id']}", headers=headers)
    assert delete_timelog_response.status_code == 200

    timelogs_after_delete = client.get("/api/timelog/", headers=headers)
    assert timelogs_after_delete.status_code == 200
    assert all(log["id"] != timelog["id"] for log in timelogs_after_delete.json())

    projects_after_delete = client.get("/api/projects/", headers=headers)
    assert projects_after_delete.status_code == 200
    updated_project = next(p for p in projects_after_delete.json() if p["id"] == project["id"])
    assert updated_project["total_hours"] == pytest.approx(0.0)
    assert updated_project["total_earned"] == pytest.approx(0.0)


def test_invoice_status_update_and_delete_flow(client):
    headers = register_and_login(client)

    due_date = (datetime.now(UTC) + timedelta(days=14)).isoformat()
    create_invoice_response = client.post(
        "/api/invoices/",
        headers=headers,
        json={"total_hours": 3.5, "hourly_rate": 120, "due_date": due_date},
    )
    assert create_invoice_response.status_code == 200
    invoice = create_invoice_response.json()

    update_status_response = client.put(
        f"/api/invoices/{invoice['id']}/status",
        headers=headers,
        params={"status": "paid"},
    )
    assert update_status_response.status_code == 200

    invoices_after_status = client.get("/api/invoices/", headers=headers)
    assert invoices_after_status.status_code == 200
    updated_invoice = next(inv for inv in invoices_after_status.json() if inv["id"] == invoice["id"])
    assert updated_invoice["status"] == "paid"
    assert updated_invoice["paid_date"] is not None

    delete_invoice_response = client.delete(f"/api/invoices/{invoice['id']}", headers=headers)
    assert delete_invoice_response.status_code == 200

    invoices_after_delete = client.get("/api/invoices/", headers=headers)
    assert invoices_after_delete.status_code == 200
    assert all(inv["id"] != invoice["id"] for inv in invoices_after_delete.json())


def test_get_current_user_profile(client):
    headers = register_and_login(client)

    response = client.get("/api/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "username" in data
    assert "email" in data
    # Password must never be exposed
    assert "password" not in data
    assert "hashed_password" not in data


def test_client_crud_flow(client):
    headers = register_and_login(client)

    # Create
    create_response = client.post(
        "/api/clients/",
        headers=headers,
        json={"name": "Acme Corp", "email": "acme@example.com", "rate": "95.00"},
    )
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["name"] == "Acme Corp"
    assert created["email"] == "acme@example.com"
    client_id = created["id"]

    # List
    list_response = client.get("/api/clients/", headers=headers)
    assert list_response.status_code == 200
    ids = [c["id"] for c in list_response.json()]
    assert client_id in ids

    # Delete
    delete_response = client.delete(f"/api/clients/{client_id}", headers=headers)
    assert delete_response.status_code == 200

    # Confirm removal
    list_after = client.get("/api/clients/", headers=headers)
    assert list_after.status_code == 200
    assert all(c["id"] != client_id for c in list_after.json())


def test_project_update_flow(client):
    headers = register_and_login(client)

    create_response = client.post(
        "/api/projects/",
        headers=headers,
        json={"name": "Old Name", "description": "Old description", "hourly_rate": 50},
    )
    assert create_response.status_code == 200
    project_id = create_response.json()["id"]

    update_response = client.put(
        f"/api/projects/{project_id}",
        headers=headers,
        json={"name": "New Name", "description": "New description", "hourly_rate": 150},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["name"] == "New Name"
    assert updated["description"] == "New description"
    assert updated["hourly_rate"] == 150


def test_earnings_summary_reflects_invoices(client):
    headers = register_and_login(client)

    due_date = (datetime.now(UTC) + timedelta(days=30)).isoformat()

    # Create two invoices: one paid, one draft
    inv1 = client.post(
        "/api/invoices/",
        headers=headers,
        json={"total_hours": 10, "hourly_rate": 100, "due_date": due_date},
    ).json()
    inv2 = client.post(
        "/api/invoices/",
        headers=headers,
        json={"total_hours": 5, "hourly_rate": 100, "due_date": due_date},
    ).json()

    # Mark inv1 as paid
    client.put(f"/api/invoices/{inv1['id']}/status", headers=headers, params={"status": "paid"})

    summary_response = client.get("/api/invoices/earnings/summary", headers=headers)
    assert summary_response.status_code == 200
    summary = summary_response.json()

    assert summary["total_invoiced"] == pytest.approx(1500.0)
    assert summary["paid"] == pytest.approx(1000.0)
    assert summary["pending"] == pytest.approx(500.0)


def test_timelog_project_filter(client):
    headers = register_and_login(client)

    proj_a = client.post(
        "/api/projects/",
        headers=headers,
        json={"name": "Project A", "description": "", "hourly_rate": 80},
    ).json()
    proj_b = client.post(
        "/api/projects/",
        headers=headers,
        json={"name": "Project B", "description": "", "hourly_rate": 80},
    ).json()

    now = datetime.now(UTC)

    # Log 1 hour to Project A and 2 hours to Project B
    client.post(
        "/api/timelog/",
        headers=headers,
        json={
            "project_id": proj_a["id"],
            "start_time": (now - timedelta(hours=1)).isoformat(),
            "end_time": now.isoformat(),
            "description": "Work on A",
        },
    )
    client.post(
        "/api/timelog/",
        headers=headers,
        json={
            "project_id": proj_b["id"],
            "start_time": (now - timedelta(hours=2)).isoformat(),
            "end_time": now.isoformat(),
            "description": "Work on B",
        },
    )

    logs_a = client.get(f"/api/timelog/project/{proj_a['id']}", headers=headers).json()
    logs_b = client.get(f"/api/timelog/project/{proj_b['id']}", headers=headers).json()

    assert len(logs_a) == 1
    assert logs_a[0]["project_id"] == proj_a["id"]
    assert len(logs_b) == 1
    assert logs_b[0]["project_id"] == proj_b["id"]


def test_invalid_invoice_status_rejected(client):
    headers = register_and_login(client)

    due_date = (datetime.now(UTC) + timedelta(days=7)).isoformat()
    invoice = client.post(
        "/api/invoices/",
        headers=headers,
        json={"total_hours": 1, "hourly_rate": 50, "due_date": due_date},
    ).json()

    bad_status_response = client.put(
        f"/api/invoices/{invoice['id']}/status",
        headers=headers,
        params={"status": "cancelled"},
    )
    assert bad_status_response.status_code == 400


def test_timelog_creation_rejected_for_unknown_project(client):
    headers = register_and_login(client)

    now = datetime.now(UTC)
    response = client.post(
        "/api/timelog/",
        headers=headers,
        json={
            "project_id": 999999,
            "start_time": (now - timedelta(hours=1)).isoformat(),
            "end_time": now.isoformat(),
            "description": "Should fail",
        },
    )
    assert response.status_code == 404

# ---------------------------------------------------------------------------
# Auth error paths  (auth.py lines 30, 49)
# ---------------------------------------------------------------------------

def test_duplicate_email_registration_rejected(client):
    headers = register_and_login(client)
    # Grab the email that was just registered
    me = client.get("/api/users/me", headers=headers).json()
    suffix = uuid4().hex[:8]
    response = client.post(
        "/api/auth/register",
        json={
            "email": me["email"],          # same email, different username
            "username": f"other_{suffix}",
            "password": "Pass1234!",
            "company_name": "Dupe Co",
            "hourly_rate": 50,
        },
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_invalid_login_rejected(client):
    headers = register_and_login(client)
    me = client.get("/api/users/me", headers=headers).json()

    response = client.post(
        "/api/auth/login",
        json={"username": me["username"], "password": "WrongPassword!"},
    )
    assert response.status_code == 401


def test_duplicate_username_returns_400(client):
    headers = register_and_login(client)
    me = client.get("/api/users/me", headers=headers).json()
    suffix = uuid4().hex[:8]
    response = client.post(
        "/api/auth/register",
        json={
            "username": me["username"],            # same username, different email
            "email": f"other_{suffix}@example.com",
            "password": "Pass1234!",
        },
    )
    assert response.status_code == 400
    assert "username" in response.json()["detail"].lower()


def test_weak_password_rejected(client):
    suffix = uuid4().hex[:8]
    response = client.post(
        "/api/auth/register",
        json={
            "username": f"weakuser_{suffix}",
            "email": f"weak_{suffix}@example.com",
            "password": "short",           # fewer than 8 chars
        },
    )
    assert response.status_code == 422


def test_update_password_too_short_returns_422(client):
    headers = register_and_login(client)
    response = client.put(
        "/api/users/me",
        headers=headers,
        json={"password": "abc"},          # fewer than 8 chars
    )
    assert response.status_code == 422


def test_token_refresh(client):
    headers = register_and_login(client)
    response = client.post("/api/auth/refresh", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    # New token must work for subsequent authenticated requests
    new_headers = {"Authorization": f"Bearer {data['access_token']}"}
    me_response = client.get("/api/users/me", headers=new_headers)
    assert me_response.status_code == 200


def test_refresh_with_invalid_token_returns_401(client):
    response = client.post(
        "/api/auth/refresh",
        headers={"Authorization": "Bearer not.a.real.token"},
    )
    assert response.status_code == 401


def test_refresh_with_no_token_returns_401(client):
    response = client.post("/api/auth/refresh")
    assert response.status_code == 401


def test_refresh_with_nonexistent_user_returns_401(client):
    from jose import jwt as jose_jwt
    from datetime import datetime, timedelta, UTC
    import os

    # Build a syntactically valid token for a user ID that does not exist in DB.
    # The app's load_dotenv() has already run, so SECRET_KEY is in the environment.
    secret = os.getenv("SECRET_KEY", "")
    token = jose_jwt.encode(
        {"sub": "999999", "exp": datetime.now(UTC) + timedelta(hours=1)},
        secret,
        algorithm="HS256",
    )
    response = client.post(
        "/api/auth/refresh",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "User not found"


# ---------------------------------------------------------------------------
# Password reset flow
# ---------------------------------------------------------------------------

def test_forgot_password_known_email_returns_200(client, db_session):
    headers = register_and_login(client)
    email = client.get("/api/users/me", headers=headers).json()["email"]

    response = client.post("/api/auth/forgot-password", json={"email": email})
    assert response.status_code == 200
    assert "reset link" in response.json()["message"].lower()

    # A reset token must have been created in the DB
    from app.models.password_reset import PasswordResetToken
    token_row = db_session.query(PasswordResetToken).filter(
        PasswordResetToken.used == False  # noqa: E712
    ).order_by(PasswordResetToken.id.desc()).first()
    assert token_row is not None


def test_forgot_password_unknown_email_still_returns_200(client):
    """Prevent user-enumeration: unknown email must return the same 200."""
    response = client.post(
        "/api/auth/forgot-password",
        json={"email": "nobody_exists@example.com"},
    )
    assert response.status_code == 200


def test_reset_password_success(client, db_session):
    headers = register_and_login(client)
    me = client.get("/api/users/me", headers=headers).json()

    client.post("/api/auth/forgot-password", json={"email": me["email"]})

    from app.models.password_reset import PasswordResetToken
    token_row = db_session.query(PasswordResetToken).filter(
        PasswordResetToken.used == False  # noqa: E712
    ).order_by(PasswordResetToken.id.desc()).first()

    response = client.post(
        "/api/auth/reset-password",
        json={"token": token_row.token, "password": "BrandNew99!"},
    )
    assert response.status_code == 200
    assert "successful" in response.json()["message"].lower()

    # Token is now marked used
    db_session.refresh(token_row)
    assert token_row.used is True

    # Can log in with the new password
    login = client.post(
        "/api/auth/login",
        json={"username": me["username"], "password": "BrandNew99!"},
    )
    assert login.status_code == 200


def test_reset_password_invalid_token(client):
    response = client.post(
        "/api/auth/reset-password",
        json={"token": "completely-fake-token", "password": "NewPass99!"},
    )
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


def test_reset_password_used_token_rejected(client, db_session):
    headers = register_and_login(client)
    me = client.get("/api/users/me", headers=headers).json()

    client.post("/api/auth/forgot-password", json={"email": me["email"]})

    from app.models.password_reset import PasswordResetToken
    token_row = db_session.query(PasswordResetToken).filter(
        PasswordResetToken.used == False  # noqa: E712
    ).order_by(PasswordResetToken.id.desc()).first()
    raw_token = token_row.token

    # First use — succeeds
    client.post(
        "/api/auth/reset-password",
        json={"token": raw_token, "password": "FirstReset1!"},
    )

    # Second use — must be rejected
    response = client.post(
        "/api/auth/reset-password",
        json={"token": raw_token, "password": "SecondReset1!"},
    )
    assert response.status_code == 400


def test_reset_password_expired_token_rejected(client, db_session):
    headers = register_and_login(client)
    me = client.get("/api/users/me", headers=headers).json()

    client.post("/api/auth/forgot-password", json={"email": me["email"]})

    from app.models.password_reset import PasswordResetToken
    from datetime import datetime, timedelta, UTC
    token_row = db_session.query(PasswordResetToken).filter(
        PasswordResetToken.used == False  # noqa: E712
    ).order_by(PasswordResetToken.id.desc()).first()

    # Back-date the expiry so the token is already expired
    token_row.expires_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=2)
    db_session.commit()

    response = client.post(
        "/api/auth/reset-password",
        json={"token": token_row.token, "password": "ExpiredPass1!"},
    )
    assert response.status_code == 400


def test_reset_password_too_short_returns_422(client, db_session):
    headers = register_and_login(client)
    me = client.get("/api/users/me", headers=headers).json()

    client.post("/api/auth/forgot-password", json={"email": me["email"]})

    from app.models.password_reset import PasswordResetToken
    token_row = db_session.query(PasswordResetToken).filter(
        PasswordResetToken.used == False  # noqa: E712
    ).order_by(PasswordResetToken.id.desc()).first()

    response = client.post(
        "/api/auth/reset-password",
        json={"token": token_row.token, "password": "short"},  # < 8 chars
    )
    assert response.status_code == 422


def test_forgot_password_email_failure_still_returns_200(client, db_session):
    """If email sending raises, the endpoint must silently swallow it and return 200."""
    from unittest.mock import patch

    headers = register_and_login(client)
    email = client.get("/api/users/me", headers=headers).json()["email"]

    with patch(
        "app.routes.auth.send_password_reset_email",
        side_effect=Exception("SMTP down"),
    ):
        response = client.post("/api/auth/forgot-password", json={"email": email})

    assert response.status_code == 200


def test_email_service_smtp_path(monkeypatch):
    """Exercise the SMTP send code path in email_service.py via a mock server."""
    from unittest.mock import patch, MagicMock
    import app.services.email_service as svc

    monkeypatch.setattr(svc, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(svc, "SMTP_PORT", 587)
    monkeypatch.setattr(svc, "SMTP_USERNAME", "user@example.com")
    monkeypatch.setattr(svc, "SMTP_PASSWORD", "secret")
    monkeypatch.setattr(svc, "SMTP_FROM", "user@example.com")

    mock_server = MagicMock()
    mock_smtp_cls = MagicMock()
    mock_smtp_cls.return_value.__enter__ = lambda s: mock_server
    mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

    with patch("smtplib.SMTP", mock_smtp_cls):
        svc.send_password_reset_email("recipient@example.com", "tok123")

    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("user@example.com", "secret")
    mock_server.sendmail.assert_called_once()


def test_email_service_logs_url_when_unconfigured(monkeypatch, caplog):
    """When SMTP_HOST is empty, the reset URL is logged instead of sent."""
    import logging
    import app.services.email_service as svc

    monkeypatch.setattr(svc, "SMTP_HOST", "")  # forces _smtp_configured() → False
    with caplog.at_level(logging.WARNING, logger="app.services.email_service"):
        svc.send_password_reset_email("user@example.com", "tok_uncfg")

    assert "tok_uncfg" in caplog.text


# ---------------------------------------------------------------------------
# Admin panel
# ---------------------------------------------------------------------------

def _make_admin_headers(client, db_session):
    """Register a user, promote them to admin in the DB, return (headers, user_id)."""
    from app.models.user import User

    headers = register_and_login(client)
    me = client.get("/api/users/me", headers=headers).json()
    user = db_session.query(User).filter(User.id == me["id"]).first()
    user.is_admin = True
    db_session.commit()
    return headers, me["id"]


def test_admin_list_requires_admin(client):
    headers = register_and_login(client)
    response = client.get("/api/admin/users", headers=headers)
    assert response.status_code == 403


def test_admin_list_users(client, db_session):
    admin_headers, _ = _make_admin_headers(client, db_session)
    register_and_login(client)  # second user

    response = client.get("/api/admin/users", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert all("username" in u and "email" in u and "is_admin" in u for u in data)


def test_admin_delete_user(client, db_session):
    admin_headers, _ = _make_admin_headers(client, db_session)
    other_headers = register_and_login(client)
    other_id = client.get("/api/users/me", headers=other_headers).json()["id"]

    response = client.delete(f"/api/admin/users/{other_id}", headers=admin_headers)
    assert response.status_code == 200

    # The deleted user's data is now gone
    assert client.get("/api/users/me", headers=other_headers).status_code == 401


def test_admin_cannot_delete_self(client, db_session):
    admin_headers, admin_id = _make_admin_headers(client, db_session)
    response = client.delete(f"/api/admin/users/{admin_id}", headers=admin_headers)
    assert response.status_code == 400


def test_admin_delete_nonexistent_user(client, db_session):
    admin_headers, _ = _make_admin_headers(client, db_session)
    response = client.delete("/api/admin/users/999999", headers=admin_headers)
    assert response.status_code == 404


def test_admin_toggle_admin(client, db_session):
    admin_headers, _ = _make_admin_headers(client, db_session)
    other_headers = register_and_login(client)
    other_id = client.get("/api/users/me", headers=other_headers).json()["id"]

    response = client.post(f"/api/admin/users/{other_id}/toggle-admin", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["is_admin"] is True

    response2 = client.post(f"/api/admin/users/{other_id}/toggle-admin", headers=admin_headers)
    assert response2.status_code == 200
    assert response2.json()["is_admin"] is False


def test_admin_cannot_toggle_own_admin(client, db_session):
    admin_headers, admin_id = _make_admin_headers(client, db_session)
    response = client.post(f"/api/admin/users/{admin_id}/toggle-admin", headers=admin_headers)
    assert response.status_code == 400


def test_admin_toggle_nonexistent_user(client, db_session):
    admin_headers, _ = _make_admin_headers(client, db_session)
    response = client.post("/api/admin/users/999999/toggle-admin", headers=admin_headers)
    assert response.status_code == 404


def test_admin_force_reset_password(client, db_session):
    from unittest.mock import patch

    admin_headers, _ = _make_admin_headers(client, db_session)
    other_headers = register_and_login(client)
    other_id = client.get("/api/users/me", headers=other_headers).json()["id"]

    with patch("app.routes.admin.send_password_reset_email"):
        response = client.post(f"/api/admin/users/{other_id}/reset-password", headers=admin_headers)

    assert response.status_code == 200
    data = response.json()
    assert "/reset-password?token=" in data["reset_url"]
    assert data["email_sent"] is True


def test_admin_force_reset_email_fails_silently(client, db_session):
    from unittest.mock import patch

    admin_headers, _ = _make_admin_headers(client, db_session)
    other_headers = register_and_login(client)
    other_id = client.get("/api/users/me", headers=other_headers).json()["id"]

    with patch("app.routes.admin.send_password_reset_email", side_effect=Exception("SMTP down")):
        response = client.post(f"/api/admin/users/{other_id}/reset-password", headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["email_sent"] is False


def test_admin_force_reset_nonexistent_user(client, db_session):
    admin_headers, _ = _make_admin_headers(client, db_session)
    response = client.post("/api/admin/users/999999/reset-password", headers=admin_headers)
    assert response.status_code == 404


def test_is_admin_claim_in_refreshed_token(client, db_session):
    """After promotion, a refreshed token carries is_admin=True."""
    import base64
    import json

    admin_headers, _ = _make_admin_headers(client, db_session)
    response = client.post("/api/auth/refresh", headers=admin_headers)
    assert response.status_code == 200

    token = response.json()["access_token"]
    padded = token.split(".")[1] + "=="
    payload = json.loads(base64.b64decode(padded))
    assert payload.get("is_admin") is True


# ---------------------------------------------------------------------------
# Auth header error paths  (users.py lines 19, 23, 32-33)
# ---------------------------------------------------------------------------

def test_missing_auth_header_returns_401(client):
    response = client.get("/api/users/me")   # no Authorization header
    assert response.status_code == 401


def test_malformed_auth_header_returns_401(client):
    response = client.get("/api/users/me", headers={"Authorization": "Token abc123"})
    assert response.status_code == 401


def test_invalid_jwt_token_returns_401(client):
    response = client.get("/api/users/me", headers={"Authorization": "Bearer not.a.valid.token"})
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Client 404 path  (clients.py line 38)
# ---------------------------------------------------------------------------

def test_delete_nonexistent_client_returns_404(client):
    headers = register_and_login(client)
    response = client.delete("/api/clients/999999", headers=headers)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Invoice 404 paths  (invoices.py lines 50, 66)
# ---------------------------------------------------------------------------

def test_update_status_on_nonexistent_invoice_returns_404(client):
    headers = register_and_login(client)
    response = client.put(
        "/api/invoices/999999/status",
        headers=headers,
        params={"status": "paid"},
    )
    assert response.status_code == 404


def test_delete_nonexistent_invoice_returns_404(client):
    headers = register_and_login(client)
    response = client.delete("/api/invoices/999999", headers=headers)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Project error paths  (projects.py lines 17-19, 45, 48-50)
# ---------------------------------------------------------------------------

def test_create_project_with_invalid_client_id_returns_400(client):
    headers = register_and_login(client)
    response = client.post(
        "/api/projects/",
        headers=headers,
        json={"name": "Bad Project", "description": "", "hourly_rate": 80, "client_id": 999999},
    )
    assert response.status_code == 400


def test_update_nonexistent_project_returns_404(client):
    headers = register_and_login(client)
    response = client.put(
        "/api/projects/999999",
        headers=headers,
        json={"name": "Ghost", "description": "", "hourly_rate": 80},
    )
    assert response.status_code == 404


def test_update_project_with_invalid_client_id_returns_400(client):
    headers = register_and_login(client)
    project = client.post(
        "/api/projects/",
        headers=headers,
        json={"name": "Real Project", "description": "", "hourly_rate": 80},
    ).json()

    response = client.put(
        f"/api/projects/{project['id']}",
        headers=headers,
        json={"name": "Real Project", "description": "", "hourly_rate": 80, "client_id": 999999},
    )
    assert response.status_code == 400


def test_project_delete_flow(client):
    headers = register_and_login(client)

    project = client.post(
        "/api/projects/",
        headers=headers,
        json={"name": "Temporary Project", "description": "", "hourly_rate": 75},
    ).json()
    project_id = project["id"]

    delete_response = client.delete(f"/api/projects/{project_id}", headers=headers)
    assert delete_response.status_code == 200

    projects_after = client.get("/api/projects/", headers=headers).json()
    assert all(p["id"] != project_id for p in projects_after)


def test_delete_nonexistent_project_returns_404(client):
    headers = register_and_login(client)
    response = client.delete("/api/projects/999999", headers=headers)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Timelog error paths  (timelog.py lines 19, 65)
# ---------------------------------------------------------------------------

def test_timelog_end_before_start_returns_400(client):
    headers = register_and_login(client)
    project = client.post(
        "/api/projects/",
        headers=headers,
        json={"name": "Time Test", "description": "", "hourly_rate": 50},
    ).json()

    now = datetime.now(UTC)
    response = client.post(
        "/api/timelog/",
        headers=headers,
        json={
            "project_id": project["id"],
            "start_time": now.isoformat(),
            "end_time": (now - timedelta(hours=1)).isoformat(),  # end BEFORE start
            "description": "Invalid",
        },
    )
    assert response.status_code == 400


def test_delete_nonexistent_timelog_returns_404(client):
    headers = register_and_login(client)
    response = client.delete("/api/timelog/999999", headers=headers)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# InvoiceService.get_project_stats unit test  (invoice_service.py lines 16-22)
# ---------------------------------------------------------------------------

def test_get_project_stats_returns_correct_totals(client, db_session):
    # Build minimal ORM objects directly to test the service in isolation
    from app.models.user import User as UserModel

    user = UserModel(
        email=f"stats_{uuid4().hex[:6]}@example.com",
        username=f"stats_{uuid4().hex[:6]}",
        hashed_password="x",
        hourly_rate=100,
    )
    db_session.add(user)
    db_session.flush()

    project = Project(user_id=user.id, name="Stats Project", hourly_rate=100)
    db_session.add(project)
    db_session.flush()

    now = datetime.now(UTC)
    log = TimeLog(
        user_id=user.id,
        project_id=project.id,
        start_time=now - timedelta(hours=3),
        end_time=now,
        hours=3.0,
        description="test",
    )
    db_session.add(log)
    db_session.flush()

    stats = TimeTrackingService.get_project_stats(db_session, project.id)
    assert stats["total_hours"] == pytest.approx(3.0)
    assert stats["total_earned"] == pytest.approx(300.0)


# ---------------------------------------------------------------------------
# users.py line 37 — valid JWT but user has since been deleted
# ---------------------------------------------------------------------------

def test_orphaned_jwt_returns_401(client, db_session):
    """A valid token for a user who was subsequently deleted must be rejected."""
    headers = register_and_login(client)

    # Resolve which user this token belongs to
    me = client.get("/api/users/me", headers=headers).json()

    # Delete directly in the shared session so the request handler sees the change
    user = db_session.query(UserModel).filter(UserModel.id == me["id"]).first()
    db_session.delete(user)
    db_session.flush()

    # Token is still structurally valid but the user no longer exists
    response = client.get("/api/users/me", headers=headers)
    assert response.status_code == 401
    assert "not found" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# PUT /api/users/me  (users.py update_me)
# ---------------------------------------------------------------------------

def test_update_user_profile(client):
    headers = register_and_login(client)
    response = client.put(
        "/api/users/me",
        headers=headers,
        json={"company_name": "Updated Co", "hourly_rate": 150.0},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == "Updated Co"
    assert data["hourly_rate"] == 150.0


def test_update_user_password_allows_new_login(client):
    headers = register_and_login(client)
    me = client.get("/api/users/me", headers=headers).json()

    update_response = client.put(
        "/api/users/me",
        headers=headers,
        json={"password": "NewPass5678!"},
    )
    assert update_response.status_code == 200

    login_response = client.post(
        "/api/auth/login",
        json={"username": me["username"], "password": "NewPass5678!"},
    )
    assert login_response.status_code == 200
    assert login_response.json().get("access_token")


# ---------------------------------------------------------------------------
# PUT /api/clients/{id}  (clients.py update_client)
# ---------------------------------------------------------------------------

def test_update_client(client):
    headers = register_and_login(client)
    created = client.post(
        "/api/clients/",
        headers=headers,
        json={"name": "Old Name", "email": "old@example.com", "rate": "50"},
    ).json()

    response = client.put(
        f"/api/clients/{created['id']}",
        headers=headers,
        json={"name": "New Name", "email": "new@example.com", "rate": "99"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["email"] == "new@example.com"
    assert data["rate"] == "99"


def test_update_nonexistent_client_returns_404(client):
    headers = register_and_login(client)
    response = client.put(
        "/api/clients/999999",
        headers=headers,
        json={"name": "Ghost"},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Invoice: project-linked creation + PDF
# ---------------------------------------------------------------------------

def _create_project_with_log(client, headers):
    """Helper: create a project, log 2 hours to it, return (project, timelog)."""
    project = client.post(
        "/api/projects/",
        headers=headers,
        json={"name": "Invoice Test Project", "hourly_rate": 80.0},
    ).json()
    start = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
    end = datetime.now(UTC).isoformat()
    log = client.post(
        "/api/timelog/",
        headers=headers,
        json={"project_id": project["id"], "start_time": start, "end_time": end},
    ).json()
    return project, log


def test_invoice_from_project_auto_computes_hours(client):
    headers = register_and_login(client)
    project, _ = _create_project_with_log(client, headers)

    due = (datetime.now(UTC) + timedelta(days=14)).isoformat()
    response = client.post(
        "/api/invoices/",
        headers=headers,
        json={"project_id": project["id"], "due_date": due},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["project_name"] == "Invoice Test Project"
    assert data["total_hours"] == pytest.approx(2.0, abs=0.01)
    assert data["hourly_rate"] == pytest.approx(80.0)
    assert data["total_amount"] == pytest.approx(160.0, abs=0.1)


def test_invoice_from_project_marks_logs_invoiced(client, db_session):
    headers = register_and_login(client)
    project, log = _create_project_with_log(client, headers)

    due = (datetime.now(UTC) + timedelta(days=14)).isoformat()
    client.post(
        "/api/invoices/",
        headers=headers,
        json={"project_id": project["id"], "due_date": due},
    )

    tl = db_session.query(TimeLog).filter(TimeLog.id == log["id"]).first()
    assert tl.is_invoiced == 1


def test_invoice_from_project_no_uninvoiced_logs_returns_400(client):
    headers = register_and_login(client)
    project, _ = _create_project_with_log(client, headers)
    due = (datetime.now(UTC) + timedelta(days=14)).isoformat()

    # First invoice consumes all logs
    client.post("/api/invoices/", headers=headers,
                json={"project_id": project["id"], "due_date": due})

    # Second attempt — no uninvoiced logs remain
    response = client.post("/api/invoices/", headers=headers,
                           json={"project_id": project["id"], "due_date": due})
    assert response.status_code == 400
    assert "uninvoiced" in response.json()["detail"].lower()


def test_invoice_manual_missing_hours_returns_422(client):
    headers = register_and_login(client)
    due = (datetime.now(UTC) + timedelta(days=14)).isoformat()
    # No project_id and missing total_hours — validator should reject
    response = client.post(
        "/api/invoices/",
        headers=headers,
        json={"hourly_rate": 100.0, "due_date": due},
    )
    assert response.status_code == 422


def test_download_invoice_pdf(client):
    headers = register_and_login(client)
    due = (datetime.now(UTC) + timedelta(days=14)).isoformat()
    invoice = client.post(
        "/api/invoices/",
        headers=headers,
        json={"total_hours": 5.0, "hourly_rate": 100.0, "due_date": due},
    ).json()

    pdf_response = client.get(f"/api/invoices/{invoice['id']}/pdf", headers=headers)
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    # PDF magic bytes: %PDF
    assert pdf_response.content[:4] == b"%PDF"


def test_download_pdf_nonexistent_invoice_returns_404(client):
    headers = register_and_login(client)
    response = client.get("/api/invoices/999999/pdf", headers=headers)
    assert response.status_code == 404


def test_invoice_with_explicit_client_id_snapshots_name(client):
    headers = register_and_login(client)
    c = client.post(
        "/api/clients/", headers=headers,
        json={"name": "Snapshot Client", "email": "snap@example.com"},
    ).json()
    due = (datetime.now(UTC) + timedelta(days=14)).isoformat()
    invoice = client.post(
        "/api/invoices/", headers=headers,
        json={"client_id": c["id"], "total_hours": 2.0, "hourly_rate": 50.0, "due_date": due},
    ).json()
    assert invoice["client_name"] == "Snapshot Client"
    assert invoice["client_id"] == c["id"]


def test_invoice_invalid_client_id_returns_404(client):
    headers = register_and_login(client)
    due = (datetime.now(UTC) + timedelta(days=14)).isoformat()
    response = client.post(
        "/api/invoices/", headers=headers,
        json={"client_id": 999999, "total_hours": 1.0, "hourly_rate": 50.0, "due_date": due},
    )
    assert response.status_code == 404


def test_invoice_project_with_linked_client_snapshots_names(client):
    headers = register_and_login(client)
    c = client.post(
        "/api/clients/", headers=headers,
        json={"name": "Linked Client", "email": "linked@example.com"},
    ).json()
    project = client.post(
        "/api/projects/", headers=headers,
        json={"name": "Linked Project", "hourly_rate": 90.0, "client_id": c["id"]},
    ).json()
    start = (datetime.now(UTC) - timedelta(hours=3)).isoformat()
    end = datetime.now(UTC).isoformat()
    client.post("/api/timelog/", headers=headers,
                json={"project_id": project["id"], "start_time": start, "end_time": end})

    due = (datetime.now(UTC) + timedelta(days=14)).isoformat()
    invoice = client.post(
        "/api/invoices/", headers=headers,
        json={"project_id": project["id"], "due_date": due},
    ).json()
    assert invoice["client_name"] == "Linked Client"
    assert invoice["project_name"] == "Linked Project"


def test_download_paid_invoice_pdf_includes_paid_date(client):
    """Exercises the paid_date branch in the PDF generator."""
    headers = register_and_login(client)
    due = (datetime.now(UTC) + timedelta(days=7)).isoformat()
    invoice = client.post(
        "/api/invoices/", headers=headers,
        json={"total_hours": 1.0, "hourly_rate": 100.0, "due_date": due},
    ).json()
    client.put(f"/api/invoices/{invoice['id']}/status", headers=headers, params={"status": "paid"})

    pdf_response = client.get(f"/api/invoices/{invoice['id']}/pdf", headers=headers)
    assert pdf_response.status_code == 200
    assert pdf_response.content[:4] == b"%PDF"


def test_download_pdf_with_notes(client):
    """Exercises the notes branch in the PDF generator."""
    headers = register_and_login(client)
    due = (datetime.now(UTC) + timedelta(days=7)).isoformat()
    invoice = client.post(
        "/api/invoices/", headers=headers,
        json={"total_hours": 2.0, "hourly_rate": 75.0, "due_date": due,
              "notes": "Net 30 payment terms"},
    ).json()

    pdf_response = client.get(f"/api/invoices/{invoice['id']}/pdf", headers=headers)
    assert pdf_response.status_code == 200
    assert pdf_response.content[:4] == b"%PDF"


def test_invoice_nonexistent_project_returns_404(client):
    headers = register_and_login(client)
    due = (datetime.now(UTC) + timedelta(days=14)).isoformat()
    response = client.post(
        "/api/invoices/", headers=headers,
        json={"project_id": 999999, "due_date": due},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Live timer: start / active / stop
# ---------------------------------------------------------------------------

def _make_project(client, headers, name="Timer Project", rate=75.0):
    return client.post("/api/projects/", headers=headers,
                       json={"name": name, "hourly_rate": rate}).json()


def test_start_timer_creates_log_without_end_time(client):
    headers = register_and_login(client)
    project = _make_project(client, headers)

    response = client.post("/api/timelog/", headers=headers,
                           json={"project_id": project["id"],
                                 "description": "Live work"})
    assert response.status_code == 200
    data = response.json()
    assert data["end_time"] is None
    assert data["hours"] is None
    assert data["description"] == "Live work"


def test_get_active_timer_returns_running_log(client):
    headers = register_and_login(client)
    project = _make_project(client, headers)
    created = client.post("/api/timelog/", headers=headers,
                          json={"project_id": project["id"]}).json()

    active = client.get("/api/timelog/active", headers=headers).json()
    assert active["id"] == created["id"]
    assert active["end_time"] is None


def test_get_active_timer_404_when_none_running(client):
    headers = register_and_login(client)
    response = client.get("/api/timelog/active", headers=headers)
    assert response.status_code == 404


def test_stop_timer_sets_end_time_and_hours(client):
    headers = register_and_login(client)
    project = _make_project(client, headers)
    log = client.post("/api/timelog/", headers=headers,
                      json={"project_id": project["id"]}).json()

    stopped = client.patch(f"/api/timelog/{log['id']}/stop", headers=headers).json()
    assert stopped["end_time"] is not None
    assert stopped["hours"] is not None
    assert stopped["hours"] > 0

    # Project totals should be updated
    p = client.get("/api/projects/", headers=headers).json()
    proj = next(x for x in p if x["id"] == project["id"])
    assert proj["total_hours"] == pytest.approx(stopped["hours"], abs=0.01)


def test_start_second_timer_while_one_running_returns_400(client):
    headers = register_and_login(client)
    project = _make_project(client, headers)
    client.post("/api/timelog/", headers=headers, json={"project_id": project["id"]})

    response = client.post("/api/timelog/", headers=headers,
                           json={"project_id": project["id"]})
    assert response.status_code == 400
    assert "already running" in response.json()["detail"].lower()


def test_stop_already_stopped_timer_returns_400(client):
    headers = register_and_login(client)
    project = _make_project(client, headers)
    now = datetime.now(UTC)
    log = client.post("/api/timelog/", headers=headers, json={
        "project_id": project["id"],
        "start_time": (now - timedelta(hours=1)).isoformat(),
        "end_time": now.isoformat(),
    }).json()

    response = client.patch(f"/api/timelog/{log['id']}/stop", headers=headers)
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Time log editing (PUT /api/timelog/{id})
# ---------------------------------------------------------------------------

def test_update_timelog_description(client):
    headers = register_and_login(client)
    project = _make_project(client, headers)
    now = datetime.now(UTC)
    log = client.post("/api/timelog/", headers=headers, json={
        "project_id": project["id"],
        "start_time": (now - timedelta(hours=2)).isoformat(),
        "end_time": now.isoformat(),
        "description": "Old description",
    }).json()

    response = client.put(f"/api/timelog/{log['id']}", headers=headers,
                          json={"description": "Updated description"})
    assert response.status_code == 200
    assert response.json()["description"] == "Updated description"


def test_update_timelog_times_recomputes_hours(client):
    headers = register_and_login(client)
    project = _make_project(client, headers, rate=100.0)
    now = datetime.now(UTC)
    log = client.post("/api/timelog/", headers=headers, json={
        "project_id": project["id"],
        "start_time": (now - timedelta(hours=1)).isoformat(),
        "end_time": now.isoformat(),
    }).json()
    assert log["hours"] == pytest.approx(1.0, abs=0.05)

    new_start = (now - timedelta(hours=3)).isoformat()
    response = client.put(f"/api/timelog/{log['id']}", headers=headers,
                          json={"start_time": new_start})
    assert response.status_code == 200
    assert response.json()["hours"] == pytest.approx(3.0, abs=0.05)


def test_update_running_timer_returns_400(client):
    headers = register_and_login(client)
    project = _make_project(client, headers)
    log = client.post("/api/timelog/", headers=headers,
                      json={"project_id": project["id"]}).json()

    response = client.put(f"/api/timelog/{log['id']}", headers=headers,
                          json={"description": "Should fail"})
    assert response.status_code == 400
    # Stop the timer to clean up active state
    client.patch(f"/api/timelog/{log['id']}/stop", headers=headers)


def test_update_nonexistent_timelog_returns_404(client):
    headers = register_and_login(client)
    response = client.put("/api/timelog/999999", headers=headers,
                          json={"description": "Ghost"})
    assert response.status_code == 404


def test_update_timelog_to_invalid_project_returns_404(client):
    headers = register_and_login(client)
    project = _make_project(client, headers)
    now = datetime.now(UTC)
    log = client.post("/api/timelog/", headers=headers, json={
        "project_id": project["id"],
        "start_time": (now - timedelta(hours=1)).isoformat(),
        "end_time": now.isoformat(),
    }).json()

    response = client.put(f"/api/timelog/{log['id']}", headers=headers,
                          json={"project_id": 999999})
    assert response.status_code == 404


def test_stop_nonexistent_timer_returns_404(client):
    headers = register_and_login(client)
    response = client.patch("/api/timelog/999999/stop", headers=headers)
    assert response.status_code == 404


def test_update_timelog_end_before_start_returns_400(client):
    headers = register_and_login(client)
    project = _make_project(client, headers)
    now = datetime.now(UTC)
    log = client.post("/api/timelog/", headers=headers, json={
        "project_id": project["id"],
        "start_time": (now - timedelta(hours=1)).isoformat(),
        "end_time": now.isoformat(),
    }).json()

    # Set end_time to before the existing start_time
    response = client.put(f"/api/timelog/{log['id']}", headers=headers,
                          json={"end_time": (now - timedelta(hours=2)).isoformat()})
    assert response.status_code == 400
    assert "end_time must be after" in response.json()["detail"].lower()


def test_update_timelog_reassigns_project_updates_totals(client):
    """Moving a timelog to a different project adjusts both projects' hour totals."""
    headers = register_and_login(client)
    proj1 = _make_project(client, headers, rate=50.0)
    proj2 = _make_project(client, headers, rate=100.0)
    now = datetime.now(UTC)
    log = client.post("/api/timelog/", headers=headers, json={
        "project_id": proj1["id"],
        "start_time": (now - timedelta(hours=2)).isoformat(),
        "end_time": now.isoformat(),
    }).json()

    # Reassign the log to proj2
    response = client.put(f"/api/timelog/{log['id']}", headers=headers,
                          json={"project_id": proj2["id"]})
    assert response.status_code == 200
    assert response.json()["project_id"] == proj2["id"]

    projects = {p["id"]: p for p in client.get("/api/projects/", headers=headers).json()}
    # proj1 should have 0 hours, proj2 should have ~2 hours
    assert projects[proj1["id"]]["total_hours"] == pytest.approx(0.0, abs=0.05)
    assert projects[proj2["id"]]["total_hours"] == pytest.approx(2.0, abs=0.05)


# ---------------------------------------------------------------------------
# Email verification
# ---------------------------------------------------------------------------

def _register_unverified(client):
    """Register a user suppressing the auto-verify side-effect."""
    import unittest.mock
    suffix = uuid4().hex[:8]
    username = f"unv_{suffix}"
    email = f"{username}@example.com"
    password = "Pass1234!"
    with unittest.mock.patch("app.routes.auth.send_verification_email"):
        resp = client.post("/api/auth/register", json={
            "email": email, "username": username,
            "password": password, "hourly_rate": 50,
        })
        assert resp.status_code == 200
    return username, email, password


def test_register_returns_user_object(client):
    suffix = uuid4().hex[:8]
    resp = client.post("/api/auth/register", json={
        "email": f"{suffix}@example.com",
        "username": f"reg_{suffix}",
        "password": "Pass1234!",
        "hourly_rate": 50,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "username" in data
    assert "access_token" not in data


def test_unverified_user_cannot_login(client):
    username, _, password = _register_unverified(client)
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 403
    assert resp.json()["detail"] == "EMAIL_NOT_VERIFIED"


def test_verify_email_success(client, db_session):
    import secrets as _secrets
    from datetime import UTC, datetime, timedelta
    from app.models.email_verification import EmailVerificationToken
    from app.models.user import User

    username, _, password = _register_unverified(client)

    user = db_session.query(User).filter(User.username == username).first()
    token = _secrets.token_urlsafe(16)
    expires = datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=24)
    db_session.add(EmailVerificationToken(user_id=user.id, token=token, expires_at=expires))
    db_session.flush()

    resp = client.get(f"/api/auth/verify-email?token={token}")
    assert resp.status_code == 200
    assert "verified" in resp.json()["message"].lower()

    db_session.refresh(user)
    assert user.is_verified is True

    login_resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()


def test_verify_email_invalid_token(client):
    resp = client.get("/api/auth/verify-email?token=definitelynotavalidtoken")
    assert resp.status_code == 400


def test_verify_email_expired_token(client, db_session):
    import secrets as _secrets
    from datetime import UTC, datetime, timedelta
    from app.models.email_verification import EmailVerificationToken
    from app.models.user import User

    username, _, _ = _register_unverified(client)
    user = db_session.query(User).filter(User.username == username).first()
    token = _secrets.token_urlsafe(16)
    expires = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1)  # already expired
    db_session.add(EmailVerificationToken(user_id=user.id, token=token, expires_at=expires))
    db_session.flush()

    resp = client.get(f"/api/auth/verify-email?token={token}")
    assert resp.status_code == 400


def test_verify_email_already_used_token(client, db_session):
    import secrets as _secrets
    from datetime import UTC, datetime, timedelta
    from app.models.email_verification import EmailVerificationToken
    from app.models.user import User

    username, _, _ = _register_unverified(client)
    user = db_session.query(User).filter(User.username == username).first()
    token = _secrets.token_urlsafe(16)
    expires = datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=24)
    db_session.add(EmailVerificationToken(user_id=user.id, token=token, expires_at=expires, used=True))
    db_session.flush()

    resp = client.get(f"/api/auth/verify-email?token={token}")
    assert resp.status_code == 400


def test_resend_verification_returns_200_always(client):
    resp = client.post("/api/auth/resend-verification", json={"email": "nonexistent@example.com"})
    assert resp.status_code == 200


def test_resend_verification_sends_new_token(client, db_session):
    import unittest.mock
    from app.models.user import User

    username, email, password = _register_unverified(client)

    with unittest.mock.patch("app.routes.auth.send_verification_email") as mock_send:
        resp = client.post("/api/auth/resend-verification", json={"email": email})
        assert resp.status_code == 200
        mock_send.assert_called_once()

    user = db_session.query(User).filter(User.username == username).first()
    assert user.is_verified is False  # still unverified until they click the link


def test_email_verification_service_smtp_path(monkeypatch):
    """Exercise the SMTP path for send_verification_email."""
    from unittest.mock import patch, MagicMock
    import app.services.email_service as svc

    monkeypatch.setattr(svc, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(svc, "SMTP_PORT", 587)
    monkeypatch.setattr(svc, "SMTP_USERNAME", "user@example.com")
    monkeypatch.setattr(svc, "SMTP_PASSWORD", "secret")
    monkeypatch.setattr(svc, "SMTP_FROM", "user@example.com")

    mock_server = MagicMock()
    mock_smtp_cls = MagicMock()
    mock_smtp_cls.return_value.__enter__ = lambda s: mock_server
    mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

    with patch("smtplib.SMTP", mock_smtp_cls):
        svc.send_verification_email("recipient@example.com", "vtok123")

    mock_server.starttls.assert_called_once()
    mock_server.sendmail.assert_called_once()


def test_email_verification_service_logs_url_when_unconfigured(monkeypatch, caplog):
    import logging
    import app.services.email_service as svc

    monkeypatch.setattr(svc, "SMTP_HOST", "")
    with caplog.at_level(logging.WARNING, logger="app.services.email_service"):
        svc.send_verification_email("user@example.com", "vtok_uncfg")

    assert "vtok_uncfg" in caplog.text


def test_register_silently_continues_when_smtp_raises(client, db_session):
    """If send_verification_email raises, register still returns 200."""
    import unittest.mock
    from uuid import uuid4
    suffix = uuid4().hex[:8]
    with unittest.mock.patch(
        "app.routes.auth.send_verification_email",
        side_effect=Exception("SMTP down"),
    ):
        resp = client.post("/api/auth/register", json={
            "email": f"err_{suffix}@example.com",
            "username": f"err_{suffix}",
            "password": "Pass1234!",
            "hourly_rate": 50,
        })
    assert resp.status_code == 200


def test_resend_silently_continues_when_smtp_raises(client, db_session):
    """If send_verification_email raises on resend, endpoint still returns 200."""
    import unittest.mock
    username, email, _ = _register_unverified(client)
    with unittest.mock.patch(
        "app.routes.auth.send_verification_email",
        side_effect=Exception("SMTP down"),
    ):
        resp = client.post("/api/auth/resend-verification", json={"email": email})
    assert resp.status_code == 200

