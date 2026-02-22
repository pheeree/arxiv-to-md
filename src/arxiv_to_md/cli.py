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
@click.argument("arxiv_input")
@click.option("-o", "--output", "output_path", default=None, help="출력 파일 경로 (기본: stdout)")
@click.option("--no-refs", is_flag=True, default=False, help="참고문헌 제거")
@click.option("--no-toc", is_flag=True, default=False, help="목차 제거")
@click.option("--no-appendix", is_flag=True, default=False, help="부록 제거")
@click.option(
    "--sections",
    default=None,
    help='포함할 섹션 (쉼표 구분, 예: "Abstract,Introduction,Method")',
)
@click.version_option(version=__version__)
def main(
    arxiv_input: str,
    output_path: str | None,
    no_refs: bool,
    no_toc: bool,
    no_appendix: bool,
    sections: str | None,
) -> None:
    """arXiv 논문을 마크다운으로 변환합니다.

    ARXIV_INPUT: arXiv ID (예: 2501.11120) 또는 URL
    """
    section_list = [s.strip() for s in sections.split(",")] if sections else None

    try:
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

        if output_path:
            Path(output_path).write_text(markdown, encoding="utf-8")
            console.print(
                Panel(
                    f"✅ 변환 완료! → [bold green]{output_path}[/bold green]",
                    title="arxiv-to-md",
                    border_style="green",
                )
            )
        else:
            # stdout으로 출력
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
