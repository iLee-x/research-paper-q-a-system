"""PDF processing utilities for extracting text from research papers."""

import os
from pathlib import Path
from typing import List
import httpx
from pypdf import PdfReader
from loguru import logger


class PDFProcessor:
    """Process PDF documents and extract text content."""

    def __init__(self, pdf_path: str):
        """Initialize PDF processor with path to PDF file.

        Args:
            pdf_path: Path to the PDF file to process
        """
        self.pdf_path = Path(pdf_path)
        self.text_content: str = ""

    @staticmethod
    async def download_paper(url: str, save_path: str) -> Path:
        """Download a research paper from a URL.

        Args:
            url: URL of the PDF to download
            save_path: Path where the PDF should be saved

        Returns:
            Path to the downloaded PDF file
        """
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        if save_path.exists():
            logger.info(f"PDF already exists at {save_path}")
            return save_path

        logger.info(f"Downloading PDF from {url}")
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()

            with open(save_path, 'wb') as f:
                f.write(response.content)

        logger.info(f"PDF downloaded successfully to {save_path}")
        return save_path

    def extract_text(self) -> str:
        """Extract text content from the PDF.

        Returns:
            Extracted text from all pages
        """
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {self.pdf_path}")

        logger.info(f"Extracting text from {self.pdf_path}")

        reader = PdfReader(str(self.pdf_path))
        text_parts = []

        for page_num, page in enumerate(reader.pages, 1):
            text = page.extract_text()
            if text.strip():
                text_parts.append(text)
                logger.debug(f"Extracted text from page {page_num}")

        self.text_content = "\n\n".join(text_parts)
        logger.info(f"Successfully extracted {len(self.text_content)} characters from {len(reader.pages)} pages")

        return self.text_content

    def get_text(self) -> str:
        """Get the extracted text content.

        Returns:
            Extracted text content
        """
        if not self.text_content:
            self.extract_text()
        return self.text_content


async def download_attention_paper(data_dir: str = "./data") -> Path:
    """Download the 'Attention Is All You Need' paper from arXiv.

    Args:
        data_dir: Directory to save the PDF

    Returns:
        Path to the downloaded PDF
    """
    arxiv_url = "https://arxiv.org/pdf/1706.03762.pdf"
    save_path = Path(data_dir) / "attention_is_all_you_need.pdf"

    return await PDFProcessor.download_paper(arxiv_url, str(save_path))
