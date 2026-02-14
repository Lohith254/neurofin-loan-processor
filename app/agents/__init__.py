"""
Agent modules for the Multi-Agent Loan Processor.
Each agent specializes in a specific task in the pipeline.
Import agents directly when needed to avoid eager dependency loading.
"""

__all__ = ["DocumentClassifierAgent", "DataExtractorAgent", "ValidatorAgent"]
