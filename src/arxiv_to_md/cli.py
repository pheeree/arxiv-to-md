"""CLI 엔트리포인트.

arxiv-to-md 명령행 인터페이스.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from . import __version__
from .converter import convert

console = Console()


@click.command()
@click.argument("arxiv_input", required=False, default=None)
@click.option("-o", "--output", "output_path", default=None, help="출력 파일 경로 (기본: stdout)")
@click.option("--no-refs", is_flag=True, default=False, help="참고문헌 제거")
@click.option("--no-toc", is_flag=True, default=False, help="목차 제거")
@click.option("--no-appendix", is_flag=True, default=False, help="부록 제거")
@click.option(
    "--sections",
    default=None,
    help='포함할 섹션 (쉼표 구분, 예: "Abstract,Introduction,Method")',
)
@click.option(
    "--translate",
    "translate_lang",
    default=None,
    help="번역 대상 언어 코드 (예: ko, ja, zh-cn)",
)
@click.option(
    "--translate-only",
    "translate_only_path",
    default=None,
    type=click.Path(exists=True),
    help="기존 마크다운 파일만 번역 (arXiv 입력 불필요)",
)
@click.version_option(version=__version__)
def main(
    arxiv_input: str | None,
    output_path: str | None,
    no_refs: bool,
    no_toc: bool,
    no_appendix: bool,
    sections: str | None,
    translate_lang: str | None,
    translate_only_path: str | None,
) -> None:
    """arXiv 논문을 마크다운으로 변환합니다.

    ARXIV_INPUT: arXiv ID (예: 2501.11120) 또는 URL

    \b
    예시:
      arxiv-to-md 2501.11120 -o paper.md
      arxiv-to-md 2501.11120 --translate ko -o paper_ko.md
      arxiv-to-md --translate-only paper.md --translate ko -o paper_ko.md
    """
    try:
        # 모드 1: 기존 파일 번역만
        if translate_only_path:
            if not translate_lang:
                console.print("[bold red]❌ --translate-only 사용 시 --translate 옵션 필요[/bold red]")
                raise SystemExit(1)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                progress.add_task(description="🌏 마크다운 번역 중...", total=None)
                source_text = Path(translate_only_path).read_text(encoding="utf-8")

                from .translator import translate_markdown
                markdown = translate_markdown(source_text, target_lang=translate_lang)

        # 모드 2: arXiv 변환 (+ 선택적 번역)
        elif arxiv_input:
            section_list = [s.strip() for s in sections.split(",")] if sections else None

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                progress.add_task(description="📥 논문 다운로드 및 변환 중...", total=None)
                markdown = asyncio.run(
                    convert(
                        arxiv_input,
                        remove_refs=no_refs,
                        remove_toc=no_toc,
                        remove_appendix=no_appendix,
                        sections=section_list,
                    )
                )

            # 번역 옵션이 있으면 추가 번역
            if translate_lang:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                    transient=True,
                ) as progress:
                    progress.add_task(description="🌏 마크다운 번역 중...", total=None)
                    from .translator import translate_markdown
                    markdown = translate_markdown(markdown, target_lang=translate_lang)
        else:
            console.print("[bold red]❌ arXiv ID/URL 또는 --translate-only 경로를 입력하세요[/bold red]")
            raise SystemExit(1)

        # 출력
        if output_path:
            Path(output_path).write_text(markdown, encoding="utf-8")
            label = "번역 완료" if translate_lang else "변환 완료"
            console.print(
                Panel(
                    f"✅ {label}! → [bold green]{output_path}[/bold green]",
                    title="arxiv-to-md",
                    border_style="green",
                )
            )
        else:
            sys.stdout.write(markdown)

    except ValueError as e:
        console.print(f"[bold red]❌ 오류:[/bold red] {e}")
        raise SystemExit(1)
    except ImportError as e:
        console.print(f"[bold yellow]⚠️  의존성 누락:[/bold yellow] {e}")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[bold red]❌ 변환 실패:[/bold red] {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
