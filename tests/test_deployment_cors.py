"""Deployment-level CORS regression coverage for the public Vercel frontend."""
import importlib
import sys
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def test_known_vercel_origin_survives_stale_cors_environment(monkeypatch):
    """The deployed UI must work even if Render has an obsolete CORS_ORIGINS."""
    monkeypatch.setenv("CORS_ORIGINS", "https://obsolete.example")
    import app.main as main
    main = importlib.reload(main)
    client = TestClient(main.app)
    response = client.options(
        "/api/workspaces",
        headers={
            "Origin": "https://trustlens-alpha.vercel.app",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type,x-user-id",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://trustlens-alpha.vercel.app"


def test_unrelated_origin_is_not_allowed(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    import app.main as main
    main = importlib.reload(main)
    client = TestClient(main.app)
    response = client.options(
        "/api/workspaces",
        headers={
            "Origin": "https://unrelated.vercel.app",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 400
