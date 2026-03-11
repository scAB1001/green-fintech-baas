# tests/unit/pdf_service_test.py
import pytest

from app.models.company import Company
from app.models.loan_simulation import LoanSimulation
from app.services.pdf_service import PDFService


@pytest.mark.unit
def test_generate_loan_quote_pdf_success():
    """Verify the PDF canvas compiles memory bytes without crashing."""

    # 1. Mock the SQLAlchemy models purely in memory
    mock_company = Company(
        id=1,
        name="Test Corp",
        companies_house_id="12345678",
        business_sector="Tech",
        location="London",
    )

    mock_simulation = LoanSimulation(
        id=1,
        company_id=1,
        loan_amount=500000.0,
        term_months=60,
        base_rate=8.0,
        applied_rate=5.5,
        esg_score=90.0,
        estimated_carbon_savings=15.0,
    )

    # 2. Execute the service
    pdf_bytes = PDFService.generate_loan_quote_pdf(mock_company, mock_simulation)

    # 3. Verify valid PDF structure
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000  # Ensure the buffer actually wrote data
    assert pdf_bytes.startswith(b"%PDF-")  # Standard PDF file signature
    assert b"%%EOF" in pdf_bytes  # Standard PDF End-Of-File marker
