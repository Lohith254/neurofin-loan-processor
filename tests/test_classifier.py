"""
Tests for the Document Classifier Agent.
"""

import pytest
from unittest.mock import Mock, patch

from app.agents.classifier import DocumentClassifierAgent
from app.orchestrator.state import (
    LoanProcessorState,
    ClassificationResult,
    DocumentType,
    create_initial_state
)


class TestDocumentClassifierAgent:
    """Test suite for DocumentClassifierAgent."""

    @pytest.fixture
    def classifier(self):
        """Create a classifier instance for testing."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            return DocumentClassifierAgent()

    @pytest.fixture
    def sample_bank_statement_text(self):
        """Sample bank statement text for testing."""
        return """
        HDFC BANK
        Statement of Account

        Account Holder: John Doe
        Account Number: XXXX1234
        Statement Period: 01-Jan-2026 to 31-Jan-2026

        Opening Balance: ₹50,000.00
        Closing Balance: ₹55,000.00

        Date        Description             Debit       Credit      Balance
        01-Jan-26   Opening Balance                                 50,000.00
        05-Jan-26   NEFT/Salary Credit                  75,000.00   125,000.00
        10-Jan-26   ATM Withdrawal         10,000.00               115,000.00
        15-Jan-26   UPI/Amazon             5,000.00                110,000.00
        20-Jan-26   Rent Payment           50,000.00               60,000.00
        25-Jan-26   Interest Credit                     200.00     60,200.00
        """

    def test_classify_empty_document(self, classifier):
        """Test classification of empty document."""
        state = create_initial_state("test.pdf")
        state["raw_text"] = ""

        result = classifier.classify(state)

        assert result["error"] is not None
        assert result["classification"].can_proceed is False
        assert result["classification"].quality_score == 0.0

    def test_classify_returns_correct_structure(self, classifier):
        """Test that classification returns correct state structure."""
        state = create_initial_state("test.pdf")
        state["raw_text"] = "Some document text"

        with patch.object(classifier, 'structured_llm') as mock_llm:
            mock_result = ClassificationResult(
                document_type=DocumentType.BANK_STATEMENT,
                quality_score=8.5,
                is_readable=True,
                is_complete=True,
                issues=[],
                can_proceed=True
            )
            mock_llm.invoke.return_value = mock_result

            result = classifier.classify(state)
            assert "classification" in result
            assert result["current_agent"] == "classifier"

    def test_classifier_is_callable(self, classifier):
        """Test that classifier can be called as a function."""
        state = create_initial_state("test.pdf")
        state["raw_text"] = ""

        # Should not raise
        result = classifier(state)
        assert isinstance(result, dict)


class TestClassificationResult:
    """Test the ClassificationResult Pydantic model."""

    def test_valid_classification_result(self):
        """Test creating a valid ClassificationResult."""
        result = ClassificationResult(
            document_type=DocumentType.BANK_STATEMENT,
            quality_score=8.5,
            is_readable=True,
            is_complete=True,
            issues=[],
            can_proceed=True
        )

        assert result.document_type == DocumentType.BANK_STATEMENT
        assert result.quality_score == 8.5
        assert result.can_proceed is True

    def test_quality_score_validation(self):
        """Test that quality score must be between 0 and 10."""
        with pytest.raises(ValueError):
            ClassificationResult(
                document_type=DocumentType.BANK_STATEMENT,
                quality_score=15,  # Invalid: > 10
                is_readable=True,
                is_complete=True,
                issues=[],
                can_proceed=True
            )

    def test_document_type_enum(self):
        """Test all document type enum values."""
        assert DocumentType.BANK_STATEMENT.value == "bank_statement"
        assert DocumentType.KYC.value == "kyc"
        assert DocumentType.INCOME_PROOF.value == "income_proof"
        assert DocumentType.PROPERTY_DOC.value == "property_doc"
        assert DocumentType.OTHER.value == "other"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
