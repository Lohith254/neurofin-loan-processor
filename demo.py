#!/usr/bin/env python3
"""
Neurofin Loan Processor - CLI Demo
Run: python demo.py [--pdf PATH] [--demo | --groq | --live]

Demonstrates the multi-agent loan processing pipeline.
Use --demo for mock mode, --groq for free cloud LLM, --live for Claude API.
"""

import os
import sys
import argparse
import json
import time
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.parsers.pdf_parser import PDFParser
from app.orchestrator.state import (
    DocumentType, Recommendation, ProcessingResult
)
from app.utils.mock_processor import (
    mock_classify, mock_extract, mock_monthly_summaries, mock_validate
)

logging.basicConfig(level=logging.INFO, format="%(name)s - %(message)s")
logger = logging.getLogger("demo")


def print_header(text: str):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_section(text: str):
    print(f"\n--- {text} ---")


def run_demo_pipeline(pdf_path: str, use_mock: bool = True, provider: str = "claude"):
    """Run the loan processing pipeline."""
    start_time = time.time()

    print_header("NEUROFIN MULTI-AGENT LOAN PROCESSOR")
    print(f"Processing: {pdf_path}")
    mode_label = "Demo (Mock LLM)" if use_mock else f"Live ({provider.title()})"
    print(f"Mode: {mode_label}")

    # === STAGE 1: PDF PARSING ===
    print_section("STAGE 1: PDF PARSING")
    parser = PDFParser()
    try:
        parsed = parser.parse(pdf_path)
        print(f"  PDF parsed successfully")
        print(f"   Pages: {parsed.page_count}")
        print(f"   Tables: {len(parsed.tables)}")
        print(f"   Text: {len(parsed.raw_text)} chars")
    except Exception as e:
        print(f"  PDF parsing failed: {e}")
        return None

    if use_mock:
        return _run_mock_pipeline(parsed, start_time)
    else:
        return _run_live_pipeline(pdf_path, start_time, provider)


def _run_mock_pipeline(parsed, start_time):
    """Run pipeline with pattern-matching mock agents."""

    # === STAGE 2: CLASSIFICATION ===
    print_section("STAGE 2: DOCUMENT CLASSIFICATION (Agent 1)")
    classification = mock_classify(parsed)
    print(f"  Document Type: {classification.document_type.value}")
    print(f"   Quality Score: {classification.quality_score}/10")
    print(f"   Can Proceed: {classification.can_proceed}")

    if not classification.can_proceed:
        print("  Document cannot be processed further")
        return None

    # === STAGE 3: DATA EXTRACTION ===
    print_section("STAGE 3: DATA EXTRACTION (Agent 2)")
    extracted_data = mock_extract(parsed)
    monthly_summaries = mock_monthly_summaries(extracted_data)

    print(f"  Account Holder: {extracted_data.account_holder_name}")
    print(f"   Bank: {extracted_data.bank_name}")
    print(f"   Account: {extracted_data.account_number_masked}")
    print(f"   Period: {extracted_data.statement_period_start} to {extracted_data.statement_period_end}")
    print(f"   Opening: INR {extracted_data.opening_balance:,.2f}")
    print(f"   Closing: INR {extracted_data.closing_balance:,.2f}")
    print(f"   Transactions: {extracted_data.transaction_count}")

    print_section("Monthly Summaries")
    for s in monthly_summaries:
        salary_str = f"  Salary: INR {s.salary_credit:,.2f}" if s.salary_credit else ""
        print(f"   {s.month}: Credits INR {s.total_credits:,.2f} | "
              f"Debits INR {s.total_debits:,.2f} | Net INR {s.net_flow:,.2f}{salary_str}")

    # === STAGE 4: COMPLIANCE VALIDATION ===
    print_section("STAGE 4: COMPLIANCE VALIDATION (Agent 3)")
    risk_assessment = mock_validate(extracted_data, monthly_summaries)

    print("Compliance Checks:")
    for check in risk_assessment.compliance_checks:
        status = "  PASS" if check.passed else "  FAIL"
        print(f"   {status} | {check.rule_name}: {check.actual_value} (threshold: {check.threshold})")

    # === FINAL RESULTS ===
    _print_results(risk_assessment, classification, extracted_data, monthly_summaries, start_time)

    return ProcessingResult(
        success=True,
        document_type=classification.document_type,
        quality_score=classification.quality_score,
        extracted_data=extracted_data,
        monthly_summaries=monthly_summaries,
        risk_score=risk_assessment.risk_score,
        recommendation=risk_assessment.recommendation,
        compliance_issues=risk_assessment.issues,
        red_flags=risk_assessment.red_flags,
        processing_time_seconds=time.time() - start_time
    )


def _run_live_pipeline(pdf_path, start_time, provider="claude"):
    """Run pipeline with real LLM agents via LangGraph."""
    print_section("RUNNING LIVE LANGGRAPH PIPELINE")
    print(f"  Using {provider.title()} for each agent...")

    from app.orchestrator.workflow import LoanProcessor
    processor = LoanProcessor(provider=provider)
    result = processor.process(pdf_path)

    if result.success and result.extracted_data:
        # Reconstruct risk_assessment for display
        from app.orchestrator.state import RiskAssessment, Recommendation
        from app.rules.compliance import ComplianceRules
        compliance = ComplianceRules()
        compliance_checks = compliance.run_all_checks(
            result.extracted_data, result.monthly_summaries
        )

        print(f"\n  Account Holder: {result.extracted_data.account_holder_name}")
        print(f"   Bank: {result.extracted_data.bank_name}")
        print(f"   Transactions: {result.extracted_data.transaction_count}")
        print(f"\nCompliance Checks:")
        for check in compliance_checks:
            status = "  PASS" if check.passed else "  FAIL"
            print(f"   {status} | {check.rule_name}: {check.actual_value}")

    processing_time = time.time() - start_time
    print_header("PROCESSING RESULTS")

    risk_color = "LOW" if result.risk_score <= 30 else "MEDIUM" if result.risk_score <= 60 else "HIGH"
    print(f"\n  Risk Score: [{risk_color}] {result.risk_score}/100")
    print(f"  Recommendation: {result.recommendation.value}")
    print(f"  Processing Time: {processing_time:.2f}s")

    if result.compliance_issues:
        print(f"\n  Issues:")
        for issue in result.compliance_issues:
            print(f"      {issue}")

    if result.red_flags:
        print(f"\n  RED FLAGS:")
        for flag in result.red_flags:
            print(f"      {flag}")

    return result


def _print_results(risk_assessment, classification, extracted_data, monthly_summaries, start_time):
    """Print formatted final results."""
    processing_time = time.time() - start_time

    print_header("PROCESSING RESULTS")

    risk_color = "LOW" if risk_assessment.risk_score <= 30 else "MEDIUM" if risk_assessment.risk_score <= 60 else "HIGH"

    print(f"\n  RISK ASSESSMENT")
    print(f"   Risk Score: [{risk_color}] {risk_assessment.risk_score}/100")
    print(f"\n   Score Breakdown:")
    for category, score in risk_assessment.score_breakdown.items():
        print(f"      {category}: {score}")

    print(f"\n  COMPLIANCE SUMMARY")
    passed = sum(1 for c in risk_assessment.compliance_checks if c.passed)
    total = len(risk_assessment.compliance_checks)
    print(f"   Checks Passed: {passed}/{total}")

    if risk_assessment.issues:
        print(f"   Issues:")
        for issue in risk_assessment.issues:
            print(f"      {issue}")

    if risk_assessment.red_flags:
        print(f"\n  RED FLAGS:")
        for flag in risk_assessment.red_flags:
            print(f"      {flag}")

    rec = risk_assessment.recommendation.value.upper()
    print(f"\n{'='*60}")
    print(f"  RECOMMENDATION: {rec}")
    print(f"{'='*60}")
    print(f"\n   {risk_assessment.recommendation_reason}")
    print(f"\n  Processing Time: {processing_time:.2f} seconds")


def main():
    parser = argparse.ArgumentParser(description="Neurofin Loan Processor Demo")
    parser.add_argument("--pdf", "-p", default="data/sample_statements/hdfc_statement_001.pdf",
                       help="Path to bank statement PDF")
    parser.add_argument("--demo", "-d", action="store_true", default=True,
                       help="Run in demo mode with mock LLM (default)")
    parser.add_argument("--groq", "-g", action="store_true",
                       help="Run with Groq (free cloud LLM - requires GROQ_API_KEY)")
    parser.add_argument("--live", "-l", action="store_true",
                       help="Run with Claude API (requires ANTHROPIC_API_KEY)")
    parser.add_argument("--output", "-o", help="Save results to JSON file")

    args = parser.parse_args()

    if args.groq:
        use_mock = False
        provider = "groq"
        if not os.getenv("GROQ_API_KEY"):
            print("Error: GROQ_API_KEY not set. Get a free key at https://console.groq.com")
            sys.exit(1)
    elif args.live:
        use_mock = False
        provider = "claude"
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("Error: ANTHROPIC_API_KEY not set. Use --demo or --groq instead.")
            sys.exit(1)
    else:
        use_mock = True
        provider = "groq"

    result = run_demo_pipeline(args.pdf, use_mock, provider)

    if result and args.output:
        with open(args.output, 'w') as f:
            f.write(result.model_dump_json(indent=2))
        print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()
