# src/app/services/loan_simulation_service.py
"""
Loan Simulation Service Layer.

This service orchestrates the ESG benchmarking process. It aggregates regional
emissions data and national energy grid metrics to calculate a Environmental
Performance Score (EPS), which directly influences the loan's interest rate
via a margin ratchet mechanism.
"""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.models.company import Company
from app.models.loan_simulation import LoanSimulation
from app.models.national_energy import NationalEnergy
from app.models.regional_emission import RegionalEmission


class LoanSimulationService:
    """
    Handles the logic for generating ESG-linked loan quotes.

    The service follows industry-standard frameworks (MSCI/Refinitiv) to
    benchmark a company's operating environment against national averages.
    """

    # Industry constants based on HBS/Baker McKenzie literature
    BASE_INTEREST_RATE = 8.00    # Default APR for the simulation
    MAX_GREEN_DISCOUNT = 2.50    # Maximum 250 basis points (bps) reduction

    # Materiality Weightings: We prioritize the local authority's footprint
    # (Location) over the national grid mix (National) to reflect SME impact.
    NATIONAL_GRID_WEIGHT = 0.30
    LOCATION_EMISSION_WEIGHT = 0.70

    def __init__(self, db: AsyncSession):
        """
        Initializes the service with an asynchronous database session.
        """
        self.db = db

    @staticmethod
    def calculate_green_rate(
        emissions_kt: float,
        total_consumption: float,
        renew_consumption: float,
        base_rate: float,
        max_discount: float,
    ) -> tuple[float, float]:
        """
        Pure function for mathematical ESG rate calculation.

        This logic is decoupled from IO to allow for easy unit testing
        and deterministic simulation results.

        Formula:
            $$EPS = (S_{nat} \times 0.30) + (E_{loc} \times 0.70)$$
            $$Rate = Base - (\frac{EPS}{100} \times MaxDiscount)$$

        Returns:
            tuple: (Environmental Performance Score, Final Interest Rate)
        """

        # 1. Location Score (E_loc)
        # Higher emissions in a local authority lower the score.
        # Scaled against a benchmark of 5000 ktCO2.
        e_loc_score = max(0.0, 100.0 - ((emissions_kt / 5000.0) * 100.0))

        # 2. National Score (S_nat)
        # Represents the percentage of renewables in the national energy mix.
        if total_consumption > 0:
            s_nat_score = (renew_consumption / total_consumption) * 100.0
        else:
            s_nat_score = 20.0  # Default baseline if data is missing

        # 3. Calculate Weighted EPS
        eps = float((s_nat_score * 0.30) + (e_loc_score * 0.70))

        # 4. Final Rate Calculation (Margin Ratchet)
        # The discount is proportional to the EPS.
        discount_applied = (eps / 100.0) * max_discount
        final_rate = float(base_rate - discount_applied)

        return round(eps, 2), round(final_rate, 2)

    async def generate_quote(
        self, company_id: int, loan_amount: float, term_months: int
    ) -> LoanSimulation:
        """
        Aggregates data and persists a new loan simulation record.

        Steps:
            1. Validate company existence.
            2. Fetch latest regional emission totals for the company's locality.
            3. Fetch latest UK national energy grid statistics.
            4. Compute interest rate using the margin ratchet formula.
            5. Persist simulation for audit trails and reporting.
        """
        # 1. Fetch Target Entity
        company = await self.db.get(Company, company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
            )
        logger.info(
            f"Starting loan simulation for {company.name} (ID: {company_id})")

        # 2. Fetch Regional Emissions Data (E_loc)
        # Uses ILIKE to handle minor variations in Local Authority naming conventions.
        emissions_query = select(RegionalEmission).where(
            RegionalEmission.local_authority.ilike(f"%{company.location}%")
        )
        emissions_result = await self.db.execute(emissions_query)
        regional_data = emissions_result.scalars().first()

        emissions_kt = (
            float(regional_data.grand_total)
            if regional_data and regional_data.grand_total
            else 1500.0  # Fallback to UK average if region is not found
        )

        # 3. Fetch National Energy Data (S_nat)
        target_country = "United Kingdom"

        # Query latest 'Total' energy consumption record
        total_energy_query = (
            select(NationalEnergy)
            .where(
                NationalEnergy.country == target_country,
                NationalEnergy.energy_type == "all_energy_types",
            )
            .order_by(NationalEnergy.year.desc())
            .limit(1)
        )
        total_energy_result = await self.db.execute(total_energy_query)
        total_energy_data = total_energy_result.scalars().first()

        # Query latest 'Renewable' energy consumption record
        renew_energy_query = (
            select(NationalEnergy)
            .where(
                NationalEnergy.country == target_country,
                NationalEnergy.energy_type == "renewables_n_other",
            )
            .order_by(NationalEnergy.year.desc())
            .limit(1)
        )
        renew_energy_result = await self.db.execute(renew_energy_query)
        renew_energy_data = renew_energy_result.scalars().first()

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

        # 4. Compute ESG Score and Interest Rate
        eps, final_rate = self.calculate_green_rate(
            emissions_kt=emissions_kt,
            total_consumption=total_consumption,
            renew_consumption=renew_consumption,
            base_rate=self.BASE_INTEREST_RATE,
            max_discount=self.MAX_GREEN_DISCOUNT,
        )

        logger.debug(f"Calculated EPS: {eps}, Final Rate: {final_rate}%")

        # 5. Persistence
        # We also calculate a projected carbon saving based on the capital
        # deployed and the company's performance score.
        simulation = LoanSimulation(
            company_id=company.id,
            loan_amount=loan_amount,
            term_months=term_months,
            base_rate=self.BASE_INTEREST_RATE,
            applied_rate=final_rate,
            esg_score=eps,
            estimated_carbon_savings=round(
                (eps / 100) * (loan_amount / 1000), 2),
        )

        self.db.add(simulation)
        await self.db.commit()
        await self.db.refresh(simulation)

        logger.info(
            f"Simulation complete. Applied Rate: {final_rate}%, ESG Score: {eps}"
        )

        return simulation
