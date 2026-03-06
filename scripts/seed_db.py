# scripts/seed_db.py
import asyncio
import json
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import insert, select

from app.core.logger import logger
from app.database.session import AsyncSessionLocal
from app.models.company import Company
from app.models.national_energy import NationalEnergy
from app.models.regional_emission import RegionalEmission

# Add the src/ directory to the Python path so it finds 'app'
# This MUST happen before importing any 'app' modules.
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


async def seed_companies(db):
    existing = (await db.execute(select(Company).limit(1))).scalars().first()
    if existing:
        logger.info("Companies already seeded, skipping.")
        return

    fixture_path = project_root / "tests" / "fixtures" / "companies.json"

    if not fixture_path.exists():
        logger.error(f"Fixture not found at {fixture_path}")
        return

    with open(fixture_path) as f:
        data = json.load(f)

    # Use the async context manager for the database session
    try:
        companies_added = 0
        for item in data:
            query = select(Company).where(Company.name == item["name"])
            result = await db.execute(query)
            existing = result.scalars().first()

            if not existing:
                company = Company(**item)
                db.add(company)
                companies_added += 1

        await db.commit()
        if companies_added > 0:
            logger.info(f"Successfully seeded {companies_added} companies.")
        else:
            logger.info("Companies already seeded.")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error seeding companies: {e}")


async def seed_regional_emissions(db):
    existing = (await db.execute(select(RegionalEmission).limit(1))).scalars().first()
    if existing:
        logger.info("Regional emissions already seeded, skipping.")
        return

    xlsx_path = project_root / "data" / "2005-23-uk-local-authority-ghg-emissions.xlsx"

    if not xlsx_path.exists():
        logger.error(f"Excel file not found at {xlsx_path}")
        return

    logger.info("Processing Regional GHG Emissions...")
    try:
        df = pd.read_excel(
            xlsx_path,
            sheet_name="1_1",
            skiprows=4,
            engine="openpyxl"
        )

        columns_to_keep = {
            'Local Authority': 'local_authority',
            'Calendar Year': 'year',
            'Industry Total': 'industry_total',
            'Commercial Total': 'commercial_total',
            'Public Sector Total': 'public_sector_total',
            'Domestic Total': 'domestic_total',
            'Transport Total': 'transport_total',
            'Agriculture Total': 'agriculture_total',
            'Grand Total': 'grand_total'
        }

        available_cols = [
            col for col in columns_to_keep if col in df.columns]
        df = df[available_cols].rename(
            columns={k: columns_to_keep[k] for k in available_cols})

        df = df.dropna(subset=['local_authority', 'year'])

        numeric_cols = [col for col in df.columns if col not in [
            'local_authority', 'year']]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

        df['year'] = df['year'].astype(int)

        records = df.to_dict(orient="records")
        if records:
            # Chunk the inserts to avoid PostgreSQL's 2^15 or 32767 parameter limit
            chunk_size = 2048  # 2^11 slightly smaller chunk due to more columns
            for i in range(0, len(records), chunk_size):
                chunk = records[i:i + chunk_size]
                await db.execute(insert(RegionalEmission).values(chunk))

            await db.commit()
            logger.info(
                f"Successfully seeded {len(records)} regional emission records.")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error seeding regional emissions: {e}")


async def seed_national_energy(db):
    existing = (await db.execute(select(NationalEnergy).limit(1))).scalars().first()
    if existing:
        logger.info("National energy already seeded, skipping.")
        return

    csv_path = project_root / "data" / "energy.csv"
    if not csv_path.exists():
        logger.error(f"National Energy CSV not found at {csv_path}")
        return

    logger.info("Processing National Energy Data...")
    try:
        df = pd.read_csv(csv_path)

        columns_to_keep = {
            'Country': 'country',
            'Energy_type': 'energy_type',
            'Year': 'year',
            'Energy_consumption': 'energy_consumption',
            'CO2_emission': 'co2_emission'
        }

        df = df[list(columns_to_keep.keys())].rename(columns=columns_to_keep)

        df = df.dropna(subset=['country', 'year'])
        df['year'] = df['year'].astype(int)
        df['energy_consumption'] = pd.to_numeric(
            df['energy_consumption'], errors='coerce').fillna(0.0)
        df['co2_emission'] = pd.to_numeric(
            df['co2_emission'], errors='coerce').fillna(0.0)

        records = df.to_dict(orient="records")
        if records:
            # Chunk the inserts to avoid PostgreSQL's 2^15 or 32767 parameter limit
            chunk_size = 4096  # 2^12
            for i in range(0, len(records), chunk_size):
                chunk = records[i:i + chunk_size]
                await db.execute(insert(NationalEnergy).values(chunk))

            await db.commit()
            logger.info(
                f"Successfully seeded {len(records)} national energy records.")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error seeding national energy: {e}")


async def run_all_seeders():
    async with AsyncSessionLocal() as db:
        await seed_companies(db)
        await seed_regional_emissions(db)
        await seed_national_energy(db)

if __name__ == "__main__":
    logger.info("Starting database seed...")
    # Because this is a standard python script (not FastAPI),
    # we have to manually start the async event loop
    asyncio.run(run_all_seeders())
