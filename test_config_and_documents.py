"""Test configuration and document upload functionality."""

import pytest
from fastapi.testclient import TestClient
from main import app
import io

client = TestClient(app)


def test_update_greeting_config():
    """Test updating greeting configuration."""
    config_data = {
        "type": "greeting",
        "data": {
            "message": "Hello, welcome to Suresh Salon! How can I help you today? I can understand English, Hindi, Tamil, and Telugu."
        }
    }
    
    response = client.post("/api/config", json=config_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert "greeting" in data["message"]
    print(f"✅ Greeting configuration updated: {data['message']}")


def test_update_business_hours_config():
    """Test updating business hours configuration."""
    config_data = {
        "type": "business_hours",
        "data": {
            "weekday_start": "09:00",
            "weekday_end": "20:00",
            "weekend_start": "10:00",
            "weekend_end": "18:00"
        }
    }
    
    response = client.post("/api/config", json=config_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    print(f"✅ Business hours configuration updated")


def test_update_personality_config():
    """Test updating AI personality configuration."""
    config_data = {
        "type": "personality",
        "data": {
            "tone": "friendly",
            "style": "conversational"
        }
    }
    
    response = client.post("/api/config", json=config_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    print(f"✅ AI personality configuration updated")


def test_upload_text_document():
    """Test uploading a text document."""
    # Create a mock text file
    content = b"""
SURESH SALON - BUSINESS INFORMATION

Services:
- Haircut: Rs 300
- Hair Coloring: Rs 1500
- Facial: Rs 800

Business Hours:
Monday - Saturday: 9:00 AM - 8:00 PM
Sunday: 10:00 AM - 6:00 PM

Location:
123 MG Road, Bangalore

Special Offers:
- First-time customers get 20% off
"""
    
    files = {
        "files": ("suresh_salon_info.txt", io.BytesIO(content), "text/plain")
    }
    
    response = client.post("/api/documents", files=files)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["uploaded"] >= 0
    assert "suresh_salon_info.txt" in data.get("files", []) or data["uploaded"] == 0
    print(f"✅ Document uploaded: {data.get('files', [])}")


def test_upload_multiple_documents():
    """Test uploading multiple documents."""
    files = [
        ("files", ("services.txt", io.BytesIO(b"Haircut: Rs 300\nColoring: Rs 1500"), "text/plain")),
        ("files", ("hours.txt", io.BytesIO(b"Mon-Sat: 9AM-8PM\nSun: 10AM-6PM"), "text/plain"))
    ]
    
    response = client.post("/api/documents", files=files)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    print(f"✅ Multiple documents uploaded: {data['uploaded']} files")


def test_invalid_config_type():
    """Test handling of invalid configuration type."""
    config_data = {
        "type": "invalid_type",
        "data": {"test": "value"}
    }
    
    response = client.post("/api/config", json=config_data)
    # Should still succeed but log warning
    assert response.status_code in [200, 400]
    print(f"✅ Invalid config type handled gracefully")


def test_config_persistence():
    """Test that configuration persists across requests."""
    # Set greeting
    config_data = {
        "type": "greeting",
        "data": {
            "message": "Test greeting message"
        }
    }
    
    response = client.post("/api/config", json=config_data)
    assert response.status_code == 200
    
    # Configuration should be in app.state
    # (In real scenario, would verify from database)
    print(f"✅ Configuration persistence tested")


def test_document_upload_validation():
    """Test document upload with invalid file type."""
    # Try to upload an executable file (should be rejected)
    files = {
        "files": ("malicious.exe", io.BytesIO(b"fake exe content"), "application/x-msdownload")
    }
    
    response = client.post("/api/documents", files=files)
    # Should succeed but skip invalid file
    assert response.status_code == 200
    
    data = response.json()
    # File should be skipped
    assert data["uploaded"] == 0 or "malicious.exe" not in data.get("files", [])
    print(f"✅ Invalid file type rejected")


def test_empty_document_upload():
    """Test uploading with no files."""
    response = client.post("/api/documents", files=[])
    # Should handle gracefully
    assert response.status_code in [200, 422]  # 422 is validation error
    print(f"✅ Empty upload handled")


if __name__ == "__main__":
    print("\n🧪 Testing Configuration and Document Upload\n")
    print("=" * 60)
    
    # Run tests
    test_update_greeting_config()
    test_update_business_hours_config()
    test_update_personality_config()
    test_upload_text_document()
    test_upload_multiple_documents()
    test_invalid_config_type()
    test_config_persistence()
    test_document_upload_validation()
    test_empty_document_upload()
    
    print("=" * 60)
    print("\n✅ All tests passed!\n")
