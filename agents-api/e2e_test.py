"""Keyless local check of the actual private bridge, not Agent/model acceptance."""
from __future__ import annotations

import os

import httpx


def main() -> int:
    base = os.environ["E2E_BASE_URL"].rstrip("/")
    token = os.environ["E2E_MANAGED_TOKEN"]
    with httpx.Client(base_url=base, timeout=10, trust_env=False, follow_redirects=False) as client:
        response = client.get("/health")
        assert response.status_code == 200
        health = response.json()
        assert health["status"] == "ok"
        assert health["protocol"] == "agent-sandbox-managed-bridge/v1"
        assert health.get("epoch")
        assert client.get("/capabilities").status_code == 401
        assert client.get("/capabilities", headers={"Authorization": "Bearer invalid-test-token"}).status_code == 401
        client.headers["Authorization"] = "Bearer " + token
        response = client.get("/capabilities")
        assert response.status_code == 200
        assert response.json()["protocol"] == health["protocol"]
        assert response.json()["durable_receipts"] is True
        for path in ("/commands", "/v1/agents/sessions", "/shell", "/files"):
            assert client.get(path).status_code == 404
    print("PASS: actual managed bridge readiness, private authentication and closed route surface")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
