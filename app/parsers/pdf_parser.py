"""
PDF Parser Module
Extracts text and tables from PDF documents.
"""

import os
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass


@dataclass
class ParsedPDF:
    """Container for parsed PDF data."""
    raw_text: str
    pages: List[str]
    tables: List[Dict[str, Any]]
    page_count: int
    metadata: Dict[str, Any]


class PDFParser:
    """Handles PDF text and table extraction using PyMuPDF and pdfplumber."""

    def __init__(self):
        """Initialize the PDF parser."""
        self._check_dependencies()

    def _check_dependencies(self):
        """Verify required libraries are available."""
        try:
            import fitz  # PyMuPDF
            import pdfplumber
        except ImportError as e:
            raise ImportError(
                f"Required PDF library not found: {e}. "
                "Please install with: pip install pymupdf pdfplumber"
            )

    def parse(self, file_path: str) -> ParsedPDF:
        """Parse a PDF file and extract text and tables.

        Args:
            file_path: Path to the PDF file.

        Returns:
            ParsedPDF object with extracted content.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the file is not a valid PDF.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        if not file_path.lower().endswith('.pdf'):
            raise ValueError(f"File is not a PDF: {file_path}")

        # Extract text using PyMuPDF
        raw_text, pages, metadata = self._extract_text_pymupdf(file_path)

        # Extract tables using pdfplumber
        tables = self._extract_tables_pdfplumber(file_path)

        return ParsedPDF(
            raw_text=raw_text,
            pages=pages,
            tables=tables,
            page_count=len(pages),
            metadata=metadata
        )

    def _extract_text_pymupdf(
        self,
        file_path: str
    ) -> Tuple[str, List[str], Dict[str, Any]]:
        """Extract text from PDF using PyMuPDF.

        Args:
            file_path: Path to the PDF file.

        Returns:
            Tuple of (full_text, page_texts, metadata).
        """
        import fitz

        doc = fitz.open(file_path)
        pages = []
        full_text_parts = []
        metadata = doc.metadata or {}

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            pages.append(text)
            full_text_parts.append(f"--- Page {page_num + 1} ---\n{text}")

        doc.close()

        return "\n\n".join(full_text_parts), pages, metadata

    def _extract_tables_pdfplumber(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract tables from PDF using pdfplumber.

        Args:
            file_path: Path to the PDF file.

        Returns:
            List of table dictionaries with headers and rows.
        """
        import pdfplumber

        tables = []

        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_tables = page.extract_tables()

                for table_idx, table in enumerate(page_tables):
                    if not table or len(table) < 2:
                        continue

                    # First row as headers
                    headers = [
                        str(cell).strip() if cell else f"col_{i}"
                        for i, cell in enumerate(table[0])
                    ]

                    # Remaining rows as data
                    rows = []
                    for row in table[1:]:
                        row_dict = {}
                        for i, cell in enumerate(row):
                            if i < len(headers):
                                row_dict[headers[i]] = str(cell).strip() if cell else ""
                        rows.append(row_dict)

                    tables.append({
                        "page": page_num + 1,
                        "table_index": table_idx,
                        "headers": headers,
                        "rows": rows,
                        "row_count": len(rows)
                    })

        return tables

    def extract_text_only(self, file_path: str) -> str:
        """Quick text-only extraction.

        Args:
            file_path: Path to the PDF file.

        Returns:
            Extracted text as string.
        """
        result = self.parse(file_path)
        return result.raw_text

    def extract_tables_only(self, file_path: str) -> List[Dict[str, Any]]:
        """Quick table-only extraction.

        Args:
            file_path: Path to the PDF file.

        Returns:
            List of extracted tables.
        """
        result = self.parse(file_path)
        return result.tables
