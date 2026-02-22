"""PDF → Markdown 폴백 변환 모듈.

arXiv HTML이 없는 구형 논문을 위해 Docling을 사용하여 PDF를 변환한다.
docling이 설치되지 않은 경우 안내 메시지를 출력한다.
"""

from __future__ import annotations

import tempfile
from pathlib import Path


def is_docling_available() -> bool:
    """Docling이 설치되어 있는지 확인한다."""
    try:
        import docling  # noqa: F401

        return True
    except ImportError:
        return False


def convert_pdf_to_markdown(pdf_bytes: bytes) -> str:
    """PDF 바이트를 마크다운으로 변환한다.

    Args:
        pdf_bytes: PDF 파일 바이트

    Returns:
        변환된 마크다운 문자열

    Raises:
        ImportError: Docling이 설치되지 않은 경우
    """
    if not is_docling_available():
        raise ImportError(
            "PDF 변환에는 docling이 필요합니다.\n"
            "설치: pip install arxiv-to-md[pdf]"
        )

    from docling.document_converter import DocumentConverter

    # PDF를 임시 파일로 저장
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(pdf_bytes)
        tmp_path = Path(f.name)

    try:
        converter = DocumentConverter()
        result = converter.convert(str(tmp_path))
        return result.document.export_to_markdown()
    finally:
        tmp_path.unlink(missing_ok=True)
