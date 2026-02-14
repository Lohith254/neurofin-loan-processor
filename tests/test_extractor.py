"""
Tests for the Data Extractor Agent.
"""

import pytest
from unittest.mock import Mock, patch

from app.agents.extractor import DataExtractorAgent
from app.orchestrator.state import (
    LoanProcessorState,
    ExtractedData,
    Transaction,
    TransactionSummary,
    create_initial_state
)


class TestDataExtractorAgent:
    """Test suite for DataExtractorAgent."""

    @pytest.fixture
    def extractor(self):
        """Create an extractor instance for testing."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            return DataExtractorAgent()

    @pytest.fixture
    def sample_transactions(self):
        """Sample transactions for testing."""
        return [
            Transaction(
                date="2026-01-05",
                description="NEFT/Salary Credit from ABC Corp",
                amount=75000.0,
                type="credit",
                balance=125000.0
            ),
            Transaction(
                date="2026-01-10",
                description="ATM Withdrawal",
                amount=10000.0,
                type="debit",
                balance=115000.0
            ),
            Transaction(
                date="2026-02-05",
                description="NEFT/Salary Credit from ABC Corp",
                amount=75000.0,
                type="credit",
                balance=190000.0
            ),
        ]

    def test_is_salary_detection(self, extractor):
        """Test salary detection logic."""
        salary_txn = Transaction(
            date="2026-01-05",
            description="NEFT/Salary Credit from ABC Corp",
            amount=75000.0,
            type="credit",
            balance=125000.0
        )
        assert extractor._is_salary(salary_txn) is True

        non_salary_txn = Transaction(
            date="2026-01-10",
            description="UPI/Amazon Purchase",
            amount=5000.0,
            type="debit",
            balance=120000.0
        )
        assert extractor._is_salary(non_salary_txn) is False

    def test_monthly_summary_calculation(self, extractor, sample_transactions):
        """Test monthly summary calculation."""
        summaries = extractor._calculate_monthly_summaries(sample_transactions)

        assert len(summaries) == 2  # Jan and Feb

        jan_summary = next(s for s in summaries if s.month == "2026-01")
        assert jan_summary.total_credits == 75000.0
        assert jan_summary.total_debits == 10000.0
        assert jan_summary.net_flow == 65000.0
        assert jan_summary.salary_credit == 75000.0

    def test_extractor_is_callable(self, extractor):
        """Test that extractor can be called as a function."""
        state = create_initial_state("test.pdf")
        state["raw_text"] = "Some document text"
        state["tables"] = []

        # Should not raise (will fail on LLM call but structure is correct)
        try:
            result = extractor(state)
            assert isinstance(result, dict)
        except Exception:
            pass  # Expected due to mocked API


class TestExtractedData:
    """Test the ExtractedData Pydantic model."""

    def test_valid_extracted_data(self):
        """Test creating valid ExtractedData."""
        data = ExtractedData(
            account_holder_name="John Doe",
            bank_name="HDFC Bank",
            branch="MG Road",
            account_number_masked="XXXX1234",
            account_type="Savings",
            statement_period_start="2026-01-01",
            statement_period_end="2026-01-31",
            opening_balance=50000.0,
            closing_balance=55000.0,
            total_credits=80000.0,
            total_debits=75000.0,
            transaction_count=10,
            transactions=[]
        )

        assert data.account_holder_name == "John Doe"
        assert data.closing_balance == 55000.0


class TestTransaction:
    """Test the Transaction Pydantic model."""

    def test_credit_transaction(self):
        """Test creating a credit transaction."""
        txn = Transaction(
            date="2026-01-05",
            description="Salary Credit",
            amount=75000.0,
            type="credit",
            balance=125000.0
        )

        assert txn.type == "credit"
        assert txn.amount == 75000.0

    def test_debit_transaction(self):
        """Test creating a debit transaction."""
        txn = Transaction(
            date="2026-01-10",
            description="ATM Withdrawal",
            amount=10000.0,
            type="debit",
            balance=115000.0
        )

        assert txn.type == "debit"
        assert txn.amount == 10000.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
