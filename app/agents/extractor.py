"""
Agent 2: Data Extractor
Extracts structured data from bank statements.
"""

import logging
from typing import Dict, Any, List
from collections import defaultdict
from langchain_core.prompts import ChatPromptTemplate

from app.orchestrator.state import (
    ExtractedData,
    Transaction,
    TransactionSummary,
    LoanProcessorState
)
from app.utils.llm_factory import create_llm, LLMProvider

logger = logging.getLogger(__name__)

EXTRACTOR_PROMPT = """You are a financial document extraction expert for Indian bank statements.
Extract all relevant information from this bank statement.

Extract the following fields precisely:

1. **Account Information**:
   - account_holder_name: Full name of account holder
   - bank_name: Name of the bank (e.g., "HDFC Bank", "ICICI Bank", "SBI")
   - branch: Branch name if available, otherwise null
   - account_number_masked: Mask all but last 4 digits (e.g., "XXXX1234")
   - account_type: "Savings" or "Current"

2. **Statement Period**:
   - statement_period_start: Start date (YYYY-MM-DD format)
   - statement_period_end: End date (YYYY-MM-DD format)

3. **Balance Information**:
   - opening_balance: Opening balance amount (number)
   - closing_balance: Closing balance amount (number)
   - total_credits: Total credit amount (number)
   - total_debits: Total debit amount (number)

4. **transaction_count**: Total number of transactions found

5. **transactions**: Extract EVERY transaction with:
   - date: Transaction date in YYYY-MM-DD format
   - description: Full transaction description
   - amount: Amount as a positive number
   - type: "credit" or "debit"
   - balance: Running balance after transaction (null if not available)

Bank Statement Text:
{document_text}

Tables Extracted:
{tables}
"""


class DataExtractorAgent:
    """Agent responsible for extracting structured data from bank statements."""

    def __init__(self, provider: LLMProvider = "ollama", model_name: str = None):
        self.llm = create_llm(provider=provider, model_name=model_name, max_tokens=4096)
        self.structured_llm = self.llm.with_structured_output(ExtractedData)
        self.prompt = ChatPromptTemplate.from_template(EXTRACTOR_PROMPT)

    def extract(self, state: LoanProcessorState) -> Dict[str, Any]:
        """Extract structured data from the document."""
        document_text = state.get("raw_text", "")
        tables = state.get("tables", [])

        chain = self.prompt | self.structured_llm

        try:
            result = chain.invoke({
                "document_text": document_text,
                "tables": str(tables)
            })

            monthly_summaries = self._calculate_monthly_summaries(result.transactions)

            logger.info(f"Extraction: {result.transaction_count} transactions, "
                       f"{len(monthly_summaries)} months")

            return {
                "extracted_data": result,
                "monthly_summaries": monthly_summaries,
                "current_agent": "extractor",
                "error": None
            }
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return {
                "extracted_data": None,
                "monthly_summaries": [],
                "current_agent": "extractor",
                "error": f"Extraction failed: {str(e)}"
            }

    def _calculate_monthly_summaries(
        self,
        transactions: List[Transaction]
    ) -> List[TransactionSummary]:
        """Calculate monthly transaction summaries."""
        monthly_data = defaultdict(lambda: {
            "credits": 0.0, "debits": 0.0, "balances": [], "salary": None
        })

        for txn in transactions:
            try:
                month = txn.date[:7]  # Get YYYY-MM
            except (IndexError, TypeError):
                continue

            if txn.type == "credit":
                monthly_data[month]["credits"] += txn.amount
                if self._is_salary(txn):
                    monthly_data[month]["salary"] = txn.amount
            else:
                monthly_data[month]["debits"] += txn.amount

            if txn.balance:
                monthly_data[month]["balances"].append(txn.balance)

        summaries = []
        for month, data in sorted(monthly_data.items()):
            avg_balance = (
                sum(data["balances"]) / len(data["balances"])
                if data["balances"] else 0.0
            )
            summaries.append(TransactionSummary(
                month=month,
                total_credits=data["credits"],
                total_debits=data["debits"],
                net_flow=data["credits"] - data["debits"],
                avg_balance=avg_balance,
                salary_credit=data["salary"]
            ))

        return summaries

    def _is_salary(self, txn: Transaction) -> bool:
        """Detect if a transaction is likely a salary credit."""
        salary_keywords = [
            "salary", "sal", "payroll", "wages", "neft",
            "compensation", "pay", "income"
        ]
        description_lower = txn.description.lower()
        return (
            txn.type == "credit"
            and txn.amount > 10000
            and any(kw in description_lower for kw in salary_keywords)
        )

    def __call__(self, state: LoanProcessorState) -> Dict[str, Any]:
        """Make the agent callable for LangGraph integration."""
        return self.extract(state)
