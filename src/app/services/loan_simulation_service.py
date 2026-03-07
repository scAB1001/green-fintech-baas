# src/app/services/loan_simulation_service.py
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.models.company import Company
from app.models.loan_simulation import LoanSimulation
from app.models.national_energy import NationalEnergy
from app.models.regional_emission import RegionalEmission


class LoanSimulationService:
    # Industry constants based on HBS/Baker McKenzie literature
    BASE_INTEREST_RATE = 8.00
    MAX_GREEN_DISCOUNT = 2.50  # 250 basis points maximum margin ratchet

    # Materiality Weightings (MSCI/Refinitiv framework)
    # Adjusted weightings: Location emissions are more highly weighted for SMEs
    # than national energy grid averages.
    NATIONAL_GRID_WEIGHT = 0.30
    LOCATION_EMISSION_WEIGHT = 0.70

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_quote(self, company_id: int, loan_amount: float,
                             term_months: int) -> LoanSimulation:
        # 1. Fetch the target company
        company = await self.db.get(Company, company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        logger.info(
            f"Starting loan simulation for {company.name} (ID: {company_id})")

        # 2. Fetch Regional Emissions Data (E_loc)
        emissions_query = select(RegionalEmission).where(
            RegionalEmission.local_authority.ilike(f"%{company.location}%")
        )
        emissions_result = await self.db.execute(emissions_query)
        regional_data = emissions_result.scalars().first()

        # Explicitly cast to float to satisfy the strict type checker
        emissions_kt = (
            float(regional_data.grand_total)
            if regional_data and regional_data.grand_total
            else 1500.0
        )

        # Normalize to a 0-100 score (lower emissions = higher score, capping at 5000kt)
        e_loc_score = max(0.0, 100.0 - ((emissions_kt / 5000.0) * 100.0))

        # 3. Fetch National Energy Data (S_nat)
        target_country = "United Kingdom"

        total_energy_query = select(NationalEnergy).where(
            NationalEnergy.country == target_country,
            NationalEnergy.energy_type == "all_energy_types"
        ).order_by(NationalEnergy.year.desc()).limit(1)
        total_energy_result = await self.db.execute(total_energy_query)
        total_energy_data = total_energy_result.scalars().first()

        renew_energy_query = select(NationalEnergy).where(
            NationalEnergy.country == target_country,
            NationalEnergy.energy_type == "renewables_n_other"
        ).order_by(NationalEnergy.year.desc()).limit(1)
        renew_energy_result = await self.db.execute(renew_energy_query)
        renew_energy_data = renew_energy_result.scalars().first()

        # Explicitly cast to float to prevent ColumnElement[bool] evaluation errors
        total_consumption = (
            float(total_energy_data.energy_consumption)
            if total_energy_data and total_energy_data.energy_consumption
            else 0.0
        )
        renew_consumption = (
            float(renew_energy_data.energy_consumption)
            if renew_energy_data and renew_energy_data.energy_consumption
            else 0.0
        )

        if total_consumption > 0:
            s_nat_score = (renew_consumption / total_consumption) * 100.0
        else:
            s_nat_score = 20.0  # Conservative baseline

        # 4. Calculate Environmental Performance Score (EPS)
        eps = float((s_nat_score * self.NATIONAL_GRID_WEIGHT) +
                    (e_loc_score * self.LOCATION_EMISSION_WEIGHT))
        logger.debug(
            f"Calculated EPS: {eps} (Sector: {s_nat_score}, Location: {e_loc_score})")

        # 5. Calculate Margin Ratchet and Final Rate
        discount_applied = (eps / 100.0) * self.MAX_GREEN_DISCOUNT
        final_rate = float(self.BASE_INTEREST_RATE - discount_applied)

        # TODO: Incorporate to DB?
        # 6. Calculate Financials (Simple Interest for the simulation)
        # total_interest = float(
        #     loan_amount * (final_rate / 100.0) * (term_months / 12.0))
        # total_payable = float(loan_amount + total_interest)

        # 7. Persist to Database
        simulation = LoanSimulation(
            company_id=company.id,
            loan_amount=loan_amount,
            term_months=term_months,
            base_rate=self.BASE_INTEREST_RATE,
            applied_rate=round(final_rate, 2),
            esg_score=round(eps, 2),
            estimated_carbon_savings=round(
                (eps / 100) * (loan_amount / 1000), 2)
        )

        self.db.add(simulation)
        await self.db.commit()
        await self.db.refresh(simulation)

        logger.info(
            f"Simulation complete. Applied Rate: {final_rate}%, ESG Score: {eps}")

        return simulation
