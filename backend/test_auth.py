import os
import sys

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.db.models.user import User, UserRole
from app.api.deps import RoleChecker, get_current_active_user
from fastapi import Depends

# Dummy protected endpoint for testing RBAC
@app.get("/api/admin-only")
def admin_only_route(current_user: User = Depends(RoleChecker([UserRole.ADMIN]))):
    return {"message": "Welcome Admin"}

client = TestClient(app)

def test_auth_flow():
    # 1. Create a user (Admin)
    print("Creating admin user...")
    setup_data = {
        "email": "admin@example.com",
        "password": "strongpassword",
        "full_name": "Admin User",
        "role": "ADMIN",
        "team_id": "HQ"
    }
    response = client.post("/api/auth/setup", json=setup_data)
    if response.status_code == 400 and "already exists" in response.text:
        print("Admin user already exists. Proceeding...")
    else:
        assert response.status_code == 200, f"Failed to create user: {response.text}"
        print("Admin user created successfully.")

    # 2. Login with incorrect password
    print("Testing login with incorrect password...")
    login_data_bad = {
        "username": "admin@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/api/auth/login", data=login_data_bad)
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    print("Incorrect password login failed as expected.")

    # 3. Login with correct password
    print("Testing login with correct password...")
    login_data = {
        "username": "admin@example.com",
        "password": "strongpassword"
    }
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == 200, f"Login failed: {response.text}"
    tokens = response.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    print("Login successful. Access and refresh tokens acquired.")

    # 4. Access /me endpoint
    print("Testing /me endpoint...")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200, f"Failed to access /me: {response.text}"
    user_data = response.json()
    assert user_data["email"] == "admin@example.com"
    print("/me accessed successfully.")

    # 5. Refresh Token
    print("Testing token refresh...")
    refresh_data = {"refresh_token": refresh_token}
    response = client.post("/api/auth/refresh", json=refresh_data)
    assert response.status_code == 200, f"Failed to refresh token: {response.text}"
    print("Token refreshed successfully.")
    
    # 6. Test RBAC (Role-Based Access Control)
    print("Testing RBAC...")
    # Create an RM user
    rm_setup_data = {
        "email": "rm@example.com",
        "password": "rmpassword",
        "full_name": "RM User",
        "role": "RM",
        "team_id": "HQ"
    }
    response = client.post("/api/auth/setup", json=rm_setup_data)
    if response.status_code != 400:
        assert response.status_code == 200, "Failed to create RM user"
    
    # Login as RM
    rm_login_data = {"username": "rm@example.com", "password": "rmpassword"}
    response = client.post("/api/auth/login", data=rm_login_data)
    rm_access_token = response.json()["access_token"]
    
    # Try to access Admin-only route as RM
    rm_headers = {"Authorization": f"Bearer {rm_access_token}"}
    response = client.get("/api/admin-only", headers=rm_headers)
    assert response.status_code == 403, f"Expected 403 Forbidden for RM accessing Admin route, got {response.status_code}"
    
    # Try to access Admin-only route as Admin
    response = client.get("/api/admin-only", headers=headers)
    assert response.status_code == 200, f"Expected 200 OK for Admin accessing Admin route, got {response.status_code}"
    
    print("RBAC tested successfully.")

if __name__ == "__main__":
    try:
        test_auth_flow()
        print("All authentication tests passed successfully!")
    except AssertionError as e:
        print(f"Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
