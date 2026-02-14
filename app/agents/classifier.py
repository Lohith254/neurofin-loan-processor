"""
Agent 1: Document Classifier
Classifies document type and assesses quality.
"""

import logging
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate

from app.orchestrator.state import ClassificationResult, DocumentType, LoanProcessorState
from app.utils.llm_factory import create_llm, LLMProvider

logger = logging.getLogger(__name__)

CLASSIFIER_PROMPT = """You are a document classification expert for an Indian loan processing system.
Analyze the provided document text and determine:

1. **Document Type**: Classify as one of:
   - bank_statement: Monthly bank account statements
   - kyc: Identity documents (Aadhaar, PAN, Passport)
   - income_proof: Salary slips, ITR, Form 16
   - property_doc: Property papers, registration documents
   - other: Any other document type

2. **Quality Assessment** (score 0-10):
   - 10: Perfect quality, all text readable, complete document
   - 7-9: Good quality, minor issues
   - 4-6: Moderate quality, some sections unclear
   - 1-3: Poor quality, significant portions unreadable
   - 0: Completely unreadable

3. **Readability**: Can the text be read and processed?

4. **Completeness**: Does the document appear complete (no missing pages, cut-off text)?

5. **Issues**: List any specific problems found. Use empty list if none.

6. **Can Proceed**: Based on quality and completeness, can we proceed with extraction?
   Set to true if quality_score >= 5 and is_readable is true and document_type is bank_statement.

Document Text (first 10,000 characters):
{document_text}
"""


class DocumentClassifierAgent:
    """Agent responsible for classifying loan documents and assessing quality."""

    def __init__(self, provider: LLMProvider = "ollama", model_name: str = None):
        self.llm = create_llm(provider=provider, model_name=model_name, max_tokens=1024)
        self.structured_llm = self.llm.with_structured_output(ClassificationResult)
        self.prompt = ChatPromptTemplate.from_template(CLASSIFIER_PROMPT)

    def classify(self, state: LoanProcessorState) -> Dict[str, Any]:
        """Classify the document and assess its quality."""
        document_text = state.get("raw_text", "")

        if not document_text:
            return {
                "classification": ClassificationResult(
                    document_type=DocumentType.OTHER,
                    quality_score=0.0,
                    is_readable=False,
                    is_complete=False,
                    issues=["No text extracted from document"],
                    can_proceed=False
                ),
                "current_agent": "classifier",
                "error": "No text extracted from document"
            }

        chain = self.prompt | self.structured_llm

        try:
            result = chain.invoke({
                "document_text": document_text[:10000]
            })

            logger.info(f"Classification: type={result.document_type.value}, quality={result.quality_score}")

            return {
                "classification": result,
                "current_agent": "classifier",
                "error": None
            }
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return {
                "classification": ClassificationResult(
                    document_type=DocumentType.OTHER,
                    quality_score=0.0,
                    is_readable=False,
                    is_complete=False,
                    issues=[f"LLM classification failed: {str(e)}"],
                    can_proceed=False
                ),
                "current_agent": "classifier",
                "error": f"Classification failed: {str(e)}"
            }

    def __call__(self, state: LoanProcessorState) -> Dict[str, Any]:
        """Make the agent callable for LangGraph integration."""
        return self.classify(state)
