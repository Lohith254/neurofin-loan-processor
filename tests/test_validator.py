"""
Tests for the Validator Agent.
"""

import pytest
from unittest.mock import Mock, patch

from app.agents.validator import ValidatorAgent
from app.orchestrator.state import (
    LoanProcessorState,
    RiskAssessment,
    ComplianceCheck,
    Recommendation,
    ExtractedData,
    Transaction,
    TransactionSummary,
    create_initial_state
)
from app.rules.compliance import ComplianceRules, COMPLIANCE_RULES


class TestValidatorAgent:
    """Test suite for ValidatorAgent."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance for testing."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            return ValidatorAgent()

    @pytest.fixture
    def sample_extracted_data(self):
        """Sample extracted data for testing."""
        return ExtractedData(
            account_holder_name="John Doe",
            bank_name="HDFC Bank",
            branch="MG Road",
            account_number_masked="XXXX1234",
            account_type="Savings",
            statement_period_start="2026-01-01",
            statement_period_end="2026-06-30",
            opening_balance=50000.0,
            closing_balance=55000.0,
            total_credits=450000.0,
            total_debits=445000.0,
            transaction_count=60,
            transactions=[
                Transaction(
                    date="2026-01-05",
                    description="NEFT/Salary Credit",
                    amount=75000.0,
                    type="credit",
                    balance=125000.0
                )
            ]
        )

    @pytest.fixture
    def sample_monthly_summaries(self):
        """Sample monthly summaries for testing."""
        return [
            TransactionSummary(
                month="2026-01",
                total_credits=75000.0,
                total_debits=70000.0,
                net_flow=5000.0,
                avg_balance=50000.0,
                salary_credit=75000.0
            ),
            TransactionSummary(
                month="2026-02",
                total_credits=75000.0,
                total_debits=72000.0,
                net_flow=3000.0,
                avg_balance=52000.0,
                salary_credit=75000.0
            ),
        ]

    def test_validate_no_data(self, validator):
        """Test validation with no extracted data."""
        state = create_initial_state("test.pdf")
        state["extracted_data"] = None

        result = validator.validate(state)

        assert result["risk_assessment"].risk_score == 100
        assert result["risk_assessment"].recommendation == Recommendation.REJECT

    def test_validator_is_callable(self, validator):
        """Test that validator can be called as a function."""
        state = create_initial_state("test.pdf")
        state["extracted_data"] = None
        state["monthly_summaries"] = []

        result = validator(state)
        assert isinstance(result, dict)
        assert "risk_assessment" in result


class TestComplianceRules:
    """Test the ComplianceRules engine."""

    @pytest.fixture
    def compliance(self):
        """Create a compliance rules instance."""
        return ComplianceRules()

    @pytest.fixture
    def good_extracted_data(self):
        """Data that passes all compliance checks."""
        return ExtractedData(
            account_holder_name="John Doe",
            bank_name="HDFC Bank",
            branch="MG Road",
            account_number_masked="XXXX1234",
            account_type="Savings",
            statement_period_start="2026-01-01",
            statement_period_end="2026-06-30",
            opening_balance=50000.0,
            closing_balance=55000.0,
            total_credits=450000.0,
            total_debits=445000.0,
            transaction_count=60,
            transactions=[]
        )

    @pytest.fixture
    def good_monthly_summaries(self):
        """Monthly summaries that pass compliance."""
        return [
            TransactionSummary(
                month=f"2026-0{i}",
                total_credits=75000.0,
                total_debits=70000.0,
                net_flow=5000.0,
                avg_balance=50000.0,
                salary_credit=75000.0
            )
            for i in range(1, 7)  # 6 months
        ]

    def test_min_avg_balance_pass(self, compliance, good_monthly_summaries):
        """Test minimum average balance check passes."""
        result = compliance._check_min_avg_balance(good_monthly_summaries)

        assert result.rule_name == "min_avg_balance"
        assert result.passed is True

    def test_min_avg_balance_fail(self, compliance):
        """Test minimum average balance check fails with low balance."""
        low_balance_summaries = [
            TransactionSummary(
                month="2026-01",
                total_credits=5000.0,
                total_debits=4000.0,
                net_flow=1000.0,
                avg_balance=5000.0,  # Below ₹10,000 threshold
                salary_credit=None
            )
        ]

        result = compliance._check_min_avg_balance(low_balance_summaries)

        assert result.passed is False
        assert result.severity == "high"

    def test_bounce_check_pass(self, compliance, good_extracted_data):
        """Test bounce check passes with no bounced transactions."""
        result = compliance._check_bounce_count(good_extracted_data)

        assert result.rule_name == "max_bounce_count"
        assert result.passed is True

    def test_bounce_check_fail(self, compliance):
        """Test bounce check fails with bounced transaction."""
        data_with_bounce = ExtractedData(
            account_holder_name="John Doe",
            bank_name="HDFC Bank",
            account_number_masked="XXXX1234",
            statement_period_start="2026-01-01",
            statement_period_end="2026-01-31",
            opening_balance=50000.0,
            closing_balance=45000.0,
            total_credits=0.0,
            total_debits=5000.0,
            transaction_count=1,
            transactions=[
                Transaction(
                    date="2026-01-15",
                    description="CHEQUE BOUNCE - Insufficient Funds",
                    amount=5000.0,
                    type="debit",
                    balance=45000.0
                )
            ]
        )

        result = compliance._check_bounce_count(data_with_bounce)

        assert result.passed is False
        assert result.severity == "high"

    def test_account_age_pass(self, compliance, good_monthly_summaries):
        """Test account age check passes with 6+ months history."""
        result = compliance._check_account_age(good_monthly_summaries)

        assert result.passed is True

    def test_account_age_fail(self, compliance):
        """Test account age check fails with insufficient history."""
        short_history = [
            TransactionSummary(
                month="2026-01",
                total_credits=75000.0,
                total_debits=70000.0,
                net_flow=5000.0,
                avg_balance=50000.0,
                salary_credit=75000.0
            )
        ]  # Only 1 month

        result = compliance._check_account_age(short_history)

        assert result.passed is False

    def test_run_all_checks(
        self,
        compliance,
        good_extracted_data,
        good_monthly_summaries
    ):
        """Test running all compliance checks."""
        results = compliance.run_all_checks(
            good_extracted_data,
            good_monthly_summaries
        )

        assert len(results) == 7  # All 7 rules
        assert all(isinstance(r, ComplianceCheck) for r in results)


class TestRiskAssessment:
    """Test the RiskAssessment Pydantic model."""

    def test_valid_risk_assessment(self):
        """Test creating a valid RiskAssessment."""
        assessment = RiskAssessment(
            risk_score=25,
            score_breakdown={
                "balance_stability": 20,
                "income_regularity": 25,
                "transaction_patterns": 20,
                "red_flags": 0
            },
            compliance_checks=[],
            issues=[],
            red_flags=[],
            recommendation=Recommendation.APPROVE,
            recommendation_reason="All checks passed with good financial health"
        )

        assert assessment.risk_score == 25
        assert assessment.recommendation == Recommendation.APPROVE

    def test_risk_score_validation(self):
        """Test that risk score must be between 0 and 100."""
        with pytest.raises(ValueError):
            RiskAssessment(
                risk_score=150,  # Invalid
                score_breakdown={},
                compliance_checks=[],
                issues=[],
                red_flags=[],
                recommendation=Recommendation.REJECT,
                recommendation_reason="Test"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
