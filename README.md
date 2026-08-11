# Think9 Intelligence Hub
**Centralized Decision Support & Institutional Quality memory Log**

**Author & Architect**: Dharmesh Singhal

Think9 Intelligence Hub is a centralized decision support and quality management platform built to optimize operational speed and capture institutional knowledge across Think9's portfolio of 30+ consumer brands. 

The platform monitors customer feedback, cross-references emerging quality anomalies against product and brand-level standard operating procedures (RAG), queries portfolio-wide historic resolutions using TF-IDF text similarity to match past precedents, hosts a Human-in-the-Loop (HITL) gatekeeper for action approval, and archives finalized choices to a central repository to accelerate future troubleshooting.

---

## 1. Project Overview & Business Value
With 30+ distinct brands (such as AURA, NEXA, and VIVA), operational data is often siloed. When Brand A solves a cap leakage packaging issue, Brand B should not have to repeat the entire research and root-cause analysis cycle.

The **Think9 Intelligence Hub** resolves this by providing:
- **Centralized Feedback Ingestion**: Collects customer reviews, tickets, and ratings.
- **Hierarchical RAG Retrieval**: Fetches both brand-wide and product-specific documentation, applying a **1.2x similarity boost** to product-specific matches.
- **Mathematical Period Comparison**: Calculates chronological negative feedback rates (Current 30 days vs Previous 30 days) to identify trend directions.
- **Semantic Memory recall**: Uses TF-IDF and cosine similarity to index and recall previous decisions across all brand portfolios.
- **Human-In-The-Loop (HITL) Gates**: Provides an editing and review panel for quality leads to confirm or modify recommendations.

---

## 2. System Architecture & Data Flow

```
   DATA INGESTION (Consumer Reviews, Tickets)
                     │
                     ▼
        CENTRAL DATA & RAG SERVICES
   (Product SOPs, Guidelines & Brand Manuals)
                     │
                     ▼
              ROUTER AGENT
    (Matches brand/product query targets)
                     │
                     ▼
             RESEARCH AGENT
    (Gathers feedbacks & boosts RAG chunks)
                     │
                     ▼
             ANALYSIS AGENT
    (Chronological trend negative rate checks)
                     │
                     ▼
              MEMORY AGENT
    (Surfaces portfolio precedents via TF-IDF)
                     │
                     ▼
          RECOMMENDATION AGENT
    (Calculates evidence scores & builds proposals)
                     │
                     ▼
         HUMAN-IN-THE-LOOP PANEL
  (Reviewer: Approve, Modify, or Reject Proposal)
                     │
                     ▼
             DECISION MEMORY
   (Resolution saved to DB for future recall)
```

---

## 3. Technology Stack
- **Backend Framework**: Python (FastAPI, Uvicorn, SQLAlchemy)
- **Data Science & ML**: Scikit-Learn (TF-IDF Vectorization, Cosine Similarity), NumPy, SQLite
- **Frontend Framework**: React (Vite, CSS glassmorphic dark-mode design, Lucide Icons)
- **Verification Engine**: Pytest, isolated SQLite memory engine sharing (`StaticPool`)

---

## 4. Getting Started (Running Locally)

### Prerequisites
- Python 3.10+
- Node.js 18+

### Setup Backend
1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Initialize and seed the SQLite database:
   ```bash
   python backend/database/seed.py
   ```
3. Start the FastAPI server (Run from the `backend` directory to resolve relative database imports):
   ```bash
   cd backend
   uvicorn main:app --port 8000
   ```
   The API documentation will be available at `http://127.0.0.1:8000/docs`.

### Setup Frontend
1. Navigate to the `frontend` directory:
   ```bash
   cd ../frontend
   ```
2. Install npm packages:
   ```bash
   npm install
   ```
3. Launch the development server on port 5173:
   ```bash
   npm run dev -- --port 5173
   ```
   Access the dashboard cockpit at `http://localhost:5173`.

---

## 5. Demo Walkthrough Script
1. Open the UI. Confirm that the dashboard loads the live database metrics.
2. Go to **Ask Think9**, select brand **AURA** and product **Hydrating Face Wash**, and query:
   > *"Why has customer satisfaction declined for AURA Face Wash over the last 30 days and what should we do?"*
3. Watch the logs execute. View the trend analysis card (showing the negative rate change) and the RAG sources listing exact matching segments and files.
4. Click **Review Action Recommendations**, input your reviewer name, and select **APPROVE DECISION**.
5. Go to **Decision Memory** and search `"leakage"`. Confirm the newly approved decision is recorded alongside VIVA's shaker precedent.

For more details, see the walkthrough script in [demo_script.md](file:///e:/Projects/New%20folder/demo/demo_script.md).

---

## 6. Evaluation Framework & Testing
We include a 10-point evaluation script verifying routing logic, RAG retrieval accuracy, chronological trend math, memory matching limits, and insufficient data handlers.

To run the automated isolated test suite:
```bash
pytest
```

To run the comprehensive 10-point evaluation suite:
```bash
python backend/demo/evaluate.py
```

### Evaluation Metrics (Calculated Locally)
- **Routing Accuracy**: 100% (Correct context resolution)
- **RAG Integrity**: 100% (Boosts product specific document segments)
- **Memory Precision**: 100% (TF-IDF returns matches above 0.10 similarity)
- **Average Query Latency**: **~60ms** (Under 130ms p95)
