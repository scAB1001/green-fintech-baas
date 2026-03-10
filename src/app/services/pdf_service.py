# src/app/services/pdf_service.py
"""
PDF Generation Service.

This module handles the synthesis of financial data and ESG scores into a
branded, professional PDF quote. It utilizes the ReportLab library to
construct documents in memory using a byte stream, ensuring no temporary
files are stored on the server's filesystem.
"""

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.models.company import Company
from app.models.loan_simulation import LoanSimulation


class PDFService:
    """
    Service responsible for generating customer-facing PDF documentation.
    """

    @staticmethod
    def generate_loan_quote_pdf(company: Company, simulation: LoanSimulation) -> bytes:
        """
        Generates a professional Sustainability-Linked Loan quote.

        The PDF includes:
        - Corporate branding and timestamping.
        - Applicant metadata (Sector/Location).
        - Financial terms (Principal/Base Rate).
        - ESG Metrics (Environmental Score/Carbon Savings).
        - The final 'Green' interest rate offer.

        Args:
            company (Company): The company entity associated with the quote.
            simulation (LoanSimulation): The calculated results of the simulation.

        Returns:
            bytes: The PDF document as a binary stream.
        """
        buffer = io.BytesIO()

        # Initialize canvas using industry-standard A4 dimensions
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # --- Header Configuration ---
        # A dark green aesthetic represents the 'Green FinTech' identity.
        c.setFillColor(colors.HexColor("#0f5132"))  # Dark Green
        c.rect(0, height - 80, width, 80, fill=1, stroke=0)

        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 24)
        c.drawString(40, height - 50, "Green FinTech BaaS")

        c.setFont("Helvetica", 12)
        c.drawString(
            width - 200, height -
            45, f"Date: {datetime.now().strftime('%Y-%m-%d')}"
        )

        # --- Document Title ---
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(40, height - 130, "Sustainability-Linked Loan Simulation")

        # --- Company Details Section ---
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, height - 170, "Applicant Details")

        c.setFont("Helvetica", 12)
        c.drawString(40, height - 195, f"Company Name: {company.name}")
        c.drawString(40, height - 215,
                     f"Registration No: {company.companies_house_id}")
        c.drawString(40, height - 235, f"Sector: {company.business_sector}")
        c.drawString(40, height - 255, f"Location: {company.location}")

        # --- Loan Details Section ---
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, height - 305, "Financial Simulation")

        c.setFont("Helvetica", 12)
        c.drawString(
            40, height -
            330, f"Requested Amount: £{simulation.loan_amount:,.2f}"
        )
        c.drawString(40, height - 350,
                     f"Term: {simulation.term_months} months")
        c.drawString(
            40, height -
            370, f"Standard Base Rate: {simulation.base_rate:.2f}%"
        )

        # --- Green Metrics Section ---
        # Highlights the ESG performance assessment that drives the margin ratchet.
        c.setFillColor(colors.HexColor("#198754"))  # Success Green
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, height - 420, "ESG Performance Assessment")

        c.setFont("Helvetica", 12)
        c.drawString(
            40,
            height - 445,
            f"Calculated Environmental Score: {simulation.esg_score:.2f} / 100",
        )
        c.drawString(
            40,
            height - 465,
            f"Estimated Carbon Savings: \
                {simulation.estimated_carbon_savings:.2f} tonnes CO2e",
        )

        # --- Final Offer Section ---
        # A highlighted box for the final rate offer, improving readability.
        c.setStrokeColor(colors.HexColor("#0f5132"))
        c.rect(40, height - 550, width - 80, 50, fill=0, stroke=1)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(
            55,
            height - 530,
            f"Approved Green Interest Rate: {simulation.applied_rate:.2f}%",
        )

        # --- Footer ---
        c.setFillColor(colors.gray)
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(
            40,
            50,
            "Generated dynamically based on UK regional emissions and \
                national energy datasets.",
        )

        # Finalize and return bytes for streaming via FastAPI's Response object
        c.save()
        buffer.seek(0)
        return buffer.getvalue()
