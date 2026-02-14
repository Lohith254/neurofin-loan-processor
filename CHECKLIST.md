# Implementation Checklist - Multi-Agent Loan Processor

> Weekend Build: February 15-16, 2026
> Goal: Impress Neurofin with CTO-level technical demonstration

---

## Pre-Build Preparation (Friday Evening)

### Environment Setup
- [ ] Create GitHub repository: `neurofin-loan-processor`
- [ ] Set up Python 3.11+ virtual environment
- [ ] Get API keys ready:
  - [ ] Anthropic Claude API key
  - [ ] (Optional) LangSmith API key for tracing
- [ ] Download 2-3 sample bank statement PDFs for testing
- [ ] Install VS Code extensions (Python, Pylance)

### Dependencies to Install
```bash
pip install langchain langgraph anthropic
pip install pymupdf pdfplumber
pip install streamlit
pip install python-dotenv pydantic
pip install chromadb  # optional
```

---

## Day 1: Saturday - Foundation (8 hours)

### Morning Session (9 AM - 12 PM) - Project Setup + Agent 1

#### Hour 1-2: Project Structure
- [ ] Create folder structure:
  ```
  mkdir -p app/{agents,orchestrator,parsers,rules,ui}
  mkdir -p data/sample_statements tests docs
  ```
- [ ] Create `__init__.py` files in all packages
- [ ] Create `requirements.txt`:
  ```
  langchain>=0.1.0
  langgraph>=0.0.20
  anthropic>=0.18.0
  pymupdf>=1.23.0
  pdfplumber>=0.10.0
  streamlit>=1.31.0
  python-dotenv>=1.0.0
  pydantic>=2.5.0
  ```
- [ ] Create `.env.example` file
- [ ] Create `.gitignore` file

#### Hour 2-3: State Definitions
- [ ] Create `app/orchestrator/state.py`:
  ```python
  from typing import TypedDict, List, Optional
  from pydantic import BaseModel

  class DocumentState(TypedDict):
      file_path: str
      raw_text: str
      document_type: str
      quality_score: float
      can_proceed: bool
      extracted_data: dict
      transactions: list
      risk_score: int
      compliance_issues: list
      recommendation: str
      error: Optional[str]
  ```
- [ ] Define Pydantic models for structured outputs

#### Hour 3-4: Agent 1 - Document Classifier
- [ ] Create `app/agents/classifier.py`
- [ ] Implement classification logic:
  - [ ] Document type detection (bank_statement, kyc, income_proof, other)
  - [ ] Quality score calculation (1-10)
  - [ ] Readability check
  - [ ] Completeness validation
- [ ] Create classifier prompt template
- [ ] Test with sample PDF
- [ ] **Checkpoint: Classifier returns correct document type**

### Afternoon Session (1 PM - 5 PM) - Agent 2

#### Hour 5-6: PDF Parser
- [ ] Create `app/parsers/pdf_parser.py`
- [ ] Implement PDF text extraction with PyMuPDF
- [ ] Implement table extraction with pdfplumber
- [ ] Handle multi-page documents
- [ ] Error handling for corrupted PDFs
- [ ] Test with sample bank statement

#### Hour 7-8: Agent 2 - Data Extractor
- [ ] Create `app/agents/extractor.py`
- [ ] Implement field extraction:
  - [ ] Account holder name
  - [ ] Bank name and branch
  - [ ] Account number (masked)
  - [ ] Statement period (start/end dates)
  - [ ] Opening balance
  - [ ] Closing balance
  - [ ] Total credits
  - [ ] Total debits
- [ ] Implement transaction parsing:
  - [ ] Date
  - [ ] Description
  - [ ] Amount (credit/debit)
  - [ ] Running balance
- [ ] Create monthly summary calculation
- [ ] **Checkpoint: Extractor returns structured JSON with all fields**

### Evening Session (6 PM - 8 PM) - Integration

#### Hour 9-10: Connect Agents 1 & 2
- [ ] Create `app/orchestrator/workflow.py`
- [ ] Set up LangGraph state machine
- [ ] Define nodes:
  - [ ] `classify_document` node
  - [ ] `extract_data` node
- [ ] Define edges and conditional routing
- [ ] Test end-to-end: PDF → Classification → Extraction
- [ ] **Checkpoint: Pipeline runs Classifier → Extractor successfully**

---

## Day 2: Sunday - Completion (8 hours)

### Morning Session (9 AM - 12 PM) - Agent 3 + Output

#### Hour 1-2: Compliance Rules Engine
- [ ] Create `app/rules/compliance.py`
- [ ] Implement RBI compliance rules:
  ```python
  COMPLIANCE_RULES = {
      "min_avg_balance": 10000,      # ₹10,000 minimum
      "max_bounce_count": 0,          # No bounced checks
      "min_account_age_months": 6,    # 6 months history
      "suspicious_txn_threshold": 1000000,  # ₹10L flag
      "income_regularity_threshold": 0.8,   # 80% months with salary
  }
  ```
- [ ] Create rule checking functions
- [ ] Return detailed compliance report

#### Hour 3-4: Agent 3 - Validator
- [ ] Create `app/agents/validator.py`
- [ ] Implement validation logic:
  - [ ] Run all compliance rules
  - [ ] Calculate risk score (0-100)
  - [ ] Generate compliance issues list
  - [ ] Determine recommendation (APPROVE/REVIEW/REJECT)
- [ ] Risk score breakdown:
  - [ ] Balance score (0-25)
  - [ ] Transaction pattern score (0-25)
  - [ ] Income regularity score (0-25)
  - [ ] Red flags score (0-25)
- [ ] **Checkpoint: Validator returns risk score and recommendation**

#### Hour 5-6: Complete Pipeline
- [ ] Add `validate_compliance` node to workflow
- [ ] Implement final report generation
- [ ] Create JSON output structure:
  ```python
  {
      "document_info": {...},
      "extracted_data": {...},
      "transactions_summary": {...},
      "compliance_check": {...},
      "risk_assessment": {
          "score": 75,
          "breakdown": {...},
          "issues": [...],
          "recommendation": "APPROVE"
      },
      "processing_time": "12.5s"
  }
  ```
- [ ] Add error handling throughout pipeline
- [ ] **Checkpoint: Full pipeline runs end-to-end**

### Afternoon Session (1 PM - 5 PM) - Streamlit UI

#### Hour 7-8: Basic UI Structure
- [ ] Create `app/ui/streamlit_app.py`
- [ ] Implement layout:
  - [ ] Header with logo/title
  - [ ] File uploader component
  - [ ] Processing status area
  - [ ] Results display area
- [ ] Add file upload handling
- [ ] Connect to LoanProcessor

#### Hour 9-10: UI Polish
- [ ] Add progress indicators:
  - [ ] "Classifying document..." with spinner
  - [ ] "Extracting data..." with spinner
  - [ ] "Running compliance checks..." with spinner
- [ ] Create results visualization:
  - [ ] Document info card
  - [ ] Extracted fields table
  - [ ] Transaction summary chart
  - [ ] Risk score gauge/meter
  - [ ] Compliance issues list
  - [ ] Recommendation badge (green/yellow/red)
- [ ] Add JSON download button
- [ ] Add "Process Another" button
- [ ] **Checkpoint: Beautiful, functional demo UI**

### Evening Session (6 PM - 9 PM) - Polish & Deploy

#### Hour 11: Error Handling & Edge Cases
- [ ] Handle invalid file types
- [ ] Handle empty/blank PDFs
- [ ] Handle LLM API errors
- [ ] Add retry logic for transient failures
- [ ] User-friendly error messages

#### Hour 12: Testing
- [ ] Test with 3+ different bank statements
- [ ] Test with intentionally bad PDF
- [ ] Test with non-bank-statement PDF
- [ ] Verify all extracted fields are accurate
- [ ] Time the full processing (target: <30s)

#### Hour 13: Deployment
- [ ] Create `requirements.txt` (final)
- [ ] Test local Streamlit run
- [ ] Deploy to Streamlit Cloud:
  - [ ] Connect GitHub repo
  - [ ] Add secrets (API keys)
  - [ ] Deploy and test live URL
- [ ] **Checkpoint: Live demo URL working**

#### Hour 14: Documentation & Recording
- [ ] Update README with final details
- [ ] Record 2-minute demo video:
  - [ ] Show upload
  - [ ] Show processing
  - [ ] Show results
  - [ ] Highlight architecture decisions
- [ ] Prepare talking points for Vijay conversation

---

## Final Deliverables Checklist

### Code
- [ ] Clean, well-commented code
- [ ] Type hints throughout
- [ ] Docstrings on all functions
- [ ] No hardcoded API keys
- [ ] Proper error handling

### Documentation
- [ ] README.md (complete)
- [ ] Architecture diagram
- [ ] API documentation
- [ ] Setup instructions

### Demo
- [ ] Live Streamlit URL
- [ ] 2-minute demo video
- [ ] Sample output JSON

### Outreach Preparation
- [ ] LinkedIn connection request draft
- [ ] Email to careers@neurofin.ai draft
- [ ] Key talking points document

---

## Success Criteria

| Criteria | Target | Status |
|----------|--------|--------|
| Processes bank statement end-to-end | ✓ | [ ] |
| Extracts 10+ fields accurately | >90% | [ ] |
| Returns valid risk score | 0-100 | [ ] |
| Processing time | <30 sec | [ ] |
| UI is professional | Clean/intuitive | [ ] |
| Demo is live | Public URL | [ ] |
| Code is on GitHub | Public repo | [ ] |

---

## Troubleshooting Notes

### Common Issues

**PDF extraction returns empty:**
- Check if PDF is image-based (needs OCR)
- Try pdfplumber if PyMuPDF fails

**LLM returns inconsistent format:**
- Use structured output with Pydantic
- Add few-shot examples to prompts

**Streamlit crashes on file upload:**
- Check file size limits
- Ensure temp file cleanup

**LangGraph state not updating:**
- Verify return statements in nodes
- Check state key names match exactly

---

## Post-Build: Monday Morning Outreach

### LinkedIn Message to Vijay Makhijani
```
Hi Vijay,

I came across the CTO role at Neurofin and was impressed by your approach
to BFSI operations automation with modular AI agents.

I'm currently building RAG systems for document matching at a real estate
startup (Kinetic Blume) - similar challenges to loan document processing.

This weekend, I built a prototype multi-agent loan processor that mirrors
your architecture: [DEMO_URL]

It uses LangGraph to orchestrate 3 specialized agents (Classifier →
Extractor → Validator) for same-day disbursal workflows.

Would love 15 minutes to discuss how I could contribute to Neurofin's
technical vision.

Best,
Lohith
```

### Email to careers@neurofin.ai
```
Subject: CTO Application - Built Multi-Agent Loan Processor Demo

Hi Neurofin Team,

I applied for the CTO position via LinkedIn and wanted to share a
technical demonstration I built this weekend.

Demo: [STREAMLIT_URL]
GitHub: [REPO_URL]
Video: [LOOM_URL]

The prototype implements a multi-agent system for loan document processing,
directly inspired by Neurofin's modular approach. It uses LangGraph for
orchestration and achieves <30 second processing time.

Happy to discuss the architecture decisions and how my experience building
production LLM systems at Kinetic Blume translates to Neurofin's mission.

Best regards,
Lohith Rampalli
lrampalli@kineticblume.com
```

---

*Created: February 13, 2026*
*Target Completion: February 16, 2026*
