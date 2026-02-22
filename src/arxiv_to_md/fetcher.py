"""arXiv 논문 소스(HTML/PDF) 다운로드 모듈."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

import httpx

# arXiv ID 패턴: 2501.11120, 2501.11120v1, hep-ph/0601001 등
ARXIV_ID_PATTERN = re.compile(
    r"(?:https?://(?:www\.)?arxiv\.org/(?:abs|html|pdf)/)?([a-z\-]+/\d{7}|\d{4}\.\d{4,5}(?:v\d+)?)"
)


class SourceType(Enum):
    """논문 소스 타입."""

    HTML = "html"
    PDF = "pdf"


@dataclass
class PaperSource:
    """다운로드된 논문 소스 정보."""

    arxiv_id: str
    source_type: SourceType
    content: str | bytes
    url: str


def parse_arxiv_id(input_str: str) -> str:
    """입력 문자열에서 arXiv ID를 추출한다.

    Args:
        input_str: arXiv URL 또는 ID 문자열

    Returns:
        정규화된 arXiv ID (예: '2501.11120v1')

    Raises:
        ValueError: 유효한 arXiv ID를 찾을 수 없는 경우
    """
    input_str = input_str.strip()
    match = ARXIV_ID_PATTERN.search(input_str)
    if not match:
        raise ValueError(f"유효한 arXiv ID를 찾을 수 없습니다: {input_str}")
    return match.group(1)


async def fetch_html(arxiv_id: str, client: httpx.AsyncClient | None = None) -> PaperSource | None:
    """arXiv HTML5 버전을 다운로드한다.

    Args:
        arxiv_id: arXiv 논문 ID
        client: httpx 비동기 클라이언트 (없으면 생성)

    Returns:
        PaperSource 또는 HTML 없는 경우 None
    """
    url = f"https://arxiv.org/html/{arxiv_id}"
    should_close = client is None
    client = client or httpx.AsyncClient(follow_redirects=True, timeout=30.0)

    try:
        response = await client.get(url)
        if response.status_code == 200 and "text/html" in response.headers.get(
            "content-type", ""
        ):
            return PaperSource(
                arxiv_id=arxiv_id,
                source_type=SourceType.HTML,
                content=response.text,
                url=url,
            )
        return None
    except httpx.HTTPError:
        return None
    finally:
        if should_close:
            await client.aclose()


async def fetch_pdf(arxiv_id: str, client: httpx.AsyncClient | None = None) -> PaperSource:
    """arXiv PDF를 다운로드한다.

    Args:
        arxiv_id: arXiv 논문 ID
        client: httpx 비동기 클라이언트

    Returns:
        PaperSource (PDF 바이트)

    Raises:
        httpx.HTTPStatusError: 다운로드 실패 시
    """
    url = f"https://arxiv.org/pdf/{arxiv_id}"
    should_close = client is None
    client = client or httpx.AsyncClient(follow_redirects=True, timeout=60.0)

    try:
        response = await client.get(url)
        response.raise_for_status()
        return PaperSource(
            arxiv_id=arxiv_id,
            source_type=SourceType.PDF,
            content=response.content,
            url=url,
        )
    finally:
        if should_close:
            await client.aclose()


async def fetch_paper(arxiv_id_or_url: str) -> PaperSource:
    """논문 소스를 다운로드한다. HTML 우선, 없으면 PDF 폴백.

    Args:
        arxiv_id_or_url: arXiv ID 또는 URL

    Returns:
        PaperSource
    """
    arxiv_id = parse_arxiv_id(arxiv_id_or_url)

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        # HTML 우선 시도
        html_source = await fetch_html(arxiv_id, client)
        if html_source:
            return html_source

        # PDF 폴백
        return await fetch_pdf(arxiv_id, client)
