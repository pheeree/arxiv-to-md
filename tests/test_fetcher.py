"""fetcher 모듈 단위 테스트."""

import pytest

from arxiv_to_md.fetcher import parse_arxiv_id


class TestParseArxivId:
    """arXiv ID 파싱 테스트."""

    def test_pure_id_new_format(self):
        assert parse_arxiv_id("2501.11120") == "2501.11120"

    def test_pure_id_with_version(self):
        assert parse_arxiv_id("2501.11120v1") == "2501.11120v1"

    def test_pure_id_old_format(self):
        assert parse_arxiv_id("hep-ph/0601001") == "hep-ph/0601001"

    def test_abs_url(self):
        assert parse_arxiv_id("https://arxiv.org/abs/2501.11120v1") == "2501.11120v1"

    def test_html_url(self):
        assert parse_arxiv_id("https://arxiv.org/html/2501.11120") == "2501.11120"

    def test_pdf_url(self):
        assert parse_arxiv_id("https://arxiv.org/pdf/2501.11120") == "2501.11120"

    def test_with_whitespace(self):
        assert parse_arxiv_id("  2501.11120  ") == "2501.11120"

    def test_invalid_input(self):
        with pytest.raises(ValueError, match="유효한 arXiv ID"):
            parse_arxiv_id("not-a-valid-id")

    def test_empty_input(self):
        with pytest.raises(ValueError, match="유효한 arXiv ID"):
            parse_arxiv_id("")

    def test_five_digit_id(self):
        """5자리 ID도 지원."""
        assert parse_arxiv_id("2312.00752") == "2312.00752"
