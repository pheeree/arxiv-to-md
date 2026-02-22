# PROJECT_PLAN.md

## 프로젝트 개요

**arxiv-to-md**는 arXiv 논문을 깔끔한 마크다운으로 변환하는 Python CLI 도구입니다.

## 문제 정의

arXiv 논문을 LLM에 넣거나 노트 정리할 때, PDF 복붙은 서식이 깨지고, 수식/테이블/참조가 제대로 보존되지 않습니다. 이 도구는 arXiv HTML5 직접 파싱을 통해 빠르고 정확한 변환을 제공합니다.

## 핵심 기능

- [x] arXiv URL/ID 파싱 및 정규화
- [x] arXiv HTML5 소스 다운로드
- [x] HTML → Markdown 변환 (섹션, 수식, 테이블, 이미지)
- [x] PDF 폴백 변환 (Docling)
- [x] 섹션 필터링 (참고문헌/부록 제거, 특정 섹션 선택)
- [x] Rich CLI 인터페이스

## 기술 스택

- Python 3.11+, httpx, beautifulsoup4 + lxml, click, rich
- 선택: docling (PDF 폴백)

## MVP 범위

1. arXiv URL/ID 입력 → HTML 파싱 → 마크다운 출력
2. 수식(MathML→LaTeX), 테이블, 이미지 변환
3. 섹션 필터링 옵션

## 마일스톤

### M1: 기본 변환 파이프라인 ✅
- [x] arXiv ID 파싱
- [x] HTML 소스 다운로드
- [x] HTML → Markdown 파서
- [x] CLI 인터페이스

### M2: 품질 개선
- [ ] 수식 변환 정확도 향상
- [ ] 복잡한 테이블 지원 개선
- [ ] 에러 핸들링 강화

### M3: PDF 폴백 & 확장
- [ ] Docling 기반 PDF 변환 통합 테스트
- [ ] 배치 변환 (여러 논문 한번에)
- [ ] 출력 포맷 커스터마이징

### M4: 배포 & 문서화
- [ ] PyPI 배포
- [ ] 문서 사이트 (mkdocs)
- [ ] CI/CD 파이프라인

## 다음 스텝

`/nextstep` 워크플로우를 실행하여 구체적인 다음 할 일을 확인하세요.
