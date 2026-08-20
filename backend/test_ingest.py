import os
import sys

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal

client = TestClient(app)

def test_ingestion_flow():
    # 1. Login to get a token
    print("Logging in to get access token...")
    login_data = {
        "username": "admin@example.com",
        "password": "strongpassword"
    }
    response = client.post("/api/auth/login", data=login_data)
    if response.status_code != 200:
        # If admin doesn't exist, create it
        setup_data = {
            "email": "admin@example.com",
            "password": "strongpassword",
            "full_name": "Admin User",
            "role": "ADMIN",
            "team_id": "HQ"
        }
        client.post("/api/auth/setup", json=setup_data)
        response = client.post("/api/auth/login", data=login_data)
        
    assert response.status_code == 200, f"Login failed: {response.text}"
    access_token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 2. Test the seed endpoint
    print("Testing /api/ingest/seed endpoint...")
    response = client.post("/api/ingest/seed", headers=headers)
    assert response.status_code == 200, f"Failed to seed data: {response.text}"
    
    result = response.json()
    print(f"Seed successful. Result: {result}")
    
    assert "customers_created" in result
    assert "accounts_created" in result
    assert "embeddings_generated" in result
    assert "duplicates_skipped" in result
    assert result["customers_created"] > 0
    
    print("Ingestion pipeline seeded and verified successfully!")

if __name__ == "__main__":
    test_ingestion_flow()
