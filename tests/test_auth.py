"""Sprint 3 QA: OAuth / Chainlit auth configuration (mocked, no live providers)."""

from __future__ import annotations

import pytest


def _import_auth():
    try:
        import auth  # type: ignore[import-not-found]
    except ImportError:
        pytest.skip("auth module not implemented (Sprint 3)")
    return auth


class TestAuthSettings:
    def test_auth_disabled_by_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        auth = _import_auth()
        monkeypatch.delenv("CHAINLIT_AUTH_SECRET", raising=False)
        monkeypatch.delenv("OAUTH_GOOGLE_CLIENT_ID", raising=False)
        monkeypatch.delenv("OAUTH_GITHUB_CLIENT_ID", raising=False)

        settings = auth.load_auth_settings()

        assert settings.enabled is False
        assert settings.providers == []

    def test_auth_enabled_when_secret_and_provider_configured(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        auth = _import_auth()
        monkeypatch.setenv("CHAINLIT_AUTH_SECRET", "test-secret-for-qa-only")
        monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_ID", "google-client-id")
        monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_SECRET", "google-client-secret")

        settings = auth.load_auth_settings()

        assert settings.enabled is True
        assert "google" in settings.providers

    def test_user_session_key_from_oauth_user(self) -> None:
        auth = _import_auth()
        user = {"identifier": "user-123", "metadata": {"role": "student"}}

        session_key = auth.session_thread_prefix(user)

        assert session_key == "user-123"
        assert "user-123" in auth.checkpoint_thread_id(user, session_id="sess-abc")

    def test_default_role_is_student(self) -> None:
        auth = _import_auth()
        user = {"identifier": "user-456", "metadata": {}}

        assert auth.resolve_user_role(user) == "student"
