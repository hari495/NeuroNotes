"""
File Parser Utility.

This module provides functions to parse various file formats and extract text content.
Supports: .txt, .md, .pdf
"""

import io
from pathlib import Path
from typing import Dict, Any

from PyPDF2 import PdfReader
from fastapi import UploadFile


# Supported file extensions
SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}


class FileParseError(Exception):
    """Exception raised when file parsing fails."""

    pass


async def parse_text_file(file_content: bytes, encoding: str = "utf-8") -> str:
    """
    Parse a text file (.txt or .md).

    Args:
        file_content: Raw bytes from the file.
        encoding: Text encoding (default: utf-8).

    Returns:
        Extracted text content.

    Raises:
        FileParseError: If parsing fails.
    """
    try:
        text = file_content.decode(encoding)
        return text.strip()
    except UnicodeDecodeError:
        # Try with a different encoding
        try:
            text = file_content.decode("latin-1")
            return text.strip()
        except Exception as e:
            raise FileParseError(f"Failed to decode text file: {e}")
    except Exception as e:
        raise FileParseError(f"Failed to parse text file: {e}")


def clean_pdf_artifacts(text: str) -> str:
    """
    Clean common PDF encoding artifacts from extracted text.

    This function fixes malformed mathematical symbols and characters that
    are often garbled during PDF text extraction.

    Args:
        text: Raw text extracted from PDF.

    Returns:
        Cleaned text with artifacts removed or replaced.
    """
    import re

    # Common PDF artifacts to clean
    replacements = [
        # Remove or clean vector notation artifacts
        (r'#\s*»\s*', ''),  # Remove "# »" (common before vectors)
        (r'#»', ''),         # Remove "#»"
        (r'»\s+', ''),       # Remove "» " followed by space
        (r'\s+»', ''),       # Remove " »"
        (r'#\s+', ''),       # Remove "# " when standalone

        # Clean up excessive whitespace around common characters
        (r'\s*∈\s*', ' ∈ '),
        (r'\s*∞\s*', ' ∞ '),
        (r'\s*≤\s*', ' ≤ '),
        (r'\s*≥\s*', ' ≥ '),
        (r'\s*×\s*', ' × '),

        # Fix common spacing issues in math expressions
        (r'(\w)\s+([₀₁₂₃₄₅₆₇₈₉])', r'\1\2'),  # Remove space before subscripts
        (r'(\w)\s+([⁰¹²³⁴⁵⁶⁷⁸⁹])', r'\1\2'),  # Remove space before superscripts

        # Clean up multiple spaces
        (r'\s{3,}', '  '),  # Replace 3+ spaces with double space
        (r'\n{4,}', '\n\n\n'),  # Replace 4+ newlines with triple newline
    ]

    cleaned_text = text
    for pattern, replacement in replacements:
        cleaned_text = re.sub(pattern, replacement, cleaned_text)

    return cleaned_text.strip()


async def parse_pdf_file(file_content: bytes) -> str:
    """
    Parse a PDF file and extract text.

    Args:
        file_content: Raw bytes from the PDF file.

    Returns:
        Extracted text content from all pages, cleaned of common PDF artifacts.

    Raises:
        FileParseError: If parsing fails.
    """
    try:
        # Create a file-like object from bytes
        pdf_file = io.BytesIO(file_content)

        # Read PDF
        reader = PdfReader(pdf_file)

        # Extract text from all pages
        text_parts = []
        for page_num, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text()
                if page_text.strip():
                    # Clean PDF artifacts from each page
                    cleaned_page = clean_pdf_artifacts(page_text)
                    text_parts.append(cleaned_page)
            except Exception as e:
                # Log warning but continue with other pages
                print(f"Warning: Could not extract text from page {page_num}: {e}")

        if not text_parts:
            raise FileParseError("No text could be extracted from PDF")

        # Join all pages with double newline
        full_text = "\n\n".join(text_parts)
        return full_text.strip()

    except FileParseError:
        raise
    except Exception as e:
        raise FileParseError(f"Failed to parse PDF file: {e}")


async def parse_uploaded_file(upload_file: UploadFile) -> Dict[str, Any]:
    """
    Parse an uploaded file and extract text content.

    This is the main entry point for file parsing. It determines the file type
    and calls the appropriate parser.

    Args:
        upload_file: FastAPI UploadFile object.

    Returns:
        Dictionary containing:
        - text: Extracted text content
        - filename: Original filename
        - file_type: File extension
        - size: File size in bytes

    Raises:
        FileParseError: If the file type is not supported or parsing fails.
    """
    # Get file extension
    filename = upload_file.filename or "unknown"
    file_ext = Path(filename).suffix.lower()

    # Check if file type is supported
    if file_ext not in SUPPORTED_EXTENSIONS:
        raise FileParseError(
            f"Unsupported file type: {file_ext}. "
            f"Supported types: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    # Read file content
    try:
        file_content = await upload_file.read()
        file_size = len(file_content)
    except Exception as e:
        raise FileParseError(f"Failed to read uploaded file: {e}")

    # Parse based on file type
    try:
        if file_ext in [".txt", ".md"]:
            text = await parse_text_file(file_content)
        elif file_ext == ".pdf":
            text = await parse_pdf_file(file_content)
        else:
            raise FileParseError(f"Unsupported file type: {file_ext}")

        # Validate that we got some text
        if not text or len(text.strip()) < 10:
            raise FileParseError(
                "File appears to be empty or contains too little text"
            )

        return {
            "text": text,
            "filename": filename,
            "file_type": file_ext,
            "size": file_size,
        }

    except FileParseError:
        raise
    except Exception as e:
        raise FileParseError(f"Unexpected error parsing {file_ext} file: {e}")


async def parse_multiple_files(upload_files: list[UploadFile]) -> list[Dict[str, Any]]:
    """
    Parse multiple uploaded files.

    Args:
        upload_files: List of FastAPI UploadFile objects.

    Returns:
        List of parsed file dictionaries (see parse_uploaded_file for structure).

    Raises:
        FileParseError: If any file fails to parse (will include filename in error).
    """
    results = []
    errors = []

    for upload_file in upload_files:
        try:
            result = await parse_uploaded_file(upload_file)
            results.append(result)
        except FileParseError as e:
            errors.append(f"{upload_file.filename}: {str(e)}")
        except Exception as e:
            errors.append(f"{upload_file.filename}: Unexpected error - {str(e)}")

    # If any errors occurred, raise them
    if errors:
        error_msg = "Failed to parse some files:\n" + "\n".join(errors)
        raise FileParseError(error_msg)

    return results


def get_file_info(upload_file: UploadFile) -> Dict[str, str]:
    """
    Get basic information about an uploaded file without parsing it.

    Args:
        upload_file: FastAPI UploadFile object.

    Returns:
        Dictionary with filename, extension, and content type.
    """
    filename = upload_file.filename or "unknown"
    file_ext = Path(filename).suffix.lower()
    content_type = upload_file.content_type or "unknown"

    return {
        "filename": filename,
        "extension": file_ext,
        "content_type": content_type,
        "is_supported": file_ext in SUPPORTED_EXTENSIONS,
    }
