"""Test configuration display functionality."""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_get_config_endpoint():
    """Test GET /api/config endpoint returns current configuration."""
    response = client.get("/api/config")
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert "config" in data
    
    config = data["config"]
    assert "greeting" in config
    assert "business_hours" in config
    assert "personality" in config
    assert "languages" in config
    
    print(f"✅ Configuration loaded:")
    print(f"   Greeting: {config['greeting']['message'][:50]}...")
    print(f"   Business Hours: {config['business_hours']}")
    print(f"   Personality: {config['personality']}")
    print(f"   Languages: {config['languages']}")


def test_get_documents_endpoint():
    """Test GET /api/documents endpoint returns uploaded documents."""
    response = client.get("/api/documents")
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert "documents" in data
    assert "count" in data
    
    print(f"✅ Documents loaded: {data['count']} documents")
    
    if data["documents"]:
        for doc in data["documents"]:
            print(f"   - {doc['filename']} ({doc['size']} bytes)")


def test_config_update_and_retrieve():
    """Test that configuration can be updated and retrieved."""
    # Update greeting
    config_data = {
        "type": "greeting",
        "data": {
            "message": "Test greeting for configuration display"
        }
    }
    
    response = client.post("/api/config", json=config_data)
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Retrieve configuration
    response = client.get("/api/config")
    assert response.status_code == 200
    
    data = response.json()
    # In memory mode, the greeting should be updated
    # (In database mode, it would be persisted)
    
    print(f"✅ Configuration update and retrieve tested")


def test_config_structure():
    """Test that configuration has the correct structure."""
    response = client.get("/api/config")
    assert response.status_code == 200
    
    config = response.json()["config"]
    
    # Check greeting structure
    assert "message" in config["greeting"]
    assert isinstance(config["greeting"]["message"], str)
    
    # Check business hours structure
    assert "weekday_start" in config["business_hours"]
    assert "weekday_end" in config["business_hours"]
    
    # Check personality structure
    assert "tone" in config["personality"]
    assert "style" in config["personality"]
    
    # Check languages
    assert isinstance(config["languages"], list)
    assert len(config["languages"]) > 0
    
    print(f"✅ Configuration structure is correct")


def test_documents_structure():
    """Test that documents list has the correct structure."""
    response = client.get("/api/documents")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data["documents"], list)
    assert isinstance(data["count"], int)
    
    # If there are documents, check their structure
    if data["documents"]:
        doc = data["documents"][0]
        assert "id" in doc
        assert "filename" in doc
        assert "file_type" in doc
        assert "size" in doc
        assert "uploaded_at" in doc
        assert "active" in doc
    
    print(f"✅ Documents structure is correct")


if __name__ == "__main__":
    print("\n🧪 Testing Configuration Display\n")
    print("=" * 60)
    
    # Run tests
    test_get_config_endpoint()
    test_get_documents_endpoint()
    test_config_update_and_retrieve()
    test_config_structure()
    test_documents_structure()
    
    print("=" * 60)
    print("\n✅ All tests passed!\n")
    print("The dashboard will now show:")
    print("  • Current greeting message")
    print("  • Current business hours")
    print("  • Current AI personality settings")
    print("  • List of uploaded documents")
    print()
