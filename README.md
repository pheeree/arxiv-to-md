# 📄 arxiv-to-md

> arXiv 논문 URL/ID를 입력하면 깔끔한 마크다운으로 변환하는 Python CLI 에이전트

## ✨ 특징

- 🚀 **빠른 변환** — arXiv HTML5 직접 파싱 (PDF 파싱 불필요)
- 🔢 **수식 보존** — MathML → LaTeX (`$...$`, `$$...$$`) 자동 변환
- 📑 **섹션 필터링** — 참고문헌, 부록 제거/선택 옵션
- 📦 **PDF 폴백** — HTML 없는 구형 논문은 Docling으로 자동 처리
- 🎨 **Rich CLI** — 진행 상태와 오류를 컬러풀하게 표시

## 🛠 기술 스택

| 영역      | 기술                      |
| --------- | ------------------------- |
| HTTP      | `httpx`                   |
| HTML 파싱 | `beautifulsoup4` + `lxml` |
| PDF 폴백  | `docling` (선택)          |
| CLI       | `click` + `rich`          |

## 📥 설치

```bash
# 기본 설치 (HTML 파싱만)
pip install -e .

# PDF 폴백 포함
pip install -e ".[pdf]"

# 개발 환경
pip install -e ".[dev]"
```

## 🚀 사용법

```bash
# 기본 사용: arXiv ID로 변환
arxiv-to-md 2501.11120

# URL로도 가능
arxiv-to-md https://arxiv.org/abs/2501.11120

# 파일로 저장
arxiv-to-md 2501.11120 -o paper.md

# 참고문헌 제거
arxiv-to-md 2501.11120 --no-refs

# 특정 섹션만 추출
arxiv-to-md 2501.11120 --sections "Abstract,Introduction,Method"
```

## 📂 프로젝트 구조

```
arxiv-to-md/
├── src/
│   └── arxiv_to_md/
│       ├── __init__.py
│       ├── cli.py          # CLI 엔트리포인트
│       ├── converter.py    # 메인 오케스트레이터
│       ├── fetcher.py      # arXiv 소스 다운로드
│       ├── html_parser.py  # HTML → Markdown 변환
│       └── pdf_parser.py   # PDF 폴백 (Docling)
├── tests/
│   ├── test_fetcher.py
│   └── test_html_parser.py
├── pyproject.toml
└── README.md
```

## 🧪 테스트

```bash
pytest tests/ -v
```

## 📄 라이선스

MIT License
