"""
Agent 3: Validator
Runs compliance checks and calculates risk score.
"""

import logging
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate

from app.orchestrator.state import (
    RiskAssessment,
    Recommendation,
    LoanProcessorState,
)
from app.rules.compliance import ComplianceRules, COMPLIANCE_RULES
from app.utils.llm_factory import create_llm, LLMProvider

logger = logging.getLogger(__name__)

VALIDATOR_PROMPT = """You are a loan compliance and risk assessment expert for Indian banking (RBI guidelines).
Analyze the extracted bank statement data and provide a comprehensive risk assessment.

**Extracted Data:**
{extracted_data}

**Monthly Summaries:**
{monthly_summaries}

**Compliance Rules Applied:**
{compliance_rules}

**Compliance Check Results (already computed):**
{compliance_results}

Based on this data, provide your assessment:

1. **risk_score** (0-100):
   - 0-30: Low risk, likely approval
   - 31-60: Medium risk, needs review
   - 61-100: High risk, likely rejection

2. **score_breakdown**: A dictionary with exactly these keys:
   - "balance_stability": 0-25 points (higher = better stability)
   - "income_regularity": 0-25 points (higher = more regular income)
   - "transaction_patterns": 0-25 points (higher = healthier patterns)
   - "red_flags": negative points for concerns (e.g., -10, -20)

3. **compliance_checks**: Include ALL the compliance check results from above.

4. **issues**: List of compliance concern strings.

5. **red_flags**: List of serious concern strings (bounced checks, suspicious transactions).

6. **recommendation**: APPROVE (risk <= 30), REVIEW (31-60), or REJECT (> 60)

7. **recommendation_reason**: 1-2 sentence explanation of the decision.
"""


class ValidatorAgent:
    """Agent responsible for compliance validation and risk scoring."""

    def __init__(self, provider: LLMProvider = "ollama", model_name: str = None):
        self.llm = create_llm(provider=provider, model_name=model_name, max_tokens=2048)
        self.structured_llm = self.llm.with_structured_output(RiskAssessment)
        self.prompt = ChatPromptTemplate.from_template(VALIDATOR_PROMPT)
        self.compliance = ComplianceRules()

    def validate(self, state: LoanProcessorState) -> Dict[str, Any]:
        """Run compliance checks and calculate risk score."""
        extracted_data = state.get("extracted_data")
        monthly_summaries = state.get("monthly_summaries", [])

        if not extracted_data:
            return {
                "risk_assessment": RiskAssessment(
                    risk_score=100,
                    score_breakdown={
                        "balance_stability": 0,
                        "income_regularity": 0,
                        "transaction_patterns": 0,
                        "red_flags": -25
                    },
                    compliance_checks=[],
                    issues=["No data extracted from document"],
                    red_flags=["Cannot assess - no data"],
                    recommendation=Recommendation.REJECT,
                    recommendation_reason="Unable to extract data from document"
                ),
                "current_agent": "validator",
                "error": "No extracted data available"
            }

        # Run rule-based compliance checks first
        compliance_results = self.compliance.run_all_checks(
            extracted_data, monthly_summaries
        )

        chain = self.prompt | self.structured_llm

        try:
            result = chain.invoke({
                "extracted_data": extracted_data.model_dump_json(indent=2),
                "monthly_summaries": [s.model_dump() for s in monthly_summaries],
                "compliance_rules": str(COMPLIANCE_RULES),
                "compliance_results": [c.model_dump() for c in compliance_results]
            })

            logger.info(f"Validation: risk={result.risk_score}, rec={result.recommendation.value}")

            return {
                "risk_assessment": result,
                "current_agent": "validator",
                "completed": True,
                "error": None
            }
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return self._fallback_assessment(compliance_results)

    def _fallback_assessment(self, compliance_results) -> Dict[str, Any]:
        """Generate risk assessment from rules alone if LLM fails."""
        passed = sum(1 for c in compliance_results if c.passed)
        failed = [c for c in compliance_results if not c.passed]
        total = len(compliance_results)

        base_score = 100 - (passed / total * 100) if total else 100
        high_fails = sum(1 for c in failed if c.severity == "high")
        risk_score = min(100, int(base_score + high_fails * 20))

        if risk_score <= 30:
            rec = Recommendation.APPROVE
            reason = "All major compliance checks passed."
        elif risk_score <= 60:
            rec = Recommendation.REVIEW
            reason = "Some compliance concerns require manual review."
        else:
            rec = Recommendation.REJECT
            reason = "Multiple compliance failures detected."

        return {
            "risk_assessment": RiskAssessment(
                risk_score=risk_score,
                score_breakdown={
                    "balance_stability": 20 if any(c.rule_name == "min_avg_balance" and c.passed for c in compliance_results) else 5,
                    "income_regularity": 25 if any(c.rule_name == "income_regularity_threshold" and c.passed for c in compliance_results) else 10,
                    "transaction_patterns": 20,
                    "red_flags": -sum(10 for c in failed if c.severity == "high")
                },
                compliance_checks=compliance_results,
                issues=[f"{c.rule_name}: {c.actual_value}" for c in failed],
                red_flags=[c.rule_name for c in failed if c.severity == "high"],
                recommendation=rec,
                recommendation_reason=reason
            ),
            "current_agent": "validator",
            "completed": True,
            "error": "LLM validation failed, used rule-based fallback"
        }

    def __call__(self, state: LoanProcessorState) -> Dict[str, Any]:
        """Make the agent callable for LangGraph integration."""
        return self.validate(state)
