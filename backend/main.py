import os
import json
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from database.db import get_db, init_db, Brand, Product, Document, Decision, ConsumerFeedback, Investigation
from agents.orchestrator import agent_orchestrator
from rag.rag_service import rag_service
from services.llm import llm_service
from dotenv import load_dotenv
import shutil

load_dotenv()

# Initialize DB on start
init_db()
from database.seed import seed_data
seed_data()

app = FastAPI(
    title="Think9 Intelligence Hub API",
    description="Centralized AI decision intelligence layer.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Schemas
class DecisionCreate(BaseModel):
    brand_id: int
    product_id: Optional[int] = None
    problem: str
    evidence: str  # JSON String
    analysis: str
    recommendation: str
    human_decision: str  # APPROVED, MODIFIED, REJECTED
    owner: str
    status: Optional[str] = "RESOLVED"
    outcome: Optional[str] = None
    investigation_id: Optional[str] = None
    priority: Optional[str] = None
    decision_type: Optional[str] = None

class InvestigationRequest(BaseModel):
    query: str
    brand_name: Optional[str] = None
    product_name: Optional[str] = None

@app.get("/")
def read_root():
    return {
        "status": "online",
        "app": "Think9 Intelligence Hub Backend",
        "version": "1.0.0",
        "mock_llm": os.getenv("USE_MOCK_LLM", "true").lower() == "true"
    }

# --- Dynamic Metrics API ---
@app.get("/api/metrics")
def get_metrics(db: Session = Depends(get_db)):
    try:
        brands_count = db.query(Brand).count()
        products_count = db.query(Product).count()
        documents_count = db.query(Document).count()
        decisions_count = db.query(Decision).count()
        investigations_count = db.query(Investigation).count()
        return {
            "brands": brands_count,
            "products": products_count,
            "documents": documents_count,
            "decisions": decisions_count,
            "investigations": investigations_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Core Brand & Product APIs ---
@app.get("/api/brands")
def get_brands(db: Session = Depends(get_db)):
    brands = db.query(Brand).all()
    return [{"id": b.id, "name": b.name, "description": b.description} for b in brands]

@app.get("/api/brands/{brand_id}/products")
def get_products(brand_id: int, db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.brand_id == brand_id).all()
    return [{"id": p.id, "brand_id": p.brand_id, "name": p.name, "sku": p.sku, "description": p.description} for p in products]

# --- Document Upload & Retrieval APIs ---
@app.post("/api/documents/upload")
def upload_document(
    brand_id: int = Form(...),
    product_id: Optional[int] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Save temp file
    temp_dir = "./temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, file.filename)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        metadata = {"uploaded_at": str(os.path.getmtime(temp_path))}
        db_docs = rag_service.ingest_document(
            db=db,
            file_path=temp_path,
            brand_id=brand_id,
            product_id=product_id,
            metadata=metadata
        )
        return {"status": "success", "message": f"Successfully ingested document '{file.filename}' into {len(db_docs)} chunks."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# --- Investigation Agent Orchestration API ---
@app.post("/api/investigate")
def run_investigation(req: InvestigationRequest, db: Session = Depends(get_db)):
    try:
        result = agent_orchestrator.run_investigation(
            db=db,
            query=req.query,
            brand_name=req.brand_name,
            product_name=req.product_name
        )
        # Persist successful investigations
        if result.get("status") == "success":
            new_inv = Investigation(
                id=result["investigation_id"],
                query=result["query"],
                brand_id=result["brand_id"],
                product_id=result["product_id"],
                findings=result["findings"],
                confidence_score=result["confidence"]["score"],
                confidence_level=result["confidence"]["level"],
                trend=result["trend_data"]["trend"]
            )
            db.add(new_inv)
            db.commit()
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# --- Decision Memory APIs (Human-In-The-Loop) ---
@app.post("/api/decisions")
def create_decision(decision: DecisionCreate, db: Session = Depends(get_db)):
    try:
        new_dec = Decision(
            brand_id=decision.brand_id,
            product_id=decision.product_id,
            problem=decision.problem,
            evidence=decision.evidence,
            analysis=decision.analysis,
            recommendation=decision.recommendation,
            human_decision=decision.human_decision,
            owner=decision.owner,
            status=decision.status,
            outcome=decision.outcome,
            investigation_id=decision.investigation_id,
            priority=decision.priority,
            decision_type=decision.decision_type
        )
        db.add(new_dec)
        db.commit()
        db.refresh(new_dec)
        return {"status": "success", "message": "Decision successfully saved to institutional memory.", "decision_id": new_dec.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/decisions")
def get_decisions(query: Optional[str] = None, db: Session = Depends(get_db)):
    """Search or list historical decision memory."""
    dec_query = db.query(Decision)
    
    if query:
        # Search criteria across problem, analysis, and recommendations
        search_filter = f"%{query}%"
        dec_query = dec_query.filter(
            (Decision.problem.ilike(search_filter)) | 
            (Decision.analysis.ilike(search_filter)) |
            (Decision.recommendation.ilike(search_filter))
        )
        
    decisions = dec_query.order_by(Decision.created_at.desc()).all()
    results = []
    
    for d in decisions:
        brand = db.query(Brand).filter(Brand.id == d.brand_id).first()
        product = db.query(Product).filter(Product.id == d.product_id).first() if d.product_id else None
        
        results.append({
            "id": d.id,
            "brand_name": brand.name if brand else "Unknown",
            "product_name": product.name if product else "N/A",
            "problem": d.problem,
            "evidence": json.loads(d.evidence) if d.evidence else {},
            "analysis": d.analysis,
            "recommendation": d.recommendation,
            "human_decision": d.human_decision,
            "owner": d.owner,
            "status": d.status,
            "outcome": d.outcome,
            "created_at": d.created_at
        })
        
    return results
