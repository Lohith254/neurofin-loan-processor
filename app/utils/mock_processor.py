"""
Mock processor for demo mode (no API key required).
Pattern-matching extraction from parsed PDFs.
"""

import re
from collections import defaultdict
from typing import List

from app.orchestrator.state import (
    DocumentType, Recommendation, ClassificationResult,
    ExtractedData, Transaction, TransactionSummary,
    RiskAssessment, ComplianceCheck, ProcessingResult
)
from app.rules.compliance import ComplianceRules
from app.parsers.pdf_parser import ParsedPDF


def mock_classify(parsed: ParsedPDF) -> ClassificationResult:
    """Classify document using keyword matching."""
    text_lower = parsed.raw_text.lower()
    is_bank_statement = any(kw in text_lower for kw in
        ['statement of account', 'bank statement', 'transaction details', 'opening balance'])

    return ClassificationResult(
        document_type=DocumentType.BANK_STATEMENT if is_bank_statement else DocumentType.OTHER,
        quality_score=8.5,
        is_readable=True,
        is_complete=True,
        issues=[],
        can_proceed=is_bank_statement
    )


def mock_extract(parsed: ParsedPDF) -> ExtractedData:
    """Extract data from parsed PDF using pattern matching."""
    text = parsed.raw_text

    name_match = re.search(r'Account Holder[:\s]+([A-Z][A-Z\s]+)', text)
    account_holder = name_match.group(1).strip() if name_match else "Unknown"

    # Look for bank name near the top of the document (first 500 chars)
    header_text = text[:500]
    bank_patterns = [
        (r'ICICI\s*Bank', 'ICICI Bank'),
        (r'HDFC\s*Bank', 'HDFC Bank'),
        (r'State Bank of India|SBI', 'State Bank of India'),
        (r'Axis\s*Bank', 'Axis Bank'),
        (r'Kotak\s*(?:Mahindra)?\s*Bank', 'Kotak Mahindra Bank'),
    ]
    bank_name = "Unknown Bank"
    for pattern, name in bank_patterns:
        if re.search(pattern, header_text, re.IGNORECASE):
            bank_name = name
            break

    acc_match = re.search(r'Account Number[:\s]+([\dX\s]+)', text)
    account_number = acc_match.group(1).strip() if acc_match else "XXXX1234"

    period_match = re.search(r'Statement Period[:\s]+(\d{2}-\w{3}-\d{4})\s+to\s+(\d{2}-\w{3}-\d{4})', text)
    if period_match:
        start_date = period_match.group(1)
        end_date = period_match.group(2)
    else:
        start_date = "2025-11-01"
        end_date = "2026-01-31"

    # Currency prefix: matches INR, I, ₹, or nothing
    cur = r'(?:INR|I|\u20b9)?\s*'

    opening_match = re.search(r'Opening Balance[^:]*[:\s]+' + cur + r'([\d,]+\.?\d*)', text)
    opening_balance = float(opening_match.group(1).replace(',', '')) if opening_match else 0.0

    closing_match = re.search(r'Closing Balance[^:]*[:\s]+' + cur + r'([\d,]+\.?\d*)', text)
    closing_balance = float(closing_match.group(1).replace(',', '')) if closing_match else 0.0

    credits_match = re.search(r'Total Credits[:\s]+' + cur + r'([\d,]+\.?\d*)', text)
    total_credits = float(credits_match.group(1).replace(',', '')) if credits_match else 0.0

    debits_match = re.search(r'Total Debits[:\s]+' + cur + r'([\d,]+\.?\d*)', text)
    total_debits = float(debits_match.group(1).replace(',', '')) if debits_match else 0.0

    transactions = []
    if parsed.tables:
        for table in parsed.tables:
            for row in table.get('rows', []):
                date = row.get('Date', '')
                desc = row.get('Description', '')
                debit = row.get('Debit (n)', row.get('Debit (I)', row.get('Debit', '')))
                credit = row.get('Credit (n)', row.get('Credit (I)', row.get('Credit', '')))
                balance = row.get('Balance (n)', row.get('Balance (I)', row.get('Balance', '')))

                if date and desc and desc not in ['Opening Balance', 'Closing Balance', '-']:
                    try:
                        amount = float(credit.replace(',', '')) if credit else float(debit.replace(',', ''))
                        txn_type = 'credit' if credit else 'debit'
                        bal = float(balance.replace(',', '')) if balance else None

                        transactions.append(Transaction(
                            date=date,
                            description=desc,
                            amount=amount,
                            type=txn_type,
                            balance=bal
                        ))
                    except (ValueError, AttributeError):
                        pass

    return ExtractedData(
        account_holder_name=account_holder,
        bank_name=bank_name,
        branch="Koramangala, Bengaluru",
        account_number_masked=account_number,
        account_type="Savings",
        statement_period_start=start_date,
        statement_period_end=end_date,
        opening_balance=opening_balance,
        closing_balance=closing_balance,
        total_credits=total_credits,
        total_debits=total_debits,
        transaction_count=len(transactions),
        transactions=transactions
    )


def mock_monthly_summaries(extracted_data: ExtractedData) -> List[TransactionSummary]:
    """Calculate monthly summaries from extracted transactions."""
    monthly_data = defaultdict(lambda: {
        "credits": 0.0, "debits": 0.0, "balances": [], "salary": None
    })

    for txn in extracted_data.transactions:
        try:
            parts = txn.date.split('-')
            month_map = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                        'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                        'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
            year = '2025' if parts[2] in ('25', '2025') else '2026'
            month = f"{year}-{month_map.get(parts[1], '01')}"
        except (IndexError, KeyError):
            continue

        if txn.type == "credit":
            monthly_data[month]["credits"] += txn.amount
            if txn.amount >= 50000 and any(kw in txn.description.lower() for kw in ['salary', 'neft']):
                monthly_data[month]["salary"] = txn.amount
        else:
            monthly_data[month]["debits"] += txn.amount

        if txn.balance:
            monthly_data[month]["balances"].append(txn.balance)

    summaries = []
    for month, data in sorted(monthly_data.items()):
        avg_balance = sum(data["balances"]) / len(data["balances"]) if data["balances"] else 50000.0
        summaries.append(TransactionSummary(
            month=month,
            total_credits=data["credits"],
            total_debits=data["debits"],
            net_flow=data["credits"] - data["debits"],
            avg_balance=avg_balance,
            salary_credit=data["salary"]
        ))

    return summaries


def mock_validate(
    extracted_data: ExtractedData,
    monthly_summaries: List[TransactionSummary],
    custom_rules: dict = None
) -> RiskAssessment:
    """Run compliance checks and calculate risk score without LLM."""
    compliance = ComplianceRules(rules=custom_rules)
    compliance_checks = compliance.run_all_checks(extracted_data, monthly_summaries)

    passed_count = sum(1 for c in compliance_checks if c.passed)
    failed_checks = [c for c in compliance_checks if not c.passed]

    base_score = 100 - (passed_count / len(compliance_checks) * 100)
    high_severity_fails = sum(1 for c in failed_checks if c.severity == "high")
    risk_score = min(100, base_score + (high_severity_fails * 20))

    if risk_score <= 30:
        recommendation = Recommendation.APPROVE
        reason = "All major compliance checks passed with good financial health indicators."
    elif risk_score <= 60:
        recommendation = Recommendation.REVIEW
        reason = "Some compliance concerns require manual review before approval."
    else:
        recommendation = Recommendation.REJECT
        reason = "Multiple high-severity compliance failures detected."

    return RiskAssessment(
        risk_score=int(risk_score),
        score_breakdown={
            "balance_stability": 20 if any(c.rule_name == "min_avg_balance" and c.passed for c in compliance_checks) else 5,
            "income_regularity": 25 if any(c.rule_name == "income_regularity_threshold" and c.passed for c in compliance_checks) else 10,
            "transaction_patterns": 20,
            "red_flags": -sum(10 for c in failed_checks if c.severity == "high")
        },
        compliance_checks=compliance_checks,
        issues=[f"{c.rule_name}: {c.actual_value}" for c in failed_checks],
        red_flags=[c.rule_name for c in failed_checks if c.severity == "high"],
        recommendation=recommendation,
        recommendation_reason=reason
    )
