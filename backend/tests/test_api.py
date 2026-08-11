import os
import sys
import pytest
import json
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database.db import Brand, Product

client = TestClient(app)

@pytest.fixture
def setup_db(db_session):
    # Seed brand & product
    b = Brand(name="AURA", description="Aura Brand")
    db_session.add(b)
    db_session.commit()
    db_session.refresh(b)
    
    p = Product(brand_id=b.id, name="Hydrating Face Wash", sku="AURA-FW-HYD-01", description="Face Wash")
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    
    # Feedbacks
    import datetime
    now = datetime.datetime.utcnow()
    from database.db import ConsumerFeedback, Document, Decision
    fb = ConsumerFeedback(brand_id=b.id, product_id=p.id, source="review", rating=1, content="Packaging leakage cap is cracked.", date=now)
    db_session.add(fb)
    
    # Document
    doc = Document(brand_id=b.id, product_id=p.id, filename="aura_spec.txt", content="Capping limits are PP hinge flip-top caps.", metadata_json="{}")
    db_session.add(doc)
    
    # Decision
    v = Brand(name="VIVA", description="Viva brand")
    db_session.add(v)
    db_session.commit()
    db_session.refresh(v)
    dec = Decision(brand_id=v.id, product_id=None, problem="leakage in shaker cap", analysis="broken cap hinge", recommendation="Apex Caps Ltd", human_decision="APPROVED", owner="Sarah Jenkins", status="RESOLVED", outcome="Complaint rate dropped")
    db_session.add(dec)
    db_session.commit()
    
    yield db_session

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_get_brands(setup_db):
    response = client.get("/api/brands")
    assert response.status_code == 200
    brands = response.json()
    assert len(brands) > 0
    assert brands[0]["name"] == "AURA"

def test_investigate_endpoint(setup_db):
    response = client.post(
        "/api/investigate",
        json={"query": "Why is customer satisfaction declining for AURA Face Wash?", "brand_name": "AURA"}
    )
    assert response.status_code == 200
    res_data = response.json()
    assert "logs" in res_data
    assert "findings" in res_data
    assert "recommendation" in res_data

def test_create_and_search_decision(setup_db):
    db = setup_db
    brand = db.query(Brand).first()
    
    # Save a decision
    decision_payload = {
        "brand_id": brand.id,
        "product_id": None,
        "problem": "Packaging caps leaking during transit tests.",
        "evidence": json.dumps({"defect_count": 5}),
        "analysis": "Torque level lower than specification SOP-QA.",
        "recommendation": "Perform calibration of capping equipment on Line 3.",
        "human_decision": "APPROVED",
        "owner": "Sarah Jenkins",
        "status": "RESOLVED",
        "outcome": "Leakage stopped"
    }
    
    response = client.post("/api/decisions", json=decision_payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Query decisions with search filter
    search_response = client.get("/api/decisions?query=calibration")
    assert search_response.status_code == 200
    decisions = search_response.json()
    assert len(decisions) == 1
    assert decisions[0]["owner"] == "Sarah Jenkins"
    assert decisions[0]["problem"] == "Packaging caps leaking during transit tests."
