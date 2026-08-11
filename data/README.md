# Think9 Intelligence Hub - Database & Seed Files

This directory is designated for database files and seeds.

* **SQLite Database**: The application uses SQLite for fast local deployment. On first run, the SQLite database is automatically generated and seeded with synthetic data for brands (AURA, NEXA, VIVA), products, documents, and historical memory.
* **Production Database**: You can configure an external PostgreSQL database by supplying the `DATABASE_URL` environment variable.
