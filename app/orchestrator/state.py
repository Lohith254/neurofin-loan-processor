"""
State definitions for the Multi-Agent Loan Processor.
These TypedDicts and Pydantic models define the data flowing through the pipeline.
"""

from typing import TypedDict, List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import date
from enum import Enum


# =============================================================================
# Enums
# =============================================================================

class DocumentType(str, Enum):
    BANK_STATEMENT = "bank_statement"
    KYC = "kyc"
    INCOME_PROOF = "income_proof"
    PROPERTY_DOC = "property_doc"
    OTHER = "other"


class Recommendation(str, Enum):
    APPROVE = "APPROVE"
    REVIEW = "REVIEW"
    REJECT = "REJECT"


# =============================================================================
# Pydantic Models (for structured LLM outputs)
# =============================================================================

class ClassificationResult(BaseModel):
    """Output from the Document Classifier Agent."""
    document_type: DocumentType = Field(description="Type of document detected")
    quality_score: float = Field(ge=0, le=10, description="Document quality score 0-10")
    is_readable: bool = Field(description="Whether the document is readable")
    is_complete: bool = Field(description="Whether the document appears complete")
    issues: List[str] = Field(default_factory=list, description="List of issues found")
    can_proceed: bool = Field(description="Whether processing can continue")


class Transaction(BaseModel):
    """Single transaction from bank statement."""
    date: str = Field(description="Transaction date")
    description: str = Field(description="Transaction description")
    amount: float = Field(description="Transaction amount")
    type: Literal["credit", "debit"] = Field(description="Credit or debit")
    balance: Optional[float] = Field(None, description="Running balance after transaction")


class ExtractedData(BaseModel):
    """Output from the Data Extractor Agent."""
    account_holder_name: str = Field(description="Name of account holder")
    bank_name: str = Field(description="Name of the bank")
    branch: Optional[str] = Field(None, description="Branch name/code")
    account_number_masked: str = Field(description="Masked account number (e.g., XXXX1234)")
    account_type: Optional[str] = Field(None, description="Savings/Current/etc.")
    statement_period_start: str = Field(description="Statement start date")
    statement_period_end: str = Field(description="Statement end date")
    opening_balance: float = Field(description="Opening balance")
    closing_balance: float = Field(description="Closing balance")
    total_credits: float = Field(description="Total credit amount")
    total_debits: float = Field(description="Total debit amount")
    transaction_count: int = Field(description="Number of transactions")
    transactions: List[Transaction] = Field(default_factory=list, description="List of transactions")


class TransactionSummary(BaseModel):
    """Monthly transaction summary."""
    month: str = Field(description="Month (YYYY-MM)")
    total_credits: float = Field(description="Total credits for month")
    total_debits: float = Field(description="Total debits for month")
    net_flow: float = Field(description="Net cash flow")
    avg_balance: float = Field(description="Average balance")
    salary_credit: Optional[float] = Field(None, description="Identified salary credit")


class ComplianceCheck(BaseModel):
    """Single compliance rule check result."""
    rule_name: str = Field(description="Name of the rule")
    rule_description: str = Field(description="What the rule checks")
    passed: bool = Field(description="Whether the check passed")
    actual_value: str = Field(description="Actual value found")
    threshold: str = Field(description="Required threshold")
    severity: Literal["high", "medium", "low"] = Field(description="Severity if failed")


class RiskAssessment(BaseModel):
    """Output from the Validator Agent."""
    risk_score: int = Field(ge=0, le=100, description="Overall risk score 0-100")
    score_breakdown: dict = Field(description="Score breakdown by category")
    compliance_checks: List[ComplianceCheck] = Field(description="Individual compliance checks")
    issues: List[str] = Field(default_factory=list, description="List of issues found")
    red_flags: List[str] = Field(default_factory=list, description="Serious concerns")
    recommendation: Recommendation = Field(description="Final recommendation")
    recommendation_reason: str = Field(description="Explanation for recommendation")


# =============================================================================
# LangGraph State (TypedDict for graph state)
# =============================================================================

class LoanProcessorState(TypedDict):
    """
    Main state object that flows through the LangGraph pipeline.
    Each agent reads from and writes to this state.
    """
    # Input
    file_path: str

    # PDF Parsing
    raw_text: str
    pages: List[str]
    tables: List[dict]

    # Agent 1: Classifier
    classification: Optional[ClassificationResult]

    # Agent 2: Extractor
    extracted_data: Optional[ExtractedData]
    monthly_summaries: List[TransactionSummary]

    # Agent 3: Validator
    risk_assessment: Optional[RiskAssessment]

    # Pipeline metadata
    current_agent: str
    processing_time_ms: int
    error: Optional[str]
    completed: bool


# =============================================================================
# Final Output Model
# =============================================================================

class ProcessingResult(BaseModel):
    """Final output returned to the user."""
    success: bool = Field(description="Whether processing completed successfully")

    # Document info
    document_type: DocumentType
    quality_score: float

    # Extracted data
    extracted_data: Optional[ExtractedData]
    monthly_summaries: List[TransactionSummary]

    # Risk assessment
    risk_score: int
    recommendation: Recommendation
    compliance_issues: List[str]
    red_flags: List[str]

    # Metadata
    processing_time_seconds: float
    error_message: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "document_type": "bank_statement",
                "quality_score": 8.5,
                "risk_score": 75,
                "recommendation": "APPROVE",
                "compliance_issues": [],
                "red_flags": [],
                "processing_time_seconds": 12.5
            }
        }


# =============================================================================
# Helper Functions
# =============================================================================

def create_initial_state(file_path: str) -> LoanProcessorState:
    """Create initial state for a new processing job."""
    return LoanProcessorState(
        file_path=file_path,
        raw_text="",
        pages=[],
        tables=[],
        classification=None,
        extracted_data=None,
        monthly_summaries=[],
        risk_assessment=None,
        current_agent="",
        processing_time_ms=0,
        error=None,
        completed=False
    )
