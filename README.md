---
title: Neurofin Loan Processor
emoji: 🏛
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: true
---

# Multi-Agent Loan Processor

> AI-powered loan document processing with RBI compliance validation — built for Neurofin AI Technologies.

**[Live Demo](https://lohith2710r-neurofin-loan-processor.hf.space)** | [Architecture](#architecture) | [Quick Start](#quick-start)

---

## Problem

Secured loan disbursal in India takes **5-7 days** due to manual document verification, ~10 manual checks per customer, and fragmented systems. This system reduces it to **minutes** using a multi-agent AI pipeline.

## Architecture

```
                    ┌─────────────────────────────┐
                    │     LangGraph Orchestrator   │
                    │      (State Machine)         │
                    └──────────┬──────────────────┘
                               │
    ┌──────────────────────────┼──────────────────────────┐
    │                          │                          │
    ▼                          ▼                          ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Agent 1    │      │   Agent 2    │      │   Agent 3    │
│  Classifier  │─────▶│  Extractor   │─────▶│  Validator   │
│              │      │              │      │              │
│ Doc type     │      │ Account info │      │ 7 RBI rules  │
│ Quality 0-10 │      │ Transactions │      │ Risk 0-100   │
│ Gate check   │      │ Monthly flow │      │ APPROVE/     │
│              │      │ Salary detect│      │ REVIEW/REJECT│
└──────────────┘      └──────────────┘      └──────────────┘
```

**Key design decisions:**
- **Conditional routing** — Classifier gates the pipeline; low-quality documents are rejected early (no wasted LLM calls)
- **Structured output** — All agents use `with_structured_output()` (native tool calling) for reliable Pydantic model responses
- **Provider abstraction** — Swap between Groq (free), Claude, or Ollama with zero code changes
- **Rule-based fallback** — Validator falls back to deterministic compliance scoring if LLM fails

## Features

| Feature | Description |
|---------|-------------|
| **3-Agent Pipeline** | Classifier, Extractor, Validator orchestrated via LangGraph |
| **7 RBI Compliance Checks** | Min balance, bounced checks, account age, suspicious transactions, income regularity, closing balance, overdraft |
| **Configurable Thresholds** | Adjust all compliance thresholds via sidebar sliders — see how rules affect outcomes in real-time |
| **Decision Explainability** | Per-check pass/fail reasoning with severity levels |
| **Pipeline Visualization** | Real-time 4-stage progress with per-agent timing |
| **3 Sample Scenarios** | Healthy (APPROVE), Risky (REJECT), Borderline (REVIEW) |
| **Multi-Provider LLM** | Groq (free cloud), Claude (paid), Ollama (local) |
| **LangSmith Tracing** | Optional observability for agent calls and token usage |

## Quick Start

### Option 1: Try the Live Demo (No Setup)

Visit the **[deployed app](https://lohith2710r-neurofin-loan-processor.hf.space)** — works immediately in Demo Mode with sample PDFs.

### Option 2: Run Locally

```bash
# Clone
git clone https://github.com/yourusername/neurofin-loan-processor.git
cd neurofin-loan-processor

# Install
pip install -r requirements.txt

# Run demo (no API key needed)
python demo.py --demo

# Run Streamlit UI
streamlit run app/ui/streamlit_app.py
```

### Option 3: Run with Live LLM (Free)

```bash
# Get a free Groq API key at https://console.groq.com
export GROQ_API_KEY=your_key_here

# CLI
python demo.py --groq --pdf data/sample_statements/icici_statement_healthy.pdf

# Or use the Streamlit UI — select "Live Mode (Groq - Free)" in sidebar
streamlit run app/ui/streamlit_app.py
```

## Project Structure

```
neurofin-loan-processor/
├── app/
│   ├── agents/
│   │   ├── classifier.py       # Agent 1: Document type + quality
│   │   ├── extractor.py        # Agent 2: Structured data extraction
│   │   └── validator.py        # Agent 3: Compliance + risk scoring
│   ├── orchestrator/
│   │   ├── workflow.py         # LangGraph state machine
│   │   └── state.py            # Pydantic state models
│   ├── parsers/
│   │   └── pdf_parser.py       # PyMuPDF + pdfplumber
│   ├── rules/
│   │   └── compliance.py       # 7 RBI compliance rules engine
│   ├── utils/
│   │   ├── llm_factory.py      # Multi-provider LLM factory
│   │   └── mock_processor.py   # Pattern-matching mock agents
│   └── ui/
│       └── streamlit_app.py    # Full demo interface
├── data/sample_statements/     # 4 sample bank statement PDFs
├── tests/                      # 23 unit tests (100% pass)
├── scripts/generate_samples.py # PDF sample generator
├── demo.py                     # CLI demo runner
├── DEMO_SCRIPT.md              # 3-minute demo narration
└── requirements.txt
```

## Tech Stack

| Component | Technology | Why |
|-----------|------------|-----|
| Orchestrator | **LangGraph** | State machine with conditional routing, production-grade agent orchestration |
| LLM | **Groq** / Claude / Ollama | Groq = free + fast; Claude = highest quality; Ollama = offline |
| Structured Output | **Pydantic v2** | Type-safe LLM responses via `with_structured_output()` |
| PDF Parsing | **PyMuPDF + pdfplumber** | Text extraction + table detection |
| UI | **Streamlit** | Rapid prototyping with real-time visualization |
| Deployment | **Streamlit Cloud** | Free hosting, GitHub integration |

## Compliance Rules

| # | Rule | Threshold | Severity |
|---|------|-----------|----------|
| 1 | Min Average Balance | INR 10,000 | High |
| 2 | Bounced Checks | 0 allowed | High |
| 3 | Account Age | 6 months | Medium |
| 4 | Suspicious Transactions | > INR 10L | Medium |
| 5 | Income Regularity | 80% months with salary | Medium |
| 6 | Min Closing Balance | INR 5,000 | Low |
| 7 | Overdraft Instances | Max 2 | Medium |

All thresholds are configurable via the Streamlit sidebar.

## Sample Outcomes

| PDF | Bank | Checks | Risk Score | Recommendation |
|-----|------|--------|------------|----------------|
| `icici_statement_healthy.pdf` | ICICI | 7/7 pass | 0 | **APPROVE** |
| `axis_statement_borderline.pdf` | Axis | 5/7 pass | 48 | **REVIEW** |
| `sbi_statement_risky.pdf` | SBI | 4/7 pass | 77 | **REJECT** |

## Testing

```bash
python -m pytest tests/ -v
# 23 passed in 0.5s
```

## API Usage

```python
from app.orchestrator.workflow import LoanProcessor

# Auto-detects provider from environment (GROQ_API_KEY or ANTHROPIC_API_KEY)
processor = LoanProcessor()
result = processor.process("path/to/bank_statement.pdf")

print(f"Risk Score: {result.risk_score}/100")
print(f"Recommendation: {result.recommendation.value}")
```

## Author

**Lohith Rampalli**
- LinkedIn: [linkedin.com/in/lohithrampalli](https://linkedin.com/in/lohithrampalli)

---

*Built as a technical demonstration for Neurofin AI Technologies — February 2026*
