"""html_parser 모듈 단위 테스트."""

from arxiv_to_md.html_parser import ArxivHTMLParser, ParseOptions


SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Test Paper</title></head>
<body>
<article class="ltx_document">
  <h1 class="ltx_title ltx_title_document">Title: A Test Paper About AI</h1>

  <div class="ltx_authors">
    <span class="ltx_personname">Alice Smith</span>
    <span class="ltx_personname">Bob Jones</span>
  </div>

  <div class="ltx_abstract">
    <h2 class="ltx_title">Abstract</h2>
    <p>This is the abstract of the paper.</p>
  </div>

  <section class="ltx_section" id="S1">
    <h2 class="ltx_title ltx_title_section">
      <span class="ltx_tag">1 </span>Introduction
    </h2>
    <p>This is the introduction with inline math <math alttext="x^2 + y^2 = z^2"><mi>x</mi></math>.</p>
  </section>

  <section class="ltx_section" id="S2">
    <h2 class="ltx_title ltx_title_section">
      <span class="ltx_tag">2 </span>Method
    </h2>
    <p>This is the method section.</p>

    <section class="ltx_subsection" id="S2.SS1">
      <h3 class="ltx_title ltx_title_subsection">
        <span class="ltx_tag">2.1 </span>Data Collection
      </h3>
      <p>We collected data.</p>
    </section>
  </section>

  <section class="ltx_section" id="S3">
    <h2 class="ltx_title ltx_title_section">References</h2>
    <p>[1] Some reference</p>
  </section>
</article>
</body>
</html>
"""


class TestArxivHTMLParser:
    """ArxivHTMLParser 테스트."""

    def test_parse_title(self):
        parser = ArxivHTMLParser()
        result = parser.parse(SAMPLE_HTML)
        assert "A Test Paper About AI" in result.title

    def test_parse_authors(self):
        parser = ArxivHTMLParser()
        result = parser.parse(SAMPLE_HTML)
        assert "Alice Smith" in result.authors
        assert "Bob Jones" in result.authors

    def test_parse_abstract(self):
        parser = ArxivHTMLParser()
        result = parser.parse(SAMPLE_HTML)
        assert "abstract of the paper" in result.abstract

    def test_parse_sections(self):
        parser = ArxivHTMLParser()
        result = parser.parse(SAMPLE_HTML)
        section_titles = [s.title for s in result.sections]
        assert "Introduction" in section_titles
        assert "Method" in section_titles

    def test_parse_subsections(self):
        parser = ArxivHTMLParser()
        result = parser.parse(SAMPLE_HTML)
        method_section = [s for s in result.sections if s.title == "Method"][0]
        assert len(method_section.subsections) > 0
        assert "Data Collection" in method_section.subsections[0].title

    def test_remove_refs(self):
        parser = ArxivHTMLParser(ParseOptions(remove_refs=True))
        result = parser.parse(SAMPLE_HTML)
        section_titles = [s.title.lower() for s in result.sections]
        assert not any("reference" in t for t in section_titles)

    def test_section_filter(self):
        parser = ArxivHTMLParser(ParseOptions(include_sections=["Introduction"]))
        result = parser.parse(SAMPLE_HTML)
        assert len(result.sections) == 1
        assert result.sections[0].title == "Introduction"

    def test_math_conversion(self):
        parser = ArxivHTMLParser()
        result = parser.parse(SAMPLE_HTML)
        intro = [s for s in result.sections if s.title == "Introduction"][0]
        assert "$x^2 + y^2 = z^2$" in intro.content


class TestMathConversion:
    """수식 변환 테스트."""

    def test_inline_math_alttext(self):
        html = '<math alttext="\\alpha + \\beta"><mi>α</mi></math>'
        parser = ArxivHTMLParser()
        soup_tag = __import__("bs4").BeautifulSoup(html, "lxml").find("math")
        result = parser._convert_math(soup_tag)
        assert result == "$\\alpha + \\beta$"

    def test_display_math(self):
        html = '<math alttext="E = mc^2" display="block"><mi>E</mi></math>'
        parser = ArxivHTMLParser()
        soup_tag = __import__("bs4").BeautifulSoup(html, "lxml").find("math")
        result = parser._convert_math(soup_tag)
        assert "$$" in result
        assert "E = mc^2" in result
