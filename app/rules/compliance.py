"""
Compliance Rules Engine
RBI compliance rules for loan document validation.
"""

from typing import List, Optional
from dataclasses import dataclass

from app.orchestrator.state import (
    ComplianceCheck,
    ExtractedData,
    TransactionSummary
)


# RBI Compliance Rules Configuration
COMPLIANCE_RULES = {
    "min_avg_balance": {
        "threshold": 10000,  # ₹10,000 minimum average balance
        "description": "Minimum average monthly balance requirement",
        "severity": "high"
    },
    "max_bounce_count": {
        "threshold": 0,  # No bounced checks allowed
        "description": "Maximum number of bounced checks in statement period",
        "severity": "high"
    },
    "min_account_age_months": {
        "threshold": 6,  # Minimum 6 months history
        "description": "Minimum account history required",
        "severity": "medium"
    },
    "suspicious_txn_threshold": {
        "threshold": 1000000,  # ₹10 lakh threshold
        "description": "Large transaction requiring additional scrutiny",
        "severity": "medium"
    },
    "income_regularity_threshold": {
        "threshold": 0.8,  # 80% of months should have salary credit
        "description": "Percentage of months with regular income credit",
        "severity": "medium"
    },
    "min_closing_balance": {
        "threshold": 5000,  # ₹5,000 minimum closing balance
        "description": "Minimum closing balance requirement",
        "severity": "low"
    },
    "max_overdraft_instances": {
        "threshold": 2,  # Maximum 2 overdraft instances
        "description": "Maximum overdraft occurrences allowed",
        "severity": "medium"
    }
}


class ComplianceRules:
    """Engine for running compliance checks against extracted data."""

    def __init__(self, rules: dict = None):
        """Initialize with custom or default rules.

        Args:
            rules: Optional custom rules dictionary.
        """
        self.rules = rules or COMPLIANCE_RULES

    def run_all_checks(
        self,
        extracted_data: ExtractedData,
        monthly_summaries: List[TransactionSummary]
    ) -> List[ComplianceCheck]:
        """Run all compliance checks.

        Args:
            extracted_data: Extracted bank statement data.
            monthly_summaries: Monthly transaction summaries.

        Returns:
            List of ComplianceCheck results.
        """
        checks = []

        # Check 1: Minimum Average Balance
        checks.append(self._check_min_avg_balance(monthly_summaries))

        # Check 2: Bounced Checks
        checks.append(self._check_bounce_count(extracted_data))

        # Check 3: Account Age
        checks.append(self._check_account_age(monthly_summaries))

        # Check 4: Suspicious Transactions
        checks.append(self._check_suspicious_transactions(extracted_data))

        # Check 5: Income Regularity
        checks.append(self._check_income_regularity(monthly_summaries))

        # Check 6: Minimum Closing Balance
        checks.append(self._check_closing_balance(extracted_data))

        # Check 7: Overdraft Instances
        checks.append(self._check_overdraft(extracted_data))

        return checks

    def _check_min_avg_balance(
        self,
        monthly_summaries: List[TransactionSummary]
    ) -> ComplianceCheck:
        """Check minimum average balance requirement."""
        rule = self.rules["min_avg_balance"]

        if not monthly_summaries:
            return ComplianceCheck(
                rule_name="min_avg_balance",
                rule_description=rule["description"],
                passed=False,
                actual_value="N/A",
                threshold=f"₹{rule['threshold']:,}",
                severity=rule["severity"]
            )

        avg_balance = sum(s.avg_balance for s in monthly_summaries) / len(monthly_summaries)
        passed = avg_balance >= rule["threshold"]

        return ComplianceCheck(
            rule_name="min_avg_balance",
            rule_description=rule["description"],
            passed=passed,
            actual_value=f"₹{avg_balance:,.2f}",
            threshold=f"₹{rule['threshold']:,}",
            severity=rule["severity"]
        )

    def _check_bounce_count(self, extracted_data: ExtractedData) -> ComplianceCheck:
        """Check for bounced checks in transactions."""
        rule = self.rules["max_bounce_count"]

        # Look for bounce-related keywords in transactions
        bounce_keywords = ["bounce", "dishonour", "return", "insufficient", "unpaid"]
        bounce_count = 0

        for txn in extracted_data.transactions:
            desc_lower = txn.description.lower()
            if any(kw in desc_lower for kw in bounce_keywords):
                bounce_count += 1

        passed = bounce_count <= rule["threshold"]

        return ComplianceCheck(
            rule_name="max_bounce_count",
            rule_description=rule["description"],
            passed=passed,
            actual_value=str(bounce_count),
            threshold=str(rule["threshold"]),
            severity=rule["severity"]
        )

    def _check_account_age(
        self,
        monthly_summaries: List[TransactionSummary]
    ) -> ComplianceCheck:
        """Check minimum account age requirement."""
        rule = self.rules["min_account_age_months"]
        account_age = len(monthly_summaries)
        passed = account_age >= rule["threshold"]

        return ComplianceCheck(
            rule_name="min_account_age_months",
            rule_description=rule["description"],
            passed=passed,
            actual_value=f"{account_age} months",
            threshold=f"{rule['threshold']} months",
            severity=rule["severity"]
        )

    def _check_suspicious_transactions(
        self,
        extracted_data: ExtractedData
    ) -> ComplianceCheck:
        """Check for suspiciously large transactions."""
        rule = self.rules["suspicious_txn_threshold"]

        large_txns = [
            txn for txn in extracted_data.transactions
            if txn.amount >= rule["threshold"]
        ]

        passed = len(large_txns) == 0

        return ComplianceCheck(
            rule_name="suspicious_txn_threshold",
            rule_description=rule["description"],
            passed=passed,
            actual_value=f"{len(large_txns)} transactions > ₹{rule['threshold']:,}",
            threshold=f"₹{rule['threshold']:,}",
            severity=rule["severity"]
        )

    def _check_income_regularity(
        self,
        monthly_summaries: List[TransactionSummary]
    ) -> ComplianceCheck:
        """Check for regular income credits."""
        rule = self.rules["income_regularity_threshold"]

        if not monthly_summaries:
            return ComplianceCheck(
                rule_name="income_regularity_threshold",
                rule_description=rule["description"],
                passed=False,
                actual_value="N/A",
                threshold=f"{rule['threshold']*100:.0f}%",
                severity=rule["severity"]
            )

        months_with_salary = sum(
            1 for s in monthly_summaries if s.salary_credit is not None
        )
        regularity = months_with_salary / len(monthly_summaries)
        passed = regularity >= rule["threshold"]

        return ComplianceCheck(
            rule_name="income_regularity_threshold",
            rule_description=rule["description"],
            passed=passed,
            actual_value=f"{regularity*100:.0f}% ({months_with_salary}/{len(monthly_summaries)} months)",
            threshold=f"{rule['threshold']*100:.0f}%",
            severity=rule["severity"]
        )

    def _check_closing_balance(self, extracted_data: ExtractedData) -> ComplianceCheck:
        """Check minimum closing balance."""
        rule = self.rules["min_closing_balance"]
        closing_balance = extracted_data.closing_balance
        passed = closing_balance >= rule["threshold"]

        return ComplianceCheck(
            rule_name="min_closing_balance",
            rule_description=rule["description"],
            passed=passed,
            actual_value=f"₹{closing_balance:,.2f}",
            threshold=f"₹{rule['threshold']:,}",
            severity=rule["severity"]
        )

    def _check_overdraft(self, extracted_data: ExtractedData) -> ComplianceCheck:
        """Check for overdraft instances."""
        rule = self.rules["max_overdraft_instances"]

        # Count transactions where balance went negative
        overdraft_count = sum(
            1 for txn in extracted_data.transactions
            if txn.balance is not None and txn.balance < 0
        )

        passed = overdraft_count <= rule["threshold"]

        return ComplianceCheck(
            rule_name="max_overdraft_instances",
            rule_description=rule["description"],
            passed=passed,
            actual_value=str(overdraft_count),
            threshold=str(rule["threshold"]),
            severity=rule["severity"]
        )
