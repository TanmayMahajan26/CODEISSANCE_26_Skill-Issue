from fastapi.testclient import TestClient
from app.main import app

def verify_ai_endpoint():
    print("--- Testing LangChain AI Endpoint ---")
    client = TestClient(app)
    
    print("\n1. Getting Admin Auth Token...")
    # Using the admin login from previous seed
    login_data = {
        "username": "admin@example.com",
        "password": "strongpassword"
    }
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == 200, "Failed to login as Admin"
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    print("[SUCCESS] Admin Auth successful")
    
    print("\n2. Pinging /api/ai/health...")
    ai_response = client.get("/api/ai/health", headers=headers)
    
    if ai_response.status_code == 200:
        result = ai_response.json()
        print(f"[SUCCESS] AI is connected! Groq responded with:\n>> '{result['response']}'")
    else:
        print(f"[ERROR] AI endpoint failed with status {ai_response.status_code}:")
        print(ai_response.json())
        assert False, "AI connection failed"

if __name__ == "__main__":
    verify_ai_endpoint()
