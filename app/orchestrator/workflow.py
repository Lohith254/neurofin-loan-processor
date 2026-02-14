"""
LangGraph Workflow Orchestrator
Coordinates the multi-agent loan processing pipeline.
"""

import os
import time
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END

from app.orchestrator.state import (
    LoanProcessorState,
    ProcessingResult,
    DocumentType,
    Recommendation,
    create_initial_state
)
from app.agents.classifier import DocumentClassifierAgent
from app.agents.extractor import DataExtractorAgent
from app.agents.validator import ValidatorAgent
from app.parsers.pdf_parser import PDFParser
from app.utils.llm_factory import LLMProvider, detect_provider

# Load environment variables
load_dotenv()


class LoanProcessor:
    """Main orchestrator for the loan document processing pipeline."""

    def __init__(self, provider: LLMProvider = None, model_name: str = None):
        """Initialize the loan processor.

        Args:
            provider: LLM provider - "ollama" (free, local) or "claude" (paid, cloud).
                      Auto-detected if not specified.
            model_name: Model name override. Defaults per provider.
        """
        self.provider = provider or detect_provider()
        self.model_name = model_name
        self.pdf_parser = PDFParser()

        # Initialize agents with provider
        self.classifier = DocumentClassifierAgent(provider=self.provider, model_name=model_name)
        self.extractor = DataExtractorAgent(provider=self.provider, model_name=model_name)
        self.validator = ValidatorAgent(provider=self.provider, model_name=model_name)

        # Build the workflow graph
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph state machine.

        Returns:
            Compiled StateGraph workflow.
        """
        # Create the graph with our state schema
        workflow = StateGraph(LoanProcessorState)

        # Add nodes for each processing step
        workflow.add_node("parse_pdf", self._parse_pdf_node)
        workflow.add_node("classify", self.classifier)
        workflow.add_node("extract", self.extractor)
        workflow.add_node("validate", self.validator)

        # Define the workflow edges
        workflow.set_entry_point("parse_pdf")

        # PDF parsing always goes to classification
        workflow.add_edge("parse_pdf", "classify")

        # After classification, decide whether to proceed
        workflow.add_conditional_edges(
            "classify",
            self._should_proceed,
            {
                "proceed": "extract",
                "stop": END
            }
        )

        # After extraction, always validate
        workflow.add_edge("extract", "validate")

        # After validation, we're done
        workflow.add_edge("validate", END)

        return workflow.compile()

    def _parse_pdf_node(self, state: LoanProcessorState) -> Dict[str, Any]:
        """Parse the PDF document and extract text/tables.

        Args:
            state: Current pipeline state.

        Returns:
            Updated state with parsed content.
        """
        file_path = state.get("file_path", "")

        try:
            parsed = self.pdf_parser.parse(file_path)
            return {
                "raw_text": parsed.raw_text,
                "pages": parsed.pages,
                "tables": parsed.tables,
                "current_agent": "parser",
                "error": None
            }
        except Exception as e:
            return {
                "raw_text": "",
                "pages": [],
                "tables": [],
                "current_agent": "parser",
                "error": f"PDF parsing failed: {str(e)}"
            }

    def _should_proceed(self, state: LoanProcessorState) -> str:
        """Decide whether to proceed with extraction based on classification.

        Args:
            state: Current pipeline state.

        Returns:
            "proceed" or "stop" based on classification results.
        """
        classification = state.get("classification")

        if not classification:
            return "stop"

        if not classification.can_proceed:
            return "stop"

        # Only proceed with bank statements for now
        if classification.document_type != DocumentType.BANK_STATEMENT:
            return "stop"

        return "proceed"

    def process(self, file_path: str) -> ProcessingResult:
        """Process a loan document through the full pipeline.

        Args:
            file_path: Path to the PDF document.

        Returns:
            ProcessingResult with all extracted data and assessments.
        """
        start_time = time.time()

        # Create initial state
        initial_state = create_initial_state(file_path)

        # Run the workflow
        try:
            final_state = self.workflow.invoke(initial_state)
            processing_time = time.time() - start_time

            return self._create_result(final_state, processing_time)
        except Exception as e:
            processing_time = time.time() - start_time
            return ProcessingResult(
                success=False,
                document_type=DocumentType.OTHER,
                quality_score=0.0,
                extracted_data=None,
                monthly_summaries=[],
                risk_score=100,
                recommendation=Recommendation.REJECT,
                compliance_issues=["Processing failed"],
                red_flags=[str(e)],
                processing_time_seconds=processing_time,
                error_message=str(e)
            )

    def _create_result(
        self,
        state: LoanProcessorState,
        processing_time: float
    ) -> ProcessingResult:
        """Create the final processing result from state.

        Args:
            state: Final pipeline state.
            processing_time: Total processing time in seconds.

        Returns:
            ProcessingResult object.
        """
        classification = state.get("classification")
        extracted_data = state.get("extracted_data")
        risk_assessment = state.get("risk_assessment")
        error = state.get("error")

        # Handle case where processing stopped early
        if not classification:
            return ProcessingResult(
                success=False,
                document_type=DocumentType.OTHER,
                quality_score=0.0,
                extracted_data=None,
                monthly_summaries=[],
                risk_score=100,
                recommendation=Recommendation.REJECT,
                compliance_issues=["Classification failed"],
                red_flags=[],
                processing_time_seconds=processing_time,
                error_message=error or "Classification failed"
            )

        if not classification.can_proceed:
            return ProcessingResult(
                success=False,
                document_type=classification.document_type,
                quality_score=classification.quality_score,
                extracted_data=None,
                monthly_summaries=[],
                risk_score=100,
                recommendation=Recommendation.REJECT,
                compliance_issues=classification.issues,
                red_flags=[],
                processing_time_seconds=processing_time,
                error_message="Document quality too low to proceed"
            )

        # Full successful processing
        if risk_assessment:
            return ProcessingResult(
                success=True,
                document_type=classification.document_type,
                quality_score=classification.quality_score,
                extracted_data=extracted_data,
                monthly_summaries=state.get("monthly_summaries", []),
                risk_score=risk_assessment.risk_score,
                recommendation=risk_assessment.recommendation,
                compliance_issues=risk_assessment.issues,
                red_flags=risk_assessment.red_flags,
                processing_time_seconds=processing_time,
                error_message=None
            )

        # Extraction succeeded but validation failed
        return ProcessingResult(
            success=False,
            document_type=classification.document_type,
            quality_score=classification.quality_score,
            extracted_data=extracted_data,
            monthly_summaries=state.get("monthly_summaries", []),
            risk_score=100,
            recommendation=Recommendation.REJECT,
            compliance_issues=["Validation incomplete"],
            red_flags=[],
            processing_time_seconds=processing_time,
            error_message=error or "Validation failed"
        )


# CLI entry point
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Process a loan document")
    parser.add_argument("--input", "-i", required=True, help="Path to PDF file")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    args = parser.parse_args()

    processor = LoanProcessor()  # Auto-detects provider
    result = processor.process(args.input)

    # Convert to JSON
    result_json = result.model_dump_json(indent=2)

    if args.output:
        with open(args.output, "w") as f:
            f.write(result_json)
        print(f"Results saved to: {args.output}")
    else:
        print(result_json)
