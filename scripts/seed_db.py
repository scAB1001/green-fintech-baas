# scripts/seed_db.py
import asyncio
import json
import sys
from pathlib import Path

from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.models.company import Company

# Add the src/ directory to the Python path so it finds 'app'
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


async def seed_companies():
    fixture_path = project_root / "tests" / "fixtures" / "companies.json"

    if not fixture_path.exists():
        print(f"❌ Fixture not found at {fixture_path}")
        return

    with open(fixture_path) as f:
        data = json.load(f)

    # Use the async context manager for the database session
    async with AsyncSessionLocal() as db:
        try:
            companies_added = 0
            for item in data:
                # Async SQLAlchemy 2.0 uses 'select' instead of 'query'
                query = select(Company).where(Company.name == item["name"])
                result = await db.execute(query)
                existing = result.scalars().first()

                if not existing:
                    company = Company(**item)
                    db.add(company)
                    companies_added += 1

            await db.commit()
            print(f"✅ Successfully seeded {companies_added} companies.")
        except Exception as e:
            await db.rollback()
            print(f"❌ Error seeding database: {e}")

if __name__ == "__main__":
    print("🌱 Starting database seed...")
    # Because this is a standard python script (not FastAPI),
    # we have to manually start the async event loop
    asyncio.run(seed_companies())
