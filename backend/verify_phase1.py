import os
import sys

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from sqlalchemy import text
from app.main import app
from app.db.session import SessionLocal
from app.db.models.source_record import SourceRecord
from app.db.models.audit import AuditLog

client = TestClient(app)

def verify_phase_1():
    print("--- Phase 1 Verification ---")
    
    # 1. Login to get token
    print("\n1. Getting Auth Token...")
    login_data = {"username": "admin@example.com", "password": "strongpassword"}
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == 200, "Failed to login"
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    print("[SUCCESS] Auth successful")
    
    # 2. Run seed once
    print("\n2. Running Seed Endpoint (1st time)...")
    response1 = client.post("/api/ingest/seed", headers=headers)
    assert response1.status_code == 200, "Seed failed"
    result1 = response1.json()
    print(f"[SUCCESS] Seed 1 result: {result1}")
    
    # 3. Run seed twice (Idempotency)
    print("\n3. Running Seed Endpoint (2nd time to test idempotency)...")
    response2 = client.post("/api/ingest/seed", headers=headers)
    assert response2.status_code == 200, "Seed 2 failed"
    result2 = response2.json()
    print(f"[SUCCESS] Seed 2 result: {result2}")
    
    # Verify duplicates skipped
    assert result2["duplicates_skipped"] > 0, "Expected duplicates to be skipped on second run"
    assert result2["customers_created"] == 0, "Expected 0 customers created on second run"
    print("[SUCCESS] Idempotency verified: Duplicates were successfully skipped.")
    
    # 4. Database checks
    print("\n4. Checking database tables and embeddings...")
    db = SessionLocal()
    try:
        # Check Source Records
        records_count = db.query(SourceRecord).count()
        print(f"Total SourceRecords in DB: {records_count}")
        assert records_count > 0, "No records found in database"
        
        # Check Embeddings exist
        # We'll fetch one record and check its vector
        record = db.query(SourceRecord).filter(SourceRecord.vector_embedding != None).first()
        assert record is not None, "No records with embeddings found"
        
        # Verify vector dimension
        vector_len = len(record.vector_embedding)
        print(f"Sample vector embedding dimension: {vector_len}")
        assert vector_len == 384, f"Expected vector dimension 384, got {vector_len}"
        print("[SUCCESS] Embeddings exist and are correctly sized (384)")
        
        # Check Audit Logs
        print("\n5. Checking Audit Logs...")
        audit_logs = db.query(AuditLog).filter(AuditLog.action_type == "DATA_INGESTION").all()
        print(f"Total DATA_INGESTION audit logs: {len(audit_logs)}")
        assert len(audit_logs) > 0, "No audit logs found for seeding"
        print(f"Sample Audit Log: {audit_logs[-1].description}")
        print("[SUCCESS] Audit logging verified.")
        
    finally:
        db.close()
        
    print("\n[SUCCESS] ALL PHASE 1 CHECKS PASSED!")

if __name__ == "__main__":
    verify_phase_1()
