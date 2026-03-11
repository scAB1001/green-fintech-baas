# src/app/services/loan_simulation_service.py
"""
Loan Simulation Service Layer.

This service orchestrates the ESG benchmarking process. It aggregates regional
emissions data, national energy grid metrics, and specific company ESG metrics
to calculate an Environmental Performance Score (EPS). This EPS directly
influences the loan's interest rate via a margin ratchet mechanism.
"""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.models.company import Company
from app.models.environmental_metric import EnvironmentalMetric
from app.models.loan_simulation import LoanSimulation
from app.models.national_energy import NationalEnergy
from app.models.regional_emission import RegionalEmission


class LoanSimulationService:
    """
    Handles the logic for generating ESG-linked loan quotes.

    The service follows industry-standard frameworks (MSCI/Refinitiv) to
    benchmark a company's operating environment against national averages,
    while heavily prioritizing the company's actual operational emissions
    if that data is available in the system.
    """

    BASE_INTEREST_RATE = 8.00
    MAX_GREEN_DISCOUNT = 2.50

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def calculate_green_rate(
        emissions_kt: float,
        total_consumption: float,
        renew_consumption: float,
        base_rate: float,
        max_discount: float,
        company_emissions_tco2e: float | None = None,
    ) -> tuple[float, float]:
        """
        Pure function for mathematical ESG rate calculation.

        This logic is decoupled from IO to allow deterministic unit testing.
        If company-specific data is absent, it relies heavily on regional data.
        If company data is present, the weightings shift to prioritize actuals.

        Formulas:
        Fallback (Proxy Data):
        $$EPS = (S_{nat} \cdot 0.30) + (E_{loc} \cdot 0.70)$$

        Actual (Company Data Present):
        $$
            EPS = (S_{nat} \cdot 0.30) + (E_{loc} \cdot 0.20) + (C_{score} \cdot 0.50)
        $$

        Returns:
            tuple: (Environmental Performance Score, Final Interest Rate)
        """

        # 1. Location Score (E_loc) -> Baseline of 5000 ktCO2
        e_loc_score = max(0.0, 100.0 - ((emissions_kt / 5000.0) * 100.0))

        # 2. National Score (S_nat)
        if total_consumption > 0:
            s_nat_score = (renew_consumption / total_consumption) * 100.0
        else:
            s_nat_score = 20.0

        # 3. Company Specific Score (C_score) & Dynamic EPS Calculation
        if company_emissions_tco2e is not None:
            # Assume 500 tCO2e is a benchmark threshold for an average SME
            c_score = max(
                0.0, 100.0 - ((company_emissions_tco2e / 500.0) * 100.0))
            eps = float((s_nat_score * 0.30) +
                        (e_loc_score * 0.20) + (c_score * 0.50))
        else:
            # Fallback to pure proxy baseline
            eps = float((s_nat_score * 0.30) + (e_loc_score * 0.70))

        # 4. Final Rate Calculation (Margin Ratchet)
        discount_applied = (eps / 100.0) * max_discount
        final_rate = float(base_rate - discount_applied)

        return round(eps, 2), round(final_rate, 2)

    async def generate_quote(
        self, company_id: int, loan_amount: float, term_months: int
    ) -> LoanSimulation:
        """
        Aggregates data and persists a new loan simulation record.
        """
        company = await self.db.get(Company, company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
            )
        logger.info(
            f"Starting loan simulation for {company.name} (ID: {company_id})")

        # Fetch Company Specific Metrics (C_score data)
        metric_query = (
            select(EnvironmentalMetric)
            .where(EnvironmentalMetric.company_id == company_id)
            .order_by(EnvironmentalMetric.reporting_year.desc())
            .limit(1)
        )
        metric_result = await self.db.execute(metric_query)
        latest_metric = metric_result.scalars().first()

        company_emissions_tco2e = (
            latest_metric.carbon_emissions_tco2e
            if latest_metric
            else None
        )

        # Fetch Regional Emissions Data (E_loc)
        emissions_query = select(RegionalEmission).where(
            RegionalEmission.local_authority.ilike(f"%{company.location}%")
        )
        emissions_result = await self.db.execute(emissions_query)
        regional_data = emissions_result.scalars().first()

        emissions_kt = (
            float(regional_data.grand_total)
            if regional_data and regional_data.grand_total
            else 1500.0
        )

        # Fetch National Energy Data (S_nat)
        target_country = "United Kingdom"
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

        # Compute ESG Score and Interest Rate
        eps, final_rate = self.calculate_green_rate(
            emissions_kt=emissions_kt,
            total_consumption=total_consumption,
            renew_consumption=renew_consumption,
            base_rate=self.BASE_INTEREST_RATE,
            max_discount=self.MAX_GREEN_DISCOUNT,
            company_emissions_tco2e=company_emissions_tco2e,
        )

        logger.debug(f"Calculated EPS: {eps}, Final Rate: {final_rate}%")

        # Refined Carbon Savings Logic:
        # If we have real emissions data, calculate a proportional 10% reduction proxy.
        # Otherwise, we use the generalized capital deployment proxy.
        if company_emissions_tco2e:
            est_savings = company_emissions_tco2e * (eps / 100.0) * 0.10
        else:
            est_savings = (eps / 100) * (loan_amount / 1000)

        simulation = LoanSimulation(
            company_id=company.id,
            loan_amount=loan_amount,
            term_months=term_months,
            base_rate=self.BASE_INTEREST_RATE,
            applied_rate=final_rate,
            esg_score=eps,
            estimated_carbon_savings=round(est_savings, 2),
        )

        self.db.add(simulation)
        await self.db.commit()
        await self.db.refresh(simulation)

        logger.info(
            f"Simulation complete. Applied Rate: {final_rate}%, ESG Score: {eps}")

        return simulation
