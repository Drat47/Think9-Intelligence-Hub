import sys
import os
import datetime
import json

# Ensure backend directory is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import init_db, SessionLocal, Brand, Product, ConsumerFeedback, Document, Decision

def seed_data():
    print("Initializing database...")
    init_db()
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(Brand).count() > 0:
            print("Database already contains data. Skipping seeding.")
            return

        print("Seeding brands...")
        # 1. Brands
        aura = Brand(name="AURA", description="Premium clean beauty and organic skincare brand specializing in natural botanical formulations.")
        nexa = Brand(name="NEXA", description="Next-generation smart home appliances and connected kitchen devices designed for efficiency.")
        viva = Brand(name="VIVA", description="Active wellness, premium organic nutrition, and dietary supplements brand.")
        db.add_all([aura, nexa, viva])
        db.commit()

        # Refresh to get IDs
        db.refresh(aura)
        db.refresh(nexa)
        db.refresh(viva)

        print("Seeding products...")
        # 2. Products
        p_aura = Product(brand_id=aura.id, name="Hydrating Face Wash", sku="AURA-FW-HYD-01", description="Gentle hydrating facial cleanser with aloe vera and hyaluronic acid.")
        p_nexa = Product(brand_id=nexa.id, name="Smart Blender", sku="NEXA-BL-SM-05", description="App-connected 1200W high-speed blender with preset program modes.")
        p_viva = Product(brand_id=viva.id, name="Organic Protein Powder", sku="VIVA-PR-ORG-10", description="Plant-based organic chocolate protein powder with probiotics.")
        db.add_all([p_aura, p_nexa, p_viva])
        db.commit()

        db.refresh(p_aura)
        db.refresh(p_nexa)
        db.refresh(p_viva)

        print("Seeding consumer feedback...")
        # 3. Consumer Feedback (Last 30 Days and older)
        # We will create feedback with a decline trend for AURA Face Wash in the last 30 days due to packaging leakage.
        now = datetime.datetime.utcnow()
        feedback_list = []

        # AURA Face wash reviews: Packaging leakage complaint spikes in last 30 days
        for i in range(1, 15):
            date_fb = now - datetime.timedelta(days=i)
            # Leakage complaints
            feedback_list.append(ConsumerFeedback(
                brand_id=aura.id,
                product_id=p_aura.id,
                source="review",
                rating=1,
                content=f"The product itself is great, but the package was leaking when it arrived! Liquid got all over my box.",
                date=date_fb
            ))
            feedback_list.append(ConsumerFeedback(
                brand_id=aura.id,
                product_id=p_aura.id,
                source="support",
                rating=2,
                content=f"Customer received facial wash with cracked flip-top cap. Liquid leaked and ruined other items in the delivery order.",
                date=date_fb
            ))

        # Older positive reviews for AURA Face Wash (satisfaction was high before 30 days ago)
        for i in range(35, 60):
            date_fb = now - datetime.timedelta(days=i)
            feedback_list.append(ConsumerFeedback(
                brand_id=aura.id,
                product_id=p_aura.id,
                source="review",
                rating=5,
                content=f"Absolutely love this face wash. Super hydrating and feels very clean.",
                date=date_fb
            ))

        # Add NEXA feedback (Blender overheating complaints)
        for i in range(1, 5):
            date_fb = now - datetime.timedelta(days=i * 2)
            feedback_list.append(ConsumerFeedback(
                brand_id=nexa.id,
                product_id=p_nexa.id,
                source="review",
                rating=2,
                content="Blender starts smelling like burnt plastic after running for 2 minutes straight on high speed.",
                date=date_fb
            ))
            feedback_list.append(ConsumerFeedback(
                brand_id=nexa.id,
                product_id=p_nexa.id,
                source="support",
                rating=1,
                content="Customer reported blender base got extremely hot to touch and shut down automatically.",
                date=date_fb
            ))

        # Add VIVA feedback (Vanilla flavor issues)
        for i in range(1, 5):
            date_fb = now - datetime.timedelta(days=i * 3)
            feedback_list.append(ConsumerFeedback(
                brand_id=viva.id,
                product_id=p_viva.id,
                source="review",
                rating=3,
                content="Taste is good but does not dissolve completely in cold almond milk. Leaves chalky clumps.",
                date=date_fb
            ))

        db.add_all(feedback_list)
        db.commit()

        print("Seeding documents...")
        # 4. Ingestible documents/SOPs/Product specs
        doc_aura = Document(
            brand_id=aura.id,
            product_id=p_aura.id,
            filename="aura_facewash_specs.txt",
            content="""AURA Hydrating Face Wash Product Specification:
- Active Ingredients: Hyaluronic Acid 1%, Aloe Vera Extract 5%, Chamomile Extract 2%.
- Packaging: 200ml clear PET bottle with a white Polypropylene (PP) flip-top cap.
- Supplier: CapTech Packaging Solutions Inc.
- Production Site: Plant 4, Mumbai.
- Quality Control Tolerances: Leakage test target pressure 0.3 bar for 30 seconds.""",
            metadata_json=json.dumps({"department": "R&D", "document_type": "Specification", "date": "2025-01-10"})
        )

        doc_packaging_sop = Document(
            brand_id=aura.id,
            product_id=None,
            filename="packaging_inspection_sop.txt",
            content="""STANDARD OPERATING PROCEDURE (SOP): PACKAGING QUALITY ASSURANCE
Ref: SOP-QA-PACK-09. Version: 2.1.
- All flip-top caps must undergo a torque check upon receiving from suppliers.
- Standard application torque range: 12 to 18 inch-pounds.
- Defect Classification: Any cap showing micro-cracks near the hinge during stress testing must be immediately flagged. Supplier replacement terms apply.""",
            metadata_json=json.dumps({"department": "Quality Assurance", "document_type": "SOP", "date": "2025-06-15"})
        )

        # 5. Seeding Institutional Memory (Historic decisions)
        # Create a historical incident of packaging leakage that occurred in VIVA a few months ago.
        # This allows us to prove cross-brand learning.
        historic_decision = Decision(
            brand_id=viva.id,
            product_id=p_viva.id,
            problem="Customer complaints regarding shaker-cup leakage and cracked cap hinges for VIVA protein shaker bottles.",
            evidence=json.dumps({
                "source": "customer reviews & support tickets",
                "affected_percentage": "14.2% of orders",
                "defect_code": "PP-CAP-HINGE-CRACK"
            }),
            analysis="R&D analyzed returned units and found supplier used a low-density PP copolymer batch that becomes brittle at cold temperatures.",
            recommendation="1. Negotiated replacement batch with supplier. 2. Changed QC specification to include drop test under frozen conditions (-5C). 3. Shifted to heavy-duty cap supplier (Apex Caps Ltd).",
            human_decision="APPROVED",
            owner="Aditi Sharma (VP Operations)",
            status="RESOLVED",
            outcome="Complaint rate fell from 14.2% to 0.4% in 30 days. Quality standards updated globally across VIVA.",
            created_at=now - datetime.timedelta(days=120)
        )

        db.add_all([doc_aura, doc_packaging_sop, historic_decision])
        db.commit()
        print("Database seeded successfully with synthetic data!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
