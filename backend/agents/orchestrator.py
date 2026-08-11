import json
import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from database.db import Brand, Product, ConsumerFeedback, Decision, Document, Investigation
from rag.rag_service import rag_service
from services.llm import llm_service
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def calculate_evidence_strength(total_feedbacks: int, negative_feedbacks: int, documents_count: int, memory_matches_count: int) -> Dict[str, Any]:
    score = 0
    reasons = []
    
    # 1. Feedback counts (max 30 points)
    if total_feedbacks > 0:
        score += min(10, total_feedbacks // 2)  # up to 10 points for volume
        neg_rate = negative_feedbacks / total_feedbacks
        if neg_rate > 0.3:
            score += 20
            reasons.append(f"High ratio of negative feedback detected ({neg_rate*100:.1f}%)")
        elif neg_rate > 0.1:
            score += 10
            reasons.append(f"Moderate ratio of negative feedback detected ({neg_rate*100:.1f}%)")
        reasons.append(f"Analyzed {total_feedbacks} feedback records")
    else:
        reasons.append("No user feedback records available")
        
    # 2. RAG documents (max 35 points)
    if documents_count > 0:
        score += min(35, documents_count * 15)  # 15 points per document up to 35
        reasons.append(f"Found {documents_count} relevant RAG specification/SOP references")
    else:
        reasons.append("No technical RAG documentation matched")
        
    # 3. Memory matches (max 35 points)
    if memory_matches_count > 0:
        score += min(35, memory_matches_count * 15)  # 15 points per match up to 35
        reasons.append(f"Found {memory_matches_count} similar historical decision records")
    else:
        reasons.append("No historical decision memory matched")
        
    score = min(100, max(0, score))
    
    if score >= 70:
        level = "HIGH"
    elif score >= 40:
        level = "MEDIUM"
    else:
        level = "LOW"
        
    return {
        "score": score,
        "level": level,
        "reasons": reasons
    }

def generate_structured_json(prompt: str, system_instruction: str, fallback_func) -> Dict[str, Any]:
    instruction = system_instruction + "\nRespond strictly in valid JSON format."
    response = llm_service.generate(prompt, instruction)
    try:
        clean_res = response.strip()
        if clean_res.startswith("```json"):
            clean_res = clean_res[7:]
        if clean_res.endswith("```"):
            clean_res = clean_res[:-3]
        return json.loads(clean_res.strip())
    except Exception as e:
        print(f"JSON parsing failed, retrying once. Error: {e}")
        # Retry once with strict message
        retry_prompt = f"{prompt}\n\nIMPORTANT: Your previous output was not valid JSON. Please reply with strictly valid JSON only. Do not add markdown or conversational wrappers."
        try:
            res_retry = llm_service.generate(retry_prompt, instruction)
            clean_res = res_retry.strip()
            if clean_res.startswith("```json"):
                clean_res = clean_res[7:]
            if clean_res.endswith("```"):
                clean_res = clean_res[:-3]
            return json.loads(clean_res.strip())
        except Exception:
            return fallback_func()

def search_decision_memory(db: Session, query: str, current_brand_id: int = None, top_k: int = 5) -> List[Dict[str, Any]]:
    decisions = db.query(Decision).all()
    if not decisions:
        return []
        
    documents = []
    for d in decisions:
        text = f"Problem: {d.problem or ''}. Analysis: {d.analysis or ''}. Recommendation: {d.recommendation or ''}. Outcome: {d.outcome or ''}"
        documents.append(text)
        
    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(documents)
        query_vec = vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
        
        results = []
        for idx, sim in enumerate(similarities):
            # Keep matches with similarity above 0.05
            if sim < 0.05:
                continue
            d = decisions[idx]
            brand = db.query(Brand).filter(Brand.id == d.brand_id).first()
            product = db.query(Product).filter(Product.id == d.product_id).first() if d.product_id else None
            
            score = float(sim)
            # Prioritize cross-brand match
            if current_brand_id is not None and d.brand_id != current_brand_id:
                score *= 1.1
                
            results.append({
                "decision_id": d.id,
                "brand": brand.name if brand else "Unknown",
                "product": product.name if product else "N/A",
                "problem": d.problem,
                "recommendation": d.recommendation,
                "outcome": d.outcome,
                "similarity": score
            })
            
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]
    except Exception as e:
        print(f"Memory TF-IDF search failed: {e}")
        # Return basic matches
        results = []
        for d in decisions[:top_k]:
            brand = db.query(Brand).filter(Brand.id == d.brand_id).first()
            product = db.query(Product).filter(Product.id == d.product_id).first() if d.product_id else None
            results.append({
                "decision_id": d.id,
                "brand": brand.name if brand else "Unknown",
                "product": product.name if product else "N/A",
                "problem": d.problem,
                "recommendation": d.recommendation,
                "outcome": d.outcome,
                "similarity": 0.5
            })
        return results

class AgentOrchestrator:
    def run_investigation(self, db: Session, query: str, brand_name: str = None, product_name: str = None) -> Dict[str, Any]:
        """Runs the 5-agent lifecycle with true data calculations and returns the results."""
        logs = []
        
        # --- Step 1: Router Agent ---
        logs.append({"agent": "Router Agent", "status": "processing", "message": "Parsing query intent, brand, and product context..."})
        
        brand_obj = None
        product_obj = None
        
        # If parameters are explicitly passed, validate them
        if brand_name:
            brand_obj = db.query(Brand).filter(Brand.name.ilike(brand_name)).first()
            if not brand_obj:
                return {
                    "status": "not_found",
                    "message": f"Brand '{brand_name}' not found."
                }
            if product_name:
                product_obj = db.query(Product).filter(Product.name.ilike(product_name), Product.brand_id == brand_obj.id).first()
                if not product_obj:
                    return {
                        "status": "not_found",
                        "message": f"Product '{product_name}' not found or does not belong to Brand '{brand_name}'."
                    }
        else:
            # Router identifies brand and product from query
            all_brands = db.query(Brand).all()
            brand_names = [b.name for b in all_brands]
            
            router_prompt = f"""Identify the brand and product names from the user query.
Query: "{query}"
Available Brands: {", ".join(brand_names)}
Format response strictly as JSON:
{{"brand": "BRAND_NAME_OR_NULL", "product": "PRODUCT_NAME_OR_NULL"}}"""
            
            def router_fallback():
                return {"brand": "null", "product": "null"}
                
            router_res = generate_structured_json(router_prompt, "You are a query router agent.", router_fallback)
            extracted_brand = router_res.get("brand")
            extracted_product = router_res.get("product")
            
            if extracted_brand and extracted_brand.lower() != "null":
                brand_obj = db.query(Brand).filter(Brand.name.ilike(extracted_brand)).first()
                if not brand_obj:
                    # Look for substring match
                    for b in all_brands:
                        if b.name.lower() in query.lower():
                            brand_obj = b
                            break
            else:
                # Substring check fallback
                for b in all_brands:
                    if b.name.lower() in query.lower():
                        brand_obj = b
                        break
                        
            if brand_obj and extracted_product and extracted_product.lower() != "null":
                product_obj = db.query(Product).filter(Product.name.ilike(extracted_product), Product.brand_id == brand_obj.id).first()
                if not product_obj:
                    # Check substring match for products
                    products_for_brand = db.query(Product).filter(Product.brand_id == brand_obj.id).all()
                    for p in products_for_brand:
                        if p.name.lower() in query.lower():
                            product_obj = p
                            break

        if not brand_obj:
            return {
                "status": "needs_context",
                "message": "I couldn't confidently identify the brand. Please select a brand or specify it in your question."
            }

        logs.append({
            "agent": "Router Agent",
            "status": "completed",
            "message": f"Routed query to Brand: {brand_obj.name}, Product: {product_obj.name if product_obj else 'None'}"
        })

        # --- Step 2: Research Agent ---
        logs.append({"agent": "Research Agent", "status": "processing", "message": "Fetching user feedback reviews, tickets and corporate SOP specs..."})
        
        # Fetch feedbacks
        fb_query = db.query(ConsumerFeedback).filter(ConsumerFeedback.brand_id == brand_obj.id)
        if product_obj:
            fb_query = fb_query.filter(ConsumerFeedback.product_id == product_obj.id)
        feedbacks = fb_query.all()
        
        # Run RAG Search for documents (utilizes the boosted product-specific lookup)
        rag_results = rag_service.search_documents(
            db=db, 
            query=query, 
            brand_id=brand_obj.id, 
            product_id=product_obj.id if product_obj else None,
            top_k=3
        )
        
        logs.append({
            "agent": "Research Agent",
            "status": "completed",
            "message": f"Retrieved {len(feedbacks)} feedback records and {len(rag_results)} relevant document segments."
        })

        # --- Step 3: Analysis Agent (Trend & Structured Findings) ---
        logs.append({"agent": "Analysis Agent", "status": "processing", "message": "Evaluating complaints and metrics to calculate emerging trends..."})
        
        # Real Trend Calculation
        now = datetime.datetime.utcnow()
        thirty_days_ago = now - datetime.timedelta(days=30)
        sixty_days_ago = now - datetime.timedelta(days=60)
        
        curr_total = 0
        curr_neg = 0
        prev_total = 0
        prev_neg = 0
        low_rating_complaints = []
        
        for fb in feedbacks:
            if fb.date >= thirty_days_ago:
                curr_total += 1
                if fb.rating and fb.rating <= 2:
                    curr_neg += 1
                    low_rating_complaints.append(fb.content)
            elif fb.date >= sixty_days_ago:
                prev_total += 1
                if fb.rating and fb.rating <= 2:
                    prev_neg += 1
                    
        curr_rate = (curr_neg / curr_total * 100) if curr_total > 0 else 0.0
        prev_rate = (prev_neg / prev_total * 100) if prev_total > 0 else 0.0
        diff = curr_rate - prev_rate
        
        if curr_total == 0 and prev_total == 0:
            trend_str = "INSUFFICIENT_DATA"
        elif diff > 5.0:
            trend_str = "INCREASING"
        elif diff < -5.0:
            trend_str = "DECREASING"
        else:
            trend_str = "STABLE"
            
        trend_payload = {
            "current_period": {
                "total": curr_total,
                "negative": curr_neg,
                "negative_rate": round(curr_rate, 2)
            },
            "previous_period": {
                "total": prev_total,
                "negative": prev_neg,
                "negative_rate": round(prev_rate, 2)
            },
            "change_percentage_points": round(diff, 2),
            "trend": trend_str
        }

        # Structured Analysis LLM prompt
        analysis_prompt = f"""Analyze these customer complaints for brand {brand_obj.name} and product {product_obj.name if product_obj else 'All Products'}:
Feedback Stats: Current total={curr_total}, current negative={curr_neg}, rate={curr_rate:.1f}%. Previous total={prev_total}, previous negative={prev_neg}, rate={prev_rate:.1f}%. Trend={trend_str}.
Complaints list: {json.dumps(low_rating_complaints[:20])}

Specify the main issue causing dissatisfaction and summarize the key findings.
Format response strictly as JSON:
{{
  "finding": "Main problem description",
  "issue_category": "Category name",
  "key_themes": ["theme1", "theme2"],
  "likely_causes": ["cause1", "cause2"],
  "trend": "INCREASING|DECREASING|STABLE|UNKNOWN",
  "supporting_evidence": ["evidence1", "evidence2"]
}}"""

        def analysis_fallback():
            return {
                "finding": "High complaint volume detected in recent reviews.",
                "issue_category": "Customer Support",
                "key_themes": ["general quality complaints"],
                "likely_causes": ["production batch quality variance"],
                "trend": trend_str,
                "supporting_evidence": [f"Negative rate {curr_rate:.1f}% in the last 30 days"]
            }

        analysis_results = generate_structured_json(analysis_prompt, "You are a Customer Experience Analyst.", analysis_fallback)

        logs.append({
            "agent": "Analysis Agent",
            "status": "completed",
            "message": f"Analyzed {curr_total} reviews. Primary finding: {analysis_results.get('finding', 'Quality Issue')}"
        })

        # --- Step 4: Memory Agent ---
        logs.append({"agent": "Memory Agent", "status": "processing", "message": "Querying institutional memory database for similar previous incidents..."})
        
        # Combine query, findings, and themes for semantic lookup
        memory_query = f"{query} {analysis_results.get('finding', '')} {' '.join(analysis_results.get('key_themes', []))}"
        similar_decisions = search_decision_memory(db, memory_query, current_brand_id=brand_obj.id, top_k=3)
        
        logs.append({
            "agent": "Memory Agent",
            "status": "completed",
            "message": f"Found {len(similar_decisions)} historical decision records matching the query context."
        })

        # --- Explicit Insufficient Evidence State check ---
        if len(feedbacks) == 0 and len(rag_results) == 0 and len(similar_decisions) == 0:
            return {
                "status": "insufficient_evidence",
                "message": "I couldn't find sufficient evidence in the Think9 knowledge base to answer this reliably."
            }

        # --- Step 5: Recommendation Agent ---
        logs.append({"agent": "Recommendation Agent", "status": "processing", "message": "Consolidating analysis and memories into actionable proposals..."})
        
        # Transparent Confidence Score calculation
        confidence_details = calculate_evidence_strength(
            total_feedbacks=len(feedbacks),
            negative_feedbacks=curr_neg + prev_neg,
            documents_count=len(rag_results),
            memory_matches_count=len(similar_decisions)
        )
        
        rec_prompt = f"""Generate a detailed final recommendation deck.
Context:
- Brand: {brand_obj.name}
- Product: {product_obj.name if product_obj else 'Unknown'}
- Query: {query}
- Trend: {trend_str}
- Analysis findings: {json.dumps(analysis_results)}
- Document details: {json.dumps(rag_results)}
- Historic decisions: {json.dumps(similar_decisions)}
- Confidence calculation: score={confidence_details['score']}, level={confidence_details['level']}, reasons={json.dumps(confidence_details['reasons'])}

Provide clear actionable recommendations.
Format response strictly as JSON:
{{
  "finding": "Main core summary finding",
  "likely_causes": ["cause1"],
  "recommendations": ["recommendation1", "recommendation2"],
  "confidence_level": "HIGH|MEDIUM|LOW"
}}"""

        def rec_fallback():
            return {
                "finding": analysis_results.get("finding", "Quality issues identified."),
                "likely_causes": analysis_results.get("likely_causes", ["Unknown variables."]),
                "recommendations": ["Perform a thorough manual audit of recent product feedback and production logs."],
                "confidence_level": confidence_details["level"]
            }

        rec_results = generate_structured_json(rec_prompt, "You are a Senior Recommendation Agent.", rec_fallback)

        logs.append({
            "agent": "Recommendation Agent",
            "status": "completed",
            "message": "Final recommendation report generated successfully."
        })

        # Build investigation traceability identifier
        import uuid
        unique_suffix = uuid.uuid4().hex[:6].upper()
        inv_id = f"INV-{datetime.datetime.now().year}-{unique_suffix}"

        return {
            "status": "success",
            "investigation_id": inv_id,
            "brand_id": brand_obj.id,
            "product_id": product_obj.id if product_obj else None,
            "query": query,
            "logs": logs,
            "trend_data": trend_payload,
            "findings": analysis_results.get("finding"),
            "evidence": {
                "negative_feedbacks_count": curr_neg,
                "total_feedbacks_count": curr_total,
                "supporting_documents": [r["filename"] for r in rag_results],
                "documents_details": rag_results
            },
            "historical_memory": similar_decisions,
            "recommendation": rec_results.get("recommendations"),
            "recommendation_text": "\n".join([f"- {r}" for r in rec_results.get("recommendations", [])]),
            "confidence": confidence_details,
            "analysis_agent_output": analysis_results,
            "recommendation_agent_output": rec_results
        }

agent_orchestrator = AgentOrchestrator()
