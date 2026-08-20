import os
import sys

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.db.models.source_record import SourceRecord
from app.db.models.golden_record import GoldenRecord
from app.db.models.identity_edge import IdentityEdge

client = TestClient(app)

def verify_phase_2():
    print("--- Phase 2 Verification ---")
    
    # 1. Login to get token
    print("\n1. Getting Auth Token...")
    login_data = {"username": "admin@example.com", "password": "strongpassword"}
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == 200, "Failed to login"
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    print("[SUCCESS] Auth successful")
    
    # 2. Ensure data is seeded
    print("\n2. Seeding Data (Idempotent)...")
    client.post("/api/ingest/seed", headers=headers)
    
    # 3. Trigger Resolution Pipeline
    print("\n3. Running Entity Resolution Pipeline...")
    res = client.post("/api/resolution/run", headers=headers)
    assert res.status_code == 200, f"Resolution failed: {res.text}"
    metrics = res.json()["metrics"]
    print(f"[SUCCESS] Resolution completed.")
    print(f"Metrics: {metrics}")
    
    # 4. Database verification
    print("\n4. Verifying Graph Clusters & Golden Records in Database...")
    db = SessionLocal()
    try:
        total_edges = db.query(IdentityEdge).count()
        total_golden = db.query(GoldenRecord).count()
        
        print(f"Total Identity Edges: {total_edges}")
        print(f"Total Golden Records: {total_golden}")
        
        assert total_golden > 0, "No Golden Records created!"
        
        # Verify a golden record's math
        golden = db.query(GoldenRecord).first()
        sources = db.query(SourceRecord).filter(SourceRecord.golden_record_id == golden.id).all()
        
        print(f"\nChecking Golden Record {golden.id}")
        print(f"Contains {len(sources)} source records")
        
        calc_trv = sum((s.account_value or 0.0) for s in sources)
        assert abs(calc_trv - golden.total_relationship_value) < 0.1, f"TRV mismatch! Calc: {calc_trv}, Golden: {golden.total_relationship_value}"
        print(f"[SUCCESS] TRV Calculation matches source components (${calc_trv})")
        
        print(f"Provenance tracked for {len(golden.provenance.keys()) if golden.provenance else 0} attributes.")
        assert golden.provenance and len(golden.provenance.keys()) > 0, "Provenance not tracked!"
        print("[SUCCESS] Attribute-level provenance verified.")
        
    finally:
        db.close()
        
    print("\n[SUCCESS] ALL PHASE 2 CHECKS PASSED!")

if __name__ == "__main__":
    verify_phase_2()
