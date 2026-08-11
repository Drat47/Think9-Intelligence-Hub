import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./think9_intelligence.db")

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Brand(Base):
    __tablename__ = "brands"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    products = relationship("Product", back_populates="brand", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="brand", cascade="all, delete-orphan")
    feedback = relationship("ConsumerFeedback", back_populates="brand", cascade="all, delete-orphan")
    decisions = relationship("Decision", back_populates="brand", cascade="all, delete-orphan")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, index=True, nullable=False)
    sku = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    brand = relationship("Brand", back_populates="products")
    documents = relationship("Document", back_populates="product", cascade="all, delete-orphan")
    feedback = relationship("ConsumerFeedback", back_populates="product", cascade="all, delete-orphan")
    decisions = relationship("Decision", back_populates="product", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=True)
    filename = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=True) # JSON stored as text
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    brand = relationship("Brand", back_populates="documents")
    product = relationship("Product", back_populates="documents")

class ConsumerFeedback(Base):
    __tablename__ = "consumer_feedback"
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    source = Column(String, nullable=False) # "review", "support", "social"
    rating = Column(Integer, nullable=True)
    content = Column(Text, nullable=False)
    date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    brand = relationship("Brand", back_populates="feedback")
    product = relationship("Product", back_populates="feedback")

class Decision(Base):
    __tablename__ = "decisions"
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=True)
    problem = Column(Text, nullable=False)
    evidence = Column(Text, nullable=True) # JSON stored as string
    analysis = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    human_decision = Column(String, nullable=False) # APPROVED, MODIFIED, REJECTED
    owner = Column(String, nullable=False)
    status = Column(String, default="RESOLVED") # RESOLVED, PENDING
    outcome = Column(Text, nullable=True)
    investigation_id = Column(String, nullable=True)
    priority = Column(String, nullable=True)
    decision_type = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    brand = relationship("Brand", back_populates="decisions")
    product = relationship("Product", back_populates="decisions")

class Investigation(Base):
    __tablename__ = "investigations"
    id = Column(String, primary_key=True, index=True) # e.g. INV-2026-00001
    query = Column(Text, nullable=False)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=True)
    findings = Column(Text, nullable=True)
    confidence_score = Column(Integer, nullable=True)
    confidence_level = Column(String, nullable=True)
    trend = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)
    # Safely perform inline migration if columns are missing
    from sqlalchemy import text
    with engine.begin() as conn:
        # Check column existence for decisions
        columns_info = conn.execute(text("PRAGMA table_info(decisions)")).fetchall()
        existing_columns = [col[1] for col in columns_info]
        if "investigation_id" not in existing_columns:
            conn.execute(text("ALTER TABLE decisions ADD COLUMN investigation_id TEXT"))
        if "priority" not in existing_columns:
            conn.execute(text("ALTER TABLE decisions ADD COLUMN priority TEXT"))
        if "decision_type" not in existing_columns:
            conn.execute(text("ALTER TABLE decisions ADD COLUMN decision_type TEXT"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
