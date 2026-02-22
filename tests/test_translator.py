"""translator 모듈 단위 테스트."""

from arxiv_to_md.translator import MarkdownTranslator, TranslateOptions


class TestPlaceholderProtection:
    """마크다운 구조 보존 테스트 (실제 번역 API 미사용)."""

    def setup_method(self):
        self.translator = MarkdownTranslator(TranslateOptions(target_lang="ko"))

    def test_inline_math_preserved(self):
        """인라인 수식이 보존되는지 확인."""
        text = "The formula $E = mc^2$ is famous."
        protected = self.translator._protect_patterns(text)
        assert "$E = mc^2$" not in protected
        assert "INLINE_MATH" in protected
        restored = self.translator._restore_patterns(protected)
        assert "$E = mc^2$" in restored

    def test_display_math_preserved(self):
        """디스플레이 수식이 보존되는지 확인."""
        text = "Here is a formula:\n$$\nx^2 + y^2 = z^2\n$$\nEnd."
        protected = self.translator._protect_patterns(text)
        assert "$$" not in protected
        assert "DISPLAY_MATH" in protected
        restored = self.translator._restore_patterns(protected)
        assert "$$\nx^2 + y^2 = z^2\n$$" in restored

    def test_code_block_preserved(self):
        """코드 블록이 보존되는지 확인."""
        text = "Example:\n```python\nprint('hello')\n```\nDone."
        protected = self.translator._protect_patterns(text)
        assert "```python" not in protected
        assert "CODE_BLOCK" in protected
        restored = self.translator._restore_patterns(protected)
        assert "```python\nprint('hello')\n```" in restored

    def test_inline_code_preserved(self):
        """인라인 코드가 보존되는지 확인."""
        text = "Use `pip install` to install."
        protected = self.translator._protect_patterns(text)
        assert "`pip install`" not in protected
        restored = self.translator._restore_patterns(protected)
        assert "`pip install`" in restored

    def test_image_preserved(self):
        """이미지 마크다운이 보존되는지 확인."""
        text = "See ![Figure 1](image.png) below."
        protected = self.translator._protect_patterns(text)
        assert "![Figure 1](image.png)" not in protected
        restored = self.translator._restore_patterns(protected)
        assert "![Figure 1](image.png)" in restored

    def test_link_preserved(self):
        """링크가 보존되는지 확인."""
        text = "Visit [Google](https://google.com) for more."
        protected = self.translator._protect_patterns(text)
        assert "[Google](https://google.com)" not in protected
        restored = self.translator._restore_patterns(protected)
        assert "[Google](https://google.com)" in restored

    def test_multiple_patterns_preserved(self):
        """여러 패턴이 동시에 보존되는지 확인."""
        text = "Formula $x$ and `code` and [link](url)."
        protected = self.translator._protect_patterns(text)
        restored = self.translator._restore_patterns(protected)
        assert "$x$" in restored
        assert "`code`" in restored
        assert "[link](url)" in restored


class TestTranslateLine:
    """줄 번역 로직 테스트."""

    def setup_method(self):
        self.translator = MarkdownTranslator(TranslateOptions(target_lang="ko"))

    def test_empty_line_unchanged(self):
        result = self.translator._translate_line("")
        assert result == ""

    def test_table_separator_unchanged(self):
        result = self.translator._translate_line("| --- | --- | --- |")
        assert result == "| --- | --- | --- |"

    def test_heading_prefix_preserved(self):
        """헤딩 마커가 보존되는지 확인."""
        result = self.translator._translate_line("## Hello World")
        assert result.startswith("## ")
