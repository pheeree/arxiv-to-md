"""메인 변환 오케스트레이터.

fetcher → parser → markdown writer 파이프라인을 조율한다.
"""

from __future__ import annotations

from .fetcher import PaperSource, SourceType, fetch_paper
from .html_parser import ArxivHTMLParser, ParsedPaper, ParseOptions, Section
from .pdf_parser import convert_pdf_to_markdown


def paper_to_markdown(paper: ParsedPaper) -> str:
    """ParsedPaper를 최종 마크다운 문자열로 변환한다."""
    lines: list[str] = []

    # 제목
    lines.append(f"# {paper.title}")
    lines.append("")

    # 저자
    if paper.authors:
        lines.append(f"**Authors:** {', '.join(paper.authors)}")
        lines.append("")

    # 초록
    if paper.abstract:
        lines.append("## Abstract")
        lines.append("")
        lines.append(paper.abstract)
        lines.append("")

    # 본문 섹션
    for section in paper.sections:
        lines.extend(_render_section(section))

    return "\n".join(lines)


def _render_section(section: Section, depth: int = 0) -> list[str]:
    """섹션을 마크다운 라인 리스트로 렌더링한다."""
    lines: list[str] = []
    heading_prefix = "#" * min(section.level, 6)
    lines.append(f"{heading_prefix} {section.title}")
    lines.append("")

    if section.content:
        # 연속 공백라인 정리
        content = section.content.strip()
        lines.append(content)
        lines.append("")

    for sub in section.subsections:
        lines.extend(_render_section(sub, depth + 1))

    return lines


async def convert(
    arxiv_id_or_url: str,
    *,
    remove_refs: bool = False,
    remove_toc: bool = False,
    remove_appendix: bool = False,
    sections: list[str] | None = None,
) -> str:
    """arXiv 논문을 마크다운으로 변환한다.

    Args:
        arxiv_id_or_url: arXiv ID 또는 URL
        remove_refs: 참고문헌 섹션 제거 여부
        remove_toc: 목차 제거 여부
        remove_appendix: 부록 제거 여부
        sections: 포함할 섹션 이름 리스트 (None이면 전체)

    Returns:
        마크다운 문자열
    """
    # 1. 논문 소스 다운로드
    source: PaperSource = await fetch_paper(arxiv_id_or_url)

    # 2. 소스 타입에 따라 변환
    if source.source_type == SourceType.HTML:
        options = ParseOptions(
            remove_refs=remove_refs,
            remove_toc=remove_toc,
            remove_appendix=remove_appendix,
            include_sections=sections,
        )
        parser = ArxivHTMLParser(options)
        paper = parser.parse(source.content)
        return paper_to_markdown(paper)
    else:
        # PDF 폴백
        return convert_pdf_to_markdown(source.content)
