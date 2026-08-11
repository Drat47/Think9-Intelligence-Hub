import os
import json
import pandas as pd
from typing import List, Dict, Any
from pypdf import PdfReader
from sqlalchemy.orm import Session
from database.db import Document
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class RAGService:
    def __init__(self):
        # We can initialize TF-IDF search for lightweight local search
        self.vectorizer = TfidfVectorizer(stop_words='english')

    def extract_text(self, file_path: str) -> str:
        """Extract text from TXT, PDF or CSV files."""
        _, ext = os.path.splitext(file_path.lower())
        
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
                
        elif ext == '.pdf':
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
            
        elif ext == '.csv':
            df = pd.read_csv(file_path)
            # Convert CSV rows to formatted text sentences for RAG ingestion
            text_lines = []
            for _, row in df.iterrows():
                row_str = ", ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
                text_lines.append(row_str)
            return "\n".join(text_lines)
            
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def chunk_text(self, text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
        """Split text into smaller chunks for RAG."""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - chunk_overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
                
        return chunks

    def ingest_document(self, db: Session, file_path: str, brand_id: int, product_id: int = None, metadata: dict = None) -> List[Document]:
        """Extract text, chunk it, and save chunks to the documents table."""
        filename = os.path.basename(file_path)
        raw_text = self.extract_text(file_path)
        chunks = self.chunk_text(raw_text)
        
        db_docs = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = (metadata or {}).copy()
            chunk_metadata.update({
                "chunk_index": i,
                "total_chunks": len(chunks),
                "source_file": filename
            })
            
            db_doc = Document(
                brand_id=brand_id,
                product_id=product_id,
                filename=filename,
                content=chunk,
                metadata_json=json.dumps(chunk_metadata)
            )
            db.add(db_doc)
            db_docs.append(db_doc)
            
        db.commit()
        return db_docs

    def search_documents(self, db: Session, query: str, brand_id: int = None, product_id: int = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve most relevant document chunks based on brand, product, and semantic TF-IDF query match."""
        # Start querying documents from the database
        query_builder = db.query(Document)
        
        if brand_id is not None:
            if product_id is not None:
                # Retrieve both product-specific and brand-level documents where product_id is NULL
                query_builder = query_builder.filter(
                    Document.brand_id == brand_id,
                    (Document.product_id == product_id) | (Document.product_id.is_(None))
                )
            else:
                query_builder = query_builder.filter(Document.brand_id == brand_id)
            
        docs = query_builder.all()
        
        if not docs:
            return []
            
        # Standardize document contents
        doc_contents = [d.content for d in docs]
        
        try:
            # Fit TF-IDF on retrieved document segments to find cosine similarity with the query
            tfidf_matrix = self.vectorizer.fit_transform(doc_contents)
            query_vec = self.vectorizer.transform([query])
            
            similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
            
            # Map docs to scores and apply product specific boosting
            scored_docs = []
            for idx, doc in enumerate(docs):
                score = float(similarities[idx])
                if score > 0.0:
                    # Boost product-specific documents by 20%
                    if product_id is not None and doc.product_id == product_id:
                        score *= 1.2
                    scored_docs.append((score, doc))
            
            # Sort by score descending
            scored_docs.sort(key=lambda x: x[0], reverse=True)
            
            results = []
            for score, doc in scored_docs[:top_k]:
                results.append({
                    "id": doc.id,
                    "filename": doc.filename,
                    "content": doc.content,
                    "metadata": json.loads(doc.metadata_json) if doc.metadata_json else {},
                    "score": score
                })
            return results
        except Exception:
            # Fallback to keyword matching or first docs if TF-IDF vectorization fails
            results = []
            for doc in docs[:top_k]:
                score = 0.5
                if product_id is not None and doc.product_id == product_id:
                    score = 0.6
                results.append({
                    "id": doc.id,
                    "filename": doc.filename,
                    "content": doc.content,
                    "metadata": json.loads(doc.metadata_json) if doc.metadata_json else {},
                    "score": score
                })
            return results

rag_service = RAGService()
