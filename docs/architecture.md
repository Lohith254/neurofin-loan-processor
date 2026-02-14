# Architecture Documentation

## System Overview

The Multi-Agent Loan Processor is a GenAI-powered document processing system designed for BFSI operations automation. It uses a modular multi-agent architecture orchestrated by LangGraph.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE                             │
│                        (Streamlit Dashboard)                         │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           ORCHESTRATOR                               │
│                    (LangGraph State Machine)                         │
│                                                                      │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐          │
│  │  START  │───▶│  PARSE  │───▶│CLASSIFY │───▶│  CHECK  │          │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘          │
│                                                     │                │
│                                     ┌───────────────┴───────────────┐│
│                                     ▼                               ▼│
│                              ┌─────────────┐                  ┌─────┐│
│                              │   EXTRACT   │──────────────────│ END ││
│                              └─────────────┘                  └─────┘│
│                                     │                                │
│                                     ▼                                │
│                              ┌─────────────┐                        │
│                              │  VALIDATE   │────────────────────────▶│
│                              └─────────────┘                        │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
            │   AGENT 1   │ │   AGENT 2   │ │   AGENT 3   │
            │ Classifier  │ │  Extractor  │ │  Validator  │
            │             │ │             │ │             │
            │ • Doc type  │ │ • Parse PDF │ │ • RBI rules │
            │ • Quality   │ │ • Extract   │ │ • Risk score│
            │ • Routing   │ │   fields    │ │ • Recommend │
            └─────────────┘ └─────────────┘ └─────────────┘
                    │              │              │
                    └──────────────┼──────────────┘
                                   ▼
            ┌─────────────────────────────────────────────────┐
            │                 SHARED STATE                     │
            │  (LoanProcessorState - TypedDict)               │
            │                                                  │
            │  • file_path          • classification          │
            │  • raw_text           • extracted_data          │
            │  • pages              • monthly_summaries       │
            │  • tables             • risk_assessment         │
            │  • current_agent      • error                   │
            └─────────────────────────────────────────────────┘
```

## Component Details

### 1. User Interface (Streamlit)

**Location**: `app/ui/streamlit_app.py`

The Streamlit interface provides:
- PDF file upload
- Real-time processing status
- Visual results display
- JSON export functionality

### 2. Orchestrator (LangGraph)

**Location**: `app/orchestrator/workflow.py`

The orchestrator coordinates the agent pipeline:

```python
workflow = StateGraph(LoanProcessorState)
workflow.add_node("parse_pdf", parse_pdf_node)
workflow.add_node("classify", classifier_agent)
workflow.add_node("extract", extractor_agent)
workflow.add_node("validate", validator_agent)
```

**Flow Control**:
- Linear progression: parse → classify → extract → validate
- Conditional routing: stops early if document can't proceed
- Error handling: captures and propagates errors through state

### 3. Agent 1: Document Classifier

**Location**: `app/agents/classifier.py`

**Responsibilities**:
- Identify document type (bank_statement, kyc, income_proof, property_doc, other)
- Assess document quality (0-10 score)
- Determine if processing should continue

**Output Schema**:
```python
class ClassificationResult(BaseModel):
    document_type: DocumentType
    quality_score: float  # 0-10
    is_readable: bool
    is_complete: bool
    issues: List[str]
    can_proceed: bool
```

### 4. Agent 2: Data Extractor

**Location**: `app/agents/extractor.py`

**Responsibilities**:
- Extract account information (holder name, bank, account number)
- Parse transaction history
- Calculate monthly summaries

**Output Schema**:
```python
class ExtractedData(BaseModel):
    account_holder_name: str
    bank_name: str
    account_number_masked: str
    statement_period_start: str
    statement_period_end: str
    opening_balance: float
    closing_balance: float
    transactions: List[Transaction]
```

### 5. Agent 3: Validator

**Location**: `app/agents/validator.py`

**Responsibilities**:
- Run compliance checks against RBI guidelines
- Calculate risk score (0-100)
- Generate recommendation (APPROVE/REVIEW/REJECT)

**Output Schema**:
```python
class RiskAssessment(BaseModel):
    risk_score: int  # 0-100
    score_breakdown: dict
    compliance_checks: List[ComplianceCheck]
    issues: List[str]
    red_flags: List[str]
    recommendation: Recommendation
    recommendation_reason: str
```

## Data Flow

```
PDF File
    │
    ▼
┌───────────────────────────────────────┐
│           PDF Parser                   │
│   (PyMuPDF + pdfplumber)              │
│                                        │
│   Input: PDF file path                │
│   Output: raw_text, pages, tables     │
└───────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────┐
│        Classifier Agent               │
│         (Claude LLM)                  │
│                                        │
│   Input: raw_text                     │
│   Output: ClassificationResult        │
└───────────────────────────────────────┘
    │
    ▼ (if can_proceed)
┌───────────────────────────────────────┐
│         Extractor Agent               │
│          (Claude LLM)                 │
│                                        │
│   Input: raw_text, tables             │
│   Output: ExtractedData,              │
│           monthly_summaries           │
└───────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────┐
│         Validator Agent               │
│    (Claude LLM + Compliance Rules)    │
│                                        │
│   Input: extracted_data,              │
│          monthly_summaries            │
│   Output: RiskAssessment              │
└───────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────┐
│        ProcessingResult               │
│                                        │
│   Combined output with:               │
│   - Document info                     │
│   - Extracted data                    │
│   - Risk assessment                   │
│   - Recommendation                    │
└───────────────────────────────────────┘
```

## State Management

The system uses a TypedDict-based state that flows through all agents:

```python
class LoanProcessorState(TypedDict):
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
```

## Compliance Rules

The validator checks these RBI compliance rules:

| Rule | Threshold | Severity |
|------|-----------|----------|
| Minimum Average Balance | ₹10,000 | High |
| Bounced Checks | 0 allowed | High |
| Account Age | 6 months | Medium |
| Large Transactions | Flag > ₹10L | Medium |
| Income Regularity | 80% months | Medium |
| Closing Balance | ₹5,000 | Low |
| Overdraft Instances | Max 2 | Medium |

## Error Handling

Each agent returns errors through the state:

```python
{
    "current_agent": "classifier",
    "error": "Classification failed: API timeout"
}
```

The orchestrator checks for errors after each step and can short-circuit processing.

## Performance Targets

| Metric | Target |
|--------|--------|
| End-to-end processing | < 30 seconds |
| PDF parsing | < 5 seconds |
| Classification | < 10 seconds |
| Extraction | < 10 seconds |
| Validation | < 10 seconds |

## Security Considerations

1. **API Keys**: Stored in `.env`, never committed
2. **File Handling**: Temp files cleaned up after processing
3. **Data Privacy**: No PII stored after processing
4. **Account Numbers**: Always masked (XXXX1234)

## Extensibility

### Adding New Document Types

1. Add to `DocumentType` enum in `state.py`
2. Update classifier prompt with new type
3. Add extraction logic for new document type
4. Add relevant compliance rules

### Adding New Compliance Rules

1. Add rule to `COMPLIANCE_RULES` in `compliance.py`
2. Implement check method in `ComplianceRules` class
3. Update validator prompt to include new rule

### Adding New Agents

1. Create new agent file in `app/agents/`
2. Define output Pydantic model in `state.py`
3. Add node to workflow in `workflow.py`
4. Update state TypedDict with new fields
