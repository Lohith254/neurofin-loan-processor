# 3-Minute Demo Script: Multi-Agent Loan Processor

## Setup (before the demo)
```bash
# Terminal 1: Have Streamlit running
streamlit run app/ui/streamlit_app.py

# Terminal 2: Have CLI ready
cd Neurofin_Loan_Processor
```

---

## [0:00 - 0:30] THE PROBLEM

> "In Indian BFSI, loan officers manually review hundreds of bank statements daily. Each one takes 15-20 minutes: check the document quality, extract account details and transactions, calculate monthly cash flows, then run compliance checks against RBI guidelines. It's slow, error-prone, and doesn't scale.
>
> I built a multi-agent system that does this in under a second."

---

## [0:30 - 1:15] THE ARCHITECTURE

> "The system uses three specialized AI agents, orchestrated by LangGraph as a state machine."

**Show the Streamlit sidebar architecture diagram, then explain:**

> "**Agent 1 - Classifier** receives the raw PDF text and determines: is this actually a bank statement? Is it readable? Is it complete? If quality is below threshold, the pipeline stops early. This is a key design decision - we gate the pipeline to avoid wasting compute on bad documents.
>
> **Agent 2 - Extractor** parses the structured data: account holder, bank, transaction history, balances. It then calculates monthly summaries and detects salary credits automatically.
>
> **Agent 3 - Validator** runs 7 RBI compliance checks - minimum balance, bounced checks, account age, suspicious transactions, income regularity - calculates a composite risk score, and gives a recommendation: Approve, Review, or Reject.
>
> Each agent uses Claude with structured outputs via Pydantic models, so every response is type-safe and validated. The state flows through a LangGraph StateGraph with conditional routing - if the classifier says the document is garbage, we don't waste API calls on extraction."

---

## [1:15 - 2:15] LIVE DEMO

> "Let me show you three real scenarios."

### Scenario 1: Healthy Account (APPROVE)
**Select: `icici_statement_healthy.pdf` -> Process**

> "Priya Sharma, ICICI Bank, 6 months of statements. Watch the pipeline - classifier confirms it's a bank statement with 8.5 quality. Extractor pulls 29 transactions, detects salary credits every month at 1.3 lakhs. Validator runs all 7 checks - they all pass. Risk score: 0. Recommendation: Approve. Total time: under a second."

### Scenario 2: Risky Account (REJECT)
**Select: `sbi_statement_risky.pdf` -> Process**

> "Now Rajesh Kumar, SBI account. Same pipeline, very different outcome. Notice: 3 bounced checks detected, irregular income - salary only 1 out of 4 months, and the closing balance is 2,100 rupees. Risk score jumps to 77. Recommendation: Reject. The system caught what a human reviewer would flag."

### Scenario 3: Borderline (REVIEW)
**Select: `axis_statement_borderline.pdf` -> Process**

> "Anita Desai, Axis Bank. This is the interesting one - she has regular salary, good average balance, but one bounced check and only 5 months of history. Risk score: 48. Recommendation: Review. The system doesn't auto-reject - it flags it for human judgment."

---

## [2:15 - 2:45] CONFIGURABLE THRESHOLDS

> "Now here's where it gets interesting for the business."

**Adjust the sidebar sliders:**

> "These compliance thresholds are configurable. Watch - if I lower the minimum account age to 4 months and set max bounced checks to 1..."

**Reprocess the borderline account**

> "Same document, but now with relaxed thresholds - the recommendation changes. This means the compliance team can tune the rules without touching code. That's product thinking, not just engineering."

**Click the Explainability tab**

> "And for every check, there's full explainability - why it passed, why it failed, what the actual value was versus the threshold. This is critical for RBI audit compliance."

---

## [2:45 - 3:00] CLOSING

> "To summarize: three specialized agents, LangGraph orchestration, 7 RBI compliance checks, configurable thresholds, full explainability, and it processes a bank statement in under a second. The architecture is modular - adding new document types or compliance rules is just adding a new agent or a new check function.
>
> I built this over a weekend to demonstrate the kind of GenAI systems I'd build at Neurofin."

---

## Key Talking Points (if Q&A follows)

- **Why 3 agents vs 1?** Separation of concerns. Each agent has a focused prompt and schema. The classifier acts as a quality gate. In production, you can scale and version each independently.

- **Why LangGraph?** State machine gives explicit control over flow. Conditional routing means we can add retry logic, human-in-the-loop, or parallel processing without restructuring.

- **Why structured outputs?** Every agent response is a Pydantic model. No parsing JSON from free-text. Type-safe, validated, serializable. This is production-grade, not notebook-grade.

- **How does it handle edge cases?** Fallback logic: if the LLM fails, the validator falls back to rule-based scoring. The pipeline always produces a result.

- **What about scale?** The architecture supports batch processing. Each document is independent. Add a FastAPI layer and a queue, and you're processing hundreds concurrently.

- **Cost?** Three Claude Sonnet calls per document. ~$0.02 per statement. At 1000 statements/day, that's $20/day vs a team of loan officers.
