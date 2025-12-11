# backend/tests/test_analyze.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_analyze_requires_consent():
    r = client.post("/analyze/", json={"raw_text":"please verify your password", "meta":{}})
    assert r.status_code == 403

def test_analyze_mock_or_gemini():
    payload = {
        "raw_text": "Your account is locked. Please verify your password immediately. Click here: http://192.0.2.1/login",
        "visible_links": [{"anchor_text":"Click here","uri":"http://192.0.2.1/login"}],
        "meta": {"source": "manual", "consent": True}
    }
    r = client.post("/analyze/", json=payload)
    assert r.status_code == 200
    j = r.json()
    assert "request_id" in j
    assert isinstance(j["score"], int)
    assert j["label"] in ("PHISHING", "SUSPICIOUS", "SAFE")
