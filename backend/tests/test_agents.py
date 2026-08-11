import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import Base, Brand, Product, ConsumerFeedback, Decision
from agents.orchestrator import agent_orchestrator

from database.db import Brand, Product, ConsumerFeedback, Decision
from agents.orchestrator import agent_orchestrator

@pytest.fixture
def setup_db(db_session):
    # Create Brand AURA
    brand = Brand(name="AURA", description="Clean Beauty")
    db_session.add(brand)
    db_session.commit()
    db_session.refresh(brand)
    
    # Create Product
    product = Product(brand_id=brand.id, name="Hydrating Face Wash", sku="AURA-FW-HYD-01", description="Face wash")
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    # Feedbacks
    import datetime
    now = datetime.datetime.utcnow()
    fb1 = ConsumerFeedback(
        brand_id=brand.id,
        product_id=product.id,
        source="review",
        rating=1,
        content="Leaking packaging",
        date=now
    )
    db_session.add(fb1)
    
    # Historic Decision
    viva = Brand(name="VIVA", description="Wellness")
    db_session.add(viva)
    db_session.commit()
    db_session.refresh(viva)
    
    historic_dec = Decision(
        brand_id=viva.id,
        product_id=None,
        problem="packaging leakage shaker bottle",
        evidence="{}",
        analysis="cap cracking",
        recommendation="change supplier to Apex Caps",
        human_decision="APPROVED",
        owner="QA team",
        status="RESOLVED",
        outcome="Solved leakage"
    )
    db_session.add(historic_dec)
    db_session.commit()
    
    yield db_session

def test_investigation_orchestration_generic(setup_db):
    result = agent_orchestrator.run_investigation(
        db=setup_db,
        query="Why has customer satisfaction declined for AURA Face Wash over the last 30 days and what should we do?"
    )
    
    assert result["status"] == "success"
    assert "logs" in result
    assert len(result["logs"]) > 0
    # Check that logs trace all agent runs
    agent_names = [log["agent"] for log in result["logs"]]
    assert "Router Agent" in agent_names
    assert "Research Agent" in agent_names
    assert "Analysis Agent" in agent_names
    assert "Memory Agent" in agent_names
    assert "Recommendation Agent" in agent_names

    # Check output components
    assert "score" in result["confidence"]
    assert result["confidence"]["score"] >= 0
    assert result["confidence"]["level"] in ["HIGH", "MEDIUM", "LOW"]
    assert result["findings"]
    assert result["trend_data"]["trend"] in ["INCREASING", "DECREASING", "STABLE", "INSUFFICIENT_DATA"]

def test_investigation_orchestration_aura(setup_db):
    result = agent_orchestrator.run_investigation(
        db=setup_db,
        query="Why has customer satisfaction declined for AURA Face Wash over the last 30 days and what should we do?"
    )
    assert result["status"] == "success"
    assert "packaging leakage" in result["findings"].lower()
    assert len(result["historical_memory"]) > 0
