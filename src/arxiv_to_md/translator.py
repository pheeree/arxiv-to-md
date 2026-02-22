"""마크다운 문서 번역 모듈.

마크다운 구조(수식, 코드 블록, 링크, 이미지)를 보존하면서
텍스트만 번역한다.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass

from deep_translator import GoogleTranslator


@dataclass
class TranslateOptions:
    """번역 옵션."""

    target_lang: str = "ko"
    source_lang: str = "auto"
    chunk_size: int = 4500  # Google Translate 제한 회피


# 보존해야 할 패턴들 (번역하지 않을 부분)
PRESERVE_PATTERNS = [
    # 디스플레이 수식 $$...$$
    (r"\$\$[\s\S]*?\$\$", "DISPLAY_MATH"),
    # 인라인 수식 $...$
    (r"(?<!\$)\$(?!\$)(?:[^\$\\]|\\.)+\$(?!\$)", "INLINE_MATH"),
    # 코드 블록 ```...```
    (r"```[\s\S]*?```", "CODE_BLOCK"),
    # 인라인 코드 `...`
    (r"`[^`]+`", "INLINE_CODE"),
    # 이미지 ![...](...) 
    (r"!\[([^\]]*)\]\([^\)]+\)", "IMAGE"),
    # 링크 [...](...) 
    (r"\[([^\]]*)\]\([^\)]+\)", "LINK"),
    # HTML 태그
    (r"<[^>]+>", "HTML_TAG"),
]


class MarkdownTranslator:
    """마크다운 구조를 보존하면서 번역하는 번역기."""

    def __init__(self, options: TranslateOptions | None = None):
        self.options = options or TranslateOptions()
        self._placeholders: dict[str, str] = {}
        self._placeholder_counter = 0

    def _get_translator(self) -> GoogleTranslator:
        """GoogleTranslator 인스턴스를 생성한다."""
        return GoogleTranslator(
            source=self.options.source_lang,
            target=self.options.target_lang,
        )

    def translate(self, markdown_text: str) -> str:
        """마크다운 텍스트를 번역한다.

        Args:
            markdown_text: 원본 마크다운 텍스트

        Returns:
            번역된 마크다운 텍스트
        """
        self._placeholders = {}
        self._placeholder_counter = 0

        # 1. 보존할 패턴을 플레이스홀더로 치환
        protected = self._protect_patterns(markdown_text)

        # 2. 라인별로 처리 (헤딩 마커, 테이블 구분선 등 보존)
        lines = protected.split("\n")
        translated_lines = []

        for line in lines:
            translated_lines.append(self._translate_line(line))

        # 3. 최종 결합
        result = "\n".join(translated_lines)

        # 4. 플레이스홀더를 원본으로 복원
        result = self._restore_patterns(result)

        return result

    def _protect_patterns(self, text: str) -> str:
        """보존할 패턴을 플레이스홀더로 치환한다."""
        for pattern, label in PRESERVE_PATTERNS:
            text = re.sub(
                pattern,
                lambda m, lb=label: self._make_placeholder(m.group(0), lb),
                text,
            )
        return text

    def _make_placeholder(self, original: str, label: str) -> str:
        """고유한 플레이스홀더를 생성한다."""
        self._placeholder_counter += 1
        key = f"XPHOLD{label}{self._placeholder_counter}XPHOLD"
        self._placeholders[key] = original
        return key

    def _restore_patterns(self, text: str) -> str:
        """플레이스홀더를 원본으로 복원한다."""
        for key, original in self._placeholders.items():
            text = text.replace(key, original)
        return text

    def _translate_line(self, line: str) -> str:
        """한 줄을 번역한다. 마크다운 구조를 보존한다."""
        stripped = line.strip()

        # 빈 줄은 그대로
        if not stripped:
            return line

        # 테이블 구분선 (|---|---|)
        if re.match(r"^\|[\s\-:|]+\|$", stripped):
            return line

        # 마크다운 헤딩 보존
        heading_match = re.match(r"^(#{1,6}\s+)(.*)", stripped)
        if heading_match:
            prefix = heading_match.group(1)
            content = heading_match.group(2)
            translated = self._translate_text(content)
            return f"{prefix}{translated}"

        # 리스트 아이템 보존
        list_match = re.match(r"^(\s*(?:[-*+]|\d+\.)\s+)(.*)", line)
        if list_match:
            prefix = list_match.group(1)
            content = list_match.group(2)
            translated = self._translate_text(content)
            return f"{prefix}{translated}"

        # 테이블 행
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = stripped.split("|")
            translated_cells = []
            for cell in cells:
                cell_stripped = cell.strip()
                if cell_stripped and not re.match(r"^[\-:]+$", cell_stripped):
                    translated_cells.append(f" {self._translate_text(cell_stripped)} ")
                else:
                    translated_cells.append(cell)
            return "|".join(translated_cells)

        # 플레이스홀더만 있는 줄은 번역 건너뛰기
        if re.match(r"^[\sXPHOLD\w]+$", stripped) and "XPHOLD" in stripped:
            return line

        # 일반 텍스트 번역
        translated = self._translate_text(stripped)

        # 원래 들여쓰기 보존
        leading_spaces = len(line) - len(line.lstrip())
        return " " * leading_spaces + translated

    def _translate_text(self, text: str) -> str:
        """텍스트를 번역한다. API 호출 포함."""
        if not text or not text.strip():
            return text

        # 플레이스홀더만 있으면 번역 불필요
        clean = re.sub(r"XPHOLD\w+XPHOLD", "", text).strip()
        if not clean:
            return text

        try:
            # 청크 분할
            if len(text) > self.options.chunk_size:
                return self._translate_long_text(text)

            translator = self._get_translator()
            result = translator.translate(text)
            return result if result else text
        except Exception:
            # 번역 실패 시 원문 반환
            return text

    def _translate_long_text(self, text: str) -> str:
        """긴 텍스트를 청크로 분할하여 번역한다."""
        chunks = []
        current = ""

        for sentence in re.split(r"(?<=[.!?])\s+", text):
            if len(current) + len(sentence) > self.options.chunk_size:
                if current:
                    chunks.append(current)
                current = sentence
            else:
                current = f"{current} {sentence}".strip()

        if current:
            chunks.append(current)

        translated_chunks = []
        for chunk in chunks:
            translated = self._translate_text(chunk)
            translated_chunks.append(translated)
            time.sleep(0.3)  # rate limit 대응

        return " ".join(translated_chunks)


def translate_markdown(
    markdown_text: str,
    target_lang: str = "ko",
    source_lang: str = "auto",
) -> str:
    """마크다운 텍스트를 번역하는 편의 함수.

    Args:
        markdown_text: 원본 마크다운 텍스트
        target_lang: 대상 언어 코드 (기본: 'ko')
        source_lang: 원본 언어 코드 (기본: 'auto')

    Returns:
        번역된 마크다운 텍스트
    """
    options = TranslateOptions(target_lang=target_lang, source_lang=source_lang)
    translator = MarkdownTranslator(options)
    return translator.translate(markdown_text)
