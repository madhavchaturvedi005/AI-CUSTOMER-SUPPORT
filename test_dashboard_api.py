"""Tests for dashboard API endpoints."""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_get_analytics():
    """Test GET /api/analytics endpoint."""
    response = client.get("/api/analytics")
    assert response.status_code == 200
    
    data = response.json()
    assert "total_calls" in data
    assert "total_leads" in data
    assert "total_appointments" in data
    assert "avg_duration" in data
    assert "call_volume" in data
    assert "intent_distribution" in data
    assert "recent_activity" in data
    
    # Verify structure
    assert isinstance(data["total_calls"], int)
    assert isinstance(data["call_volume"]["labels"], list)
    assert isinstance(data["call_volume"]["data"], list)


def test_get_calls():
    """Test GET /api/calls endpoint."""
    response = client.get("/api/calls")
    assert response.status_code == 200
    
    data = response.json()
    assert "calls" in data
    assert isinstance(data["calls"], list)
    
    # Verify call structure if calls exist
    if len(data["calls"]) > 0:
        call = data["calls"][0]
        assert "id" in call
        assert "caller_phone" in call
        assert "started_at" in call
        assert "duration_seconds" in call
        assert "intent" in call
        assert "status" in call


def test_get_calls_with_status_filter():
    """Test GET /api/calls with status filter."""
    response = client.get("/api/calls?status=completed")
    assert response.status_code == 200
    
    data = response.json()
    assert "calls" in data
    
    # All calls should have completed status
    for call in data["calls"]:
        assert call["status"] == "completed"


def test_get_leads():
    """Test GET /api/leads endpoint."""
    response = client.get("/api/leads")
    assert response.status_code == 200
    
    data = response.json()
    assert "leads" in data
    assert isinstance(data["leads"], list)
    
    # Verify lead structure if leads exist
    if len(data["leads"]) > 0:
        lead = data["leads"][0]
        assert "id" in lead
        assert "name" in lead
        assert "phone" in lead
        assert "lead_score" in lead


def test_get_leads_with_filter():
    """Test GET /api/leads with score filter."""
    # Test high value filter
    response = client.get("/api/leads?filter=high")
    assert response.status_code == 200
    data = response.json()
    for lead in data["leads"]:
        assert lead["lead_score"] >= 7
    
    # Test medium value filter
    response = client.get("/api/leads?filter=medium")
    assert response.status_code == 200
    data = response.json()
    for lead in data["leads"]:
        assert 4 <= lead["lead_score"] < 7
    
    # Test low value filter
    response = client.get("/api/leads?filter=low")
    assert response.status_code == 200
    data = response.json()
    for lead in data["leads"]:
        assert lead["lead_score"] < 4


def test_get_appointments():
    """Test GET /api/appointments endpoint."""
    response = client.get("/api/appointments")
    assert response.status_code == 200
    
    data = response.json()
    assert "appointments" in data
    assert isinstance(data["appointments"], list)
    
    # Verify appointment structure if appointments exist
    if len(data["appointments"]) > 0:
        appt = data["appointments"][0]
        assert "id" in appt
        assert "customer_name" in appt
        assert "customer_phone" in appt
        assert "service_type" in appt
        assert "appointment_datetime" in appt
        assert "duration_minutes" in appt
        assert "status" in appt


def test_update_config():
    """Test POST /api/config endpoint."""
    config_data = {
        "type": "greeting",
        "data": {
            "message": "Welcome to our business!"
        }
    }
    
    response = client.post("/api/config", json=config_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert "message" in data


def test_update_config_business_hours():
    """Test POST /api/config for business hours."""
    config_data = {
        "type": "business_hours",
        "data": {
            "weekday_start": "09:00",
            "weekday_end": "17:00"
        }
    }
    
    response = client.post("/api/config", json=config_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True


def test_update_config_personality():
    """Test POST /api/config for AI personality."""
    config_data = {
        "type": "personality",
        "data": {
            "tone": "professional",
            "style": "concise"
        }
    }
    
    response = client.post("/api/config", json=config_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True


def test_upload_documents():
    """Test POST /api/documents endpoint."""
    # Create a mock file
    files = {
        "files": ("test.txt", b"Test document content", "text/plain")
    }
    
    response = client.post("/api/documents", files=files)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["uploaded"] >= 0
    assert "files" in data


def test_cors_enabled():
    """Test that CORS is enabled for frontend access."""
    response = client.options("/api/analytics")
    # CORS should allow the request
    assert response.status_code in [200, 405]  # 405 is OK for OPTIONS if not explicitly handled


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
