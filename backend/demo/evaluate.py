import sys
import os
import time
import datetime
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import Base, Brand, Product, ConsumerFeedback, Document, Decision
from agents.orchestrator import agent_orchestrator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

def run_comprehensive_evaluation():
    print("==================================================")
    print("      THINK9 INTELLIGENCE HUB EVALUATION          ")
    print("==================================================")
    
    # Isolated SQLite database in memory
    eval_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    EvalSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=eval_engine)
    
    # Create tables
    Base.metadata.create_all(bind=eval_engine)
    db = EvalSessionLocal()
    
    # Seed data
    # Brands
    aura = Brand(name="AURA", description="Aura Brand")
    nexa = Brand(name="NEXA", description="Nexa Brand")
    viva = Brand(name="VIVA", description="Viva Brand")
    db.add_all([aura, nexa, viva])
    db.commit()
    db.refresh(aura)
    db.refresh(nexa)
    db.refresh(viva)
    
    # Products
    p_aura = Product(brand_id=aura.id, name="Hydrating Face Wash", sku="AURA-FW-01")
    p_nexa = Product(brand_id=nexa.id, name="Smart Blender", sku="NEXA-BL-05")
    p_viva = Product(brand_id=viva.id, name="Organic Protein Powder", sku="VIVA-PR-10")
    db.add_all([p_aura, p_nexa, p_viva])
    db.commit()
    db.refresh(p_aura)
    db.refresh(p_nexa)
    db.refresh(p_viva)
    
    # Feedbacks
    now = datetime.datetime.utcnow()
    # 28 complaints for AURA Face Wash (leakage) in the last 30 days
    feedbacks = []
    for i in range(28):
        feedbacks.append(ConsumerFeedback(brand_id=aura.id, product_id=p_aura.id, source="review", rating=1, content="Product was leaking during shipping transit.", date=now - datetime.timedelta(days=i%15)))
    # blender overheating for NEXA
    for i in range(5):
        feedbacks.append(ConsumerFeedback(brand_id=nexa.id, product_id=p_nexa.id, source="review", rating=2, content="Blender motor gets extremely hot.", date=now - datetime.timedelta(days=i)))
    db.add_all(feedbacks)
    
    # Documents
    doc_aura = Document(brand_id=aura.id, product_id=p_aura.id, filename="aura_spec.txt", content="Capping limits flip-top cap torque is 12-18 inch-pounds.", metadata_json="{}")
    db.add_all([doc_aura])
    
    # Decision
    historic_dec = Decision(
        brand_id=viva.id,
        product_id=p_viva.id,
        problem="container closure failure during transit shaker bottle",
        evidence="{}",
        analysis="cap hinge cracking",
        recommendation="Apex Caps Ltd torque range specifications check",
        human_decision="APPROVED",
        owner="VP Ops",
        status="RESOLVED",
        outcome="Resolved shaker cup leak"
    )
    db.add(historic_dec)
    db.commit()

    passed_tests = 0
    total_tests = 10
    execution_times = []

    # 1. AURA routing
    print("Test 1: AURA brand routing...")
    t0 = time.time()
    res = agent_orchestrator.run_investigation(db, "Why has satisfaction declined for AURA Face Wash?")
    execution_times.append(time.time() - t0)
    if res.get("status") == "success" and res.get("brand_id") == aura.id and res.get("product_id") == p_aura.id:
        print("  [PASSED]")
        passed_tests += 1
    else:
        print("  [FAILED]", res)

    # 2. NEXA routing
    print("Test 2: NEXA brand routing...")
    t0 = time.time()
    res = agent_orchestrator.run_investigation(db, "Why is my NEXA Smart Blender motor overheating?")
    execution_times.append(time.time() - t0)
    if res.get("status") == "success" and res.get("brand_id") == nexa.id and res.get("product_id") == p_nexa.id:
        print("  [PASSED]")
        passed_tests += 1
    else:
        print("  [FAILED]", res)

    # 3. VIVA routing
    print("Test 3: VIVA brand routing...")
    res = agent_orchestrator.run_investigation(db, "Why is VIVA Organic Protein Powder container closure failing in transit?")
    if res.get("brand_id") == viva.id and res.get("product_id") == p_viva.id and res.get("status") == "success":
        print("  [PASSED]")
        passed_tests += 1
    else:
        print("  [FAILED]", res)

    # 4. Unknown brand handling
    print("Test 4: Unknown brand handling...")
    t0 = time.time()
    res = agent_orchestrator.run_investigation(db, "Why is my product defective?")
    execution_times.append(time.time() - t0)
    if res.get("status") == "needs_context":
        print("  [PASSED]")
        passed_tests += 1
    else:
        print("  [FAILED]", res)

    # 5. RAG evidence retrieval
    print("Test 5: RAG evidence retrieval...")
    res = agent_orchestrator.run_investigation(db, "AURA Face Wash capping limits and spec sheets?")
    if len(res.get("evidence", {}).get("supporting_documents", [])) > 0:
        print("  [PASSED]")
        passed_tests += 1
    else:
        print("  [FAILED]")

    # 6. Trend calculation
    print("Test 6: Trend calculation correctness...")
    res = agent_orchestrator.run_investigation(db, "Why did AURA Face Wash satisfaction drop?", brand_name="AURA", product_name="Hydrating Face Wash")
    trend_data = res.get("trend_data", {})
    if trend_data.get("trend") == "INCREASING" and trend_data.get("current_period", {}).get("total") == 28:
        print("  [PASSED]")
        passed_tests += 1
    else:
        print("  [FAILED]", trend_data)

    # 7. Cross-brand memory retrieval
    print("Test 7: Cross-brand memory retrieval...")
    res = agent_orchestrator.run_investigation(db, "AURA Face wash transit leakage and closure failure?", brand_name="AURA", product_name="Hydrating Face Wash")
    memories = res.get("historical_memory", [])
    if len(memories) > 0 and any(m["brand"] == "VIVA" for m in memories):
        print("  [PASSED]")
        passed_tests += 1
    else:
        print("  [FAILED]", memories)

    # 8. Decision persistence
    print("Test 8: Decision persistence...")
    try:
        new_dec = Decision(
            brand_id=aura.id,
            product_id=p_aura.id,
            problem="Transit leakage",
            evidence="{}",
            analysis="capping checked",
            recommendation="calibrate",
            human_decision="APPROVED",
            owner="Sarah",
            status="RESOLVED",
            outcome="Approved"
        )
        db.add(new_dec)
        db.commit()
        persisted = db.query(Decision).filter(Decision.owner == "Sarah").first()
        if persisted and persisted.problem == "Transit leakage":
            print("  [PASSED]")
            passed_tests += 1
        else:
            print("  [FAILED]")
    except Exception as e:
        print("  [FAILED] Exception:", e)

    # 9. Insufficient evidence behavior
    print("Test 9: Insufficient evidence behavior...")
    # Query brand VIVA which has 0 feedbacks and 0 documents seeded
    res = agent_orchestrator.run_investigation(db, "major color variance issue", brand_name="VIVA", product_name="Organic Protein Powder")
    if res.get("status") == "insufficient_evidence":
        print("  [PASSED]")
        passed_tests += 1
    else:
        print("  [FAILED]", res)

    # 10. HITL decision workflow simulation
    print("Test 10: HITL workflow endpoint mock...")
    # Simulate saving decision payload from UI
    decision_payload = {
        "brand_id": aura.id,
        "product_id": p_aura.id,
        "problem": "Leakage test",
        "evidence": "{}",
        "analysis": "Findings summary",
        "recommendation": "Recommendations list",
        "human_decision": "APPROVED",
        "owner": "sarah.jenkins@think9.in",
        "investigation_id": "INV-2026-TEST",
        "priority": "HIGH",
        "decision_type": "PACKAGING_MITIGATION"
    }
    try:
        new_dec = Decision(
            brand_id=decision_payload["brand_id"],
            product_id=decision_payload["product_id"],
            problem=decision_payload["problem"],
            evidence=decision_payload["evidence"],
            analysis=decision_payload["analysis"],
            recommendation=decision_payload["recommendation"],
            human_decision=decision_payload["human_decision"],
            owner=decision_payload["owner"],
            investigation_id=decision_payload["investigation_id"],
            priority=decision_payload["priority"],
            decision_type=decision_payload["decision_type"]
        )
        db.add(new_dec)
        db.commit()
        print("  [PASSED]")
        passed_tests += 1
    except Exception as e:
        print("  [FAILED] Exception:", e)

    # Compile latency stats over 4 execution runs
    avg_latency = np.mean(execution_times)
    median_latency = np.median(execution_times)
    p95_latency = np.percentile(execution_times, 95)

    print("\n==================================================")
    print(f"EVALUATION COMPLETE: Passed {passed_tests}/{total_tests} tests.")
    print(f"Pass Rate: {(passed_tests/total_tests)*100:.1f}%")
    print("--------------------------------------------------")
    print(f"Performance Stats (Query Latency):")
    print(f"  Average: {avg_latency:.3f}s")
    print(f"  Median:  {median_latency:.3f}s")
    print(f"  P95:     {p95_latency:.3f}s")
    print("==================================================")
    
    db.close()

if __name__ == "__main__":
    run_comprehensive_evaluation()
