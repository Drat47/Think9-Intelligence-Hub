import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys

# Ensure backend directory is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import Base, Brand, Product, Document
from rag.rag_service import rag_service

# Setup mock database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        # Seed test Brand and Product
        brand = Brand(name="TestBrand", description="Description")
        db.add(brand)
        db.commit()
        db.refresh(brand)
        
        product = Product(brand_id=brand.id, name="TestProduct", sku="TEST-SKU", description="Desc")
        db.add(product)
        db.commit()
        db.refresh(product)
        
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_chunking():
    text = "Hello world " * 100
    chunks = rag_service.chunk_text(text, chunk_size=10, chunk_overlap=2)
    assert len(chunks) > 1
    assert all(len(c.split()) <= 10 for c in chunks)

def test_ingestion_and_search(db_session):
    # Create a temp txt file
    temp_file = "test_doc.txt"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write("The packaging supplier for TestProduct has high leakage defects. We need to check cap torque limits.")
        
    try:
        brand = db_session.query(Brand).first()
        product = db_session.query(Product).first()
        
        # Ingest
        rag_service.ingest_document(
            db=db_session,
            file_path=temp_file,
            brand_id=brand.id,
            product_id=product.id,
            metadata={"department": "QA"}
        )
        
        # Verify db counts
        docs = db_session.query(Document).all()
        assert len(docs) > 0
        assert docs[0].filename == temp_file
        
        # Search
        results = rag_service.search_documents(
            db=db_session,
            query="leakage packaging cap torque",
            brand_id=brand.id,
            top_k=1
        )
        
        assert len(results) == 1
        assert "leakage defects" in results[0]["content"]
        assert results[0]["score"] > 0.0
        
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
