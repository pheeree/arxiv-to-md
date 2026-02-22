"""arXiv HTML → Markdown 변환 모듈.

arXiv HTML5 포맷을 파싱하여 깔끔한 마크다운으로 변환한다.
수식(MathML/LaTeX), 테이블, 이미지, 참고문헌 등을 처리한다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup, NavigableString, Tag


@dataclass
class ParseOptions:
    """HTML 파싱 옵션."""

    remove_refs: bool = False
    remove_toc: bool = False
    remove_appendix: bool = False
    include_sections: list[str] | None = None  # None이면 전체 포함


@dataclass
class ParsedPaper:
    """파싱 결과."""

    title: str = ""
    authors: list[str] = field(default_factory=list)
    abstract: str = ""
    sections: list[Section] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class Section:
    """논문 섹션."""

    title: str
    level: int  # 1 = h1, 2 = h2, ...
    content: str
    subsections: list[Section] = field(default_factory=list)


class ArxivHTMLParser:
    """arXiv HTML5 논문을 파싱하는 파서."""

    def __init__(self, options: ParseOptions | None = None):
        self.options = options or ParseOptions()

    def parse(self, html_content: str) -> ParsedPaper:
        """HTML 콘텐츠를 ParsedPaper로 변환한다."""
        soup = BeautifulSoup(html_content, "lxml")
        paper = ParsedPaper()

        # 제목 추출
        paper.title = self._extract_title(soup)

        # 저자 추출
        paper.authors = self._extract_authors(soup)

        # 초록 추출
        paper.abstract = self._extract_abstract(soup)

        # 본문 섹션 추출
        paper.sections = self._extract_sections(soup)

        return paper

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """논문 제목을 추출한다."""
        # arXiv HTML의 제목은 보통 <h1 class="ltx_title"> 안에 있음
        title_el = soup.find("h1", class_="ltx_title")
        if title_el:
            # "Title:" 접두사 제거
            text = self._element_to_text(title_el)
            text = re.sub(r"^Title:\s*", "", text, flags=re.IGNORECASE)
            return text.strip()

        # 폴백: <title> 태그
        title_el = soup.find("title")
        if title_el:
            return title_el.get_text(strip=True)

        return "Untitled"

    def _extract_authors(self, soup: BeautifulSoup) -> list[str]:
        """저자 목록을 추출한다."""
        authors = []

        # arXiv HTML: <span class="ltx_personname">
        for author_el in soup.find_all("span", class_="ltx_personname"):
            name = author_el.get_text(strip=True)
            if name:
                authors.append(name)

        return authors

    def _extract_abstract(self, soup: BeautifulSoup) -> str:
        """초록을 추출한다."""
        abstract_el = soup.find("div", class_="ltx_abstract")
        if abstract_el:
            # "Abstract" 제목 제거
            title_in_abstract = abstract_el.find(["h2", "h6", "p"], class_="ltx_title")
            if title_in_abstract:
                title_in_abstract.decompose()
            return self._element_to_markdown(abstract_el).strip()
        return ""

    def _extract_sections(self, soup: BeautifulSoup) -> list[Section]:
        """본문 섹션들을 추출한다."""
        sections = []

        # arXiv HTML: <section class="ltx_section">
        for section_el in soup.find_all("section", class_=re.compile(r"ltx_section|ltx_appendix")):
            section = self._parse_section(section_el, level=2)
            if section is None:
                continue

            # 옵션에 따라 필터링
            section_title_lower = section.title.lower().strip()

            if self.options.remove_refs and "reference" in section_title_lower:
                continue
            if self.options.remove_appendix and "appendix" in section_title_lower:
                continue
            if self.options.include_sections is not None:
                if not any(
                    inc.lower() in section_title_lower
                    for inc in self.options.include_sections
                ):
                    continue

            sections.append(section)

        return sections

    def _parse_section(self, element: Tag, level: int) -> Section | None:
        """단일 섹션을 파싱한다."""
        # 제목 찾기
        heading = element.find(re.compile(r"^h[1-6]$"), class_="ltx_title")
        title = ""
        if heading:
            title = self._element_to_text(heading).strip()
            # 섹션 번호 제거 (예: "1 Introduction" → "Introduction")
            title = re.sub(r"^[\d.]+\s*", "", title)
            title = re.sub(r"^(?:Appendix\s+)?[A-Z]\s+", "", title)

        if not title:
            return None

        # 서브섹션 추출 (재귀)
        subsections = []
        for sub_el in element.find_all(
            "section", class_=re.compile(r"ltx_subsection|ltx_subsubsection"), recursive=False
        ):
            sub = self._parse_section(sub_el, level=level + 1)
            if sub:
                subsections.append(sub)

        # 본문 콘텐츠 (서브섹션과 제목 제외)
        content_parts = []
        for child in element.children:
            if isinstance(child, NavigableString):
                text = str(child).strip()
                if text:
                    content_parts.append(text)
            elif isinstance(child, Tag):
                # 서브섹션과 제목은 건너뛰기
                if child.name == "section":
                    continue
                if child.name and re.match(r"^h[1-6]$", child.name) and "ltx_title" in (
                    child.get("class") or []
                ):
                    continue
                content_parts.append(self._element_to_markdown(child))

        content = "\n\n".join(part for part in content_parts if part.strip())

        return Section(
            title=title,
            level=level,
            content=content,
            subsections=subsections,
        )

    def _element_to_markdown(self, element: Tag) -> str:
        """HTML 요소를 마크다운 텍스트로 변환한다."""
        if element is None:
            return ""

        parts = []
        for child in element.children:
            if isinstance(child, NavigableString):
                parts.append(str(child))
            elif isinstance(child, Tag):
                parts.append(self._tag_to_markdown(child))

        return "".join(parts).strip()

    def _tag_to_markdown(self, tag: Tag) -> str:
        """HTML 태그를 마크다운으로 변환한다."""
        tag_name = tag.name
        classes = tag.get("class") or []

        # 수식 처리
        if tag_name == "math" or "ltx_Math" in classes or "ltx_equation" in classes:
            return self._convert_math(tag)

        # 강조
        if tag_name in ("em", "i") or "ltx_emph" in classes:
            inner = self._element_to_markdown(tag)
            return f"*{inner}*" if inner else ""

        if tag_name in ("strong", "b") or "ltx_font_bold" in classes:
            inner = self._element_to_markdown(tag)
            return f"**{inner}**" if inner else ""

        # 코드
        if tag_name == "code" or "ltx_lstlisting" in classes:
            inner = tag.get_text()
            return f"`{inner}`"

        # 링크
        if tag_name == "a":
            href = tag.get("href", "")
            text = self._element_to_markdown(tag)
            if href and text:
                return f"[{text}]({href})"
            return text

        # 이미지
        if tag_name == "img":
            src = tag.get("src", "")
            alt = tag.get("alt", "image")
            return f"![{alt}]({src})"

        # 리스트
        if tag_name in ("ul", "ol"):
            return self._convert_list(tag)

        # 테이블
        if tag_name == "table" or "ltx_tabular" in classes:
            return self._convert_table(tag)

        # 단락
        if tag_name == "p":
            inner = self._element_to_markdown(tag)
            return f"\n\n{inner}\n\n" if inner else ""

        # figure
        if tag_name == "figure" or "ltx_figure" in classes:
            return self._convert_figure(tag)

        # 기본: 재귀적으로 내부 변환
        return self._element_to_markdown(tag)

    def _convert_math(self, tag: Tag) -> str:
        """수식을 LaTeX 문자열로 변환한다."""
        # alttext 속성이 있으면 사용 (arXiv HTML에서 보통 LaTeX 소스)
        alttext = tag.get("alttext", "")
        if alttext:
            # 디스플레이 수식인지 인라인인지 판별
            if tag.get("display") == "block" or "ltx_equation" in (tag.get("class") or []):
                return f"\n\n$$\n{alttext}\n$$\n\n"
            return f"${alttext}$"

        # annotation 태그에서 LaTeX 추출
        annotation = tag.find("annotation", encoding="application/x-tex")
        if annotation:
            tex = annotation.get_text(strip=True)
            if tag.get("display") == "block":
                return f"\n\n$$\n{tex}\n$$\n\n"
            return f"${tex}$"

        # 폴백: 텍스트만 추출
        text = tag.get_text(strip=True)
        return f"${text}$" if text else ""

    def _convert_list(self, tag: Tag) -> str:
        """리스트를 마크다운으로 변환한다."""
        items = []
        is_ordered = tag.name == "ol"

        for i, li in enumerate(tag.find_all("li", recursive=False), start=1):
            content = self._element_to_markdown(li).strip()
            prefix = f"{i}." if is_ordered else "-"
            items.append(f"{prefix} {content}")

        return "\n".join(items)

    def _convert_table(self, tag: Tag) -> str:
        """테이블을 마크다운 테이블로 변환한다."""
        rows = []

        # thead와 tbody의 tr을 모두 찾기
        for tr in tag.find_all("tr"):
            cells = []
            for td in tr.find_all(["td", "th"]):
                cell_text = self._element_to_markdown(td).strip().replace("\n", " ")
                cells.append(cell_text)
            if cells:
                rows.append(cells)

        if not rows:
            return ""

        # 마크다운 테이블 생성
        max_cols = max(len(row) for row in rows)
        # 모든 행을 같은 컬럼 수로 패딩
        for row in rows:
            while len(row) < max_cols:
                row.append("")

        lines = []
        # 헤더 행
        lines.append("| " + " | ".join(rows[0]) + " |")
        lines.append("| " + " | ".join(["---"] * max_cols) + " |")
        # 데이터 행
        for row in rows[1:]:
            lines.append("| " + " | ".join(row) + " |")

        return "\n".join(lines)

    def _convert_figure(self, tag: Tag) -> str:
        """figure를 마크다운으로 변환한다."""
        parts = []

        # 이미지
        img = tag.find("img")
        if img:
            src = img.get("src", "")
            alt = img.get("alt", "Figure")
            parts.append(f"![{alt}]({src})")

        # 캡션
        caption = tag.find("figcaption")
        if caption:
            caption_text = self._element_to_markdown(caption).strip()
            if caption_text:
                parts.append(f"*{caption_text}*")

        return "\n\n".join(parts)

    def _element_to_text(self, element: Tag) -> str:
        """요소의 순수 텍스트를 추출한다 (수식은 LaTeX로)."""
        parts = []
        for child in element.children:
            if isinstance(child, NavigableString):
                parts.append(str(child))
            elif isinstance(child, Tag):
                if child.name == "math" or "ltx_Math" in (child.get("class") or []):
                    parts.append(self._convert_math(child))
                else:
                    parts.append(self._element_to_text(child))
        return "".join(parts)
