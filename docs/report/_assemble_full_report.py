"""docs/report/full_report.md 생성 — 다음 구성을 단일 마크다운으로 통합한다.

    1. 표지 (제목 · 부제 · 저자)
    2. 초록 (00_abstract.md)
    3. 목차 (3-level 수동 작성)
    4. 그림 목록 (4 종)
    5. 본문 5 개 장 (01_introduction.md ~ 05_discussion.md)

원본 6 개 .md 파일(00_abstract + 01~05) 은 single source of truth 로 보존하며,
full_report.md 는 본 스크립트 1 회 실행으로 재생성되는 파생 산출물이다.

실행:
    python _assemble_full_report.py
"""
from pathlib import Path

REPORT_DIR = Path(__file__).resolve().parent
ABSTRACT = "00_abstract.md"
CHAPTERS = [
    "01_introduction.md",
    "02_theoretical_background.md",
    "03_methodology.md",
    "04_results.md",
    "05_discussion.md",
]


TITLE_BLOCK = """# 다국가 식품 라벨링 표준 기반 제품 적합성 비교 진단 시스템 구축

**FDA · EU · CODEX 기준의 관계형 데이터베이스 정형화와 SQL 기반 룰 엔진 설계**

표준학개론 2차 프로젝트 — 최종 보고서

| | |
|---|---|
| **이름** | 홍지윤 |
| **학번** | 2025021951 |
| **소속** | 고려대학교 빅데이터사이언스학과 석사과정 |

---

"""


TOC_AND_FIGLIST = """## 목차

> 페이지 번호는 PDF 변환 후 수동 보강 예정.

- [1. 서론](#1-서론)
  - [1.1 연구 배경](#11-연구-배경)
  - [1.2 연구 목적](#12-연구-목적)
  - [1.3 본 연구의 기여](#13-본-연구의-기여)
  - [1.4 본 연구의 핵심 발견 (미리보기)](#14-본-연구의-핵심-발견-미리보기)
  - [1.5 보고서 구성](#15-보고서-구성)
- [2. 이론적 배경 및 선행 연구](#2-이론적-배경-및-선행-연구)
  - [2.1 식품 영양 라벨링 표준 위계](#21-식품-영양-라벨링-표준-위계)
    - 2.1.1 미국 FDA — 21 CFR 101.9
    - 2.1.2 유럽 EU — Regulation (EU) No 1169/2011
    - 2.1.3 국제 CODEX — CAC/GL 2-1985 + WHO NRV-NCD
  - [2.2 적합성 평가의 표준학 개념](#22-적합성-평가의-표준학-개념)
    - 2.2.1 Level 1 — 임계값 비교
    - 2.2.2 Level 2 — 점수 기반 평가 (향후 과제)
  - [2.3 선행 연구](#23-선행-연구)
    - 2.3.1 1차 프로젝트와의 시리즈 관계
    - 2.3.2 룰 기반 적합성 진단 시스템 사례
    - 2.3.3 메타데이터 부재와 데이터 품질 연구
  - [2.4 본 연구의 위치](#24-본-연구의-위치)
- [3. 연구 방법론](#3-연구-방법론)
  - [3.1 데이터셋](#31-데이터셋)
    - 3.1.1 데이터 출처 — Open Food Facts (OFF)
    - 3.1.2 분석 대상 큐레이션 — 2,493 건의 선별
    - 3.1.3 데이터 특성
  - [3.2 데이터베이스 설계](#32-데이터베이스-설계)
    - 3.2.1 스키마 설계 원칙
    - 3.2.2 데이터베이스 구조 — 개관
    - 3.2.3 다국가 `nutrient_limits` 적재 — 3 국 × 4 영양소 = 12 행
  - [3.3 ETL 파이프라인](#33-etl-파이프라인)
    - 3.3.1 데이터 추출 (Extract)
    - 3.3.2 데이터 변환 (Transform)
    - 3.3.3 데이터 적재 (Load)
  - [3.4 SQL 분석 기법](#34-sql-분석-기법)
    - 3.4.1 핵심 VIEW 설계 — 듀얼 구조
    - 3.4.2 분석 쿼리 개요 (Q1 ~ Q10)
    - 3.4.3 통계 검증 — 비례 z-검정 (SQL + Python 하이브리드)
- [4. 분석 결과](#4-분석-결과)
  - [4.1 분석 개요](#41-분석-개요)
    - 4.1.1 표본 규모
    - 4.1.2 본 장의 그림·표 일람
  - [4.2 단일국(US) 분석 결과](#42-단일국us-분석-결과)
    - 4.2.1 영양소별 위반 분포 (Q1, Q5, Q6)
    - 4.2.2 카테고리별 위반 분포 (Q2, Q4)
    - 4.2.3 메타데이터 부재의 영양소별 차별적 영향 (Q8, 가설 검증)
  - [4.3 다국가 비교 분석 결과](#43-다국가-비교-분석-결과)
    - 4.3.1 표준 엄격도와 단조 패턴 (Q9)
    - 4.3.2 Cross-country compliance gap (Q10)
  - [4.4 라벨 표시 의무 전수 진단 (실무 활용 사례)](#44-라벨-표시-의무-전수-진단-실무-활용-사례)
    - 4.4.1 국가별 라벨 부담 분포
    - 4.4.2 영양소별 라벨 유발 빈도
    - 4.4.3 Cross-country 라벨 부담 패턴 — "CODEX safe = 글로벌 수출 안전권"
    - 4.4.4 대표 사례
    - 4.4.5 실무 활용 시사
  - [4.5 1차 프로젝트와의 결과 비교](#45-1차-프로젝트와의-결과-비교)
- [5. 표준학적 해석 및 결론](#5-표준학적-해석-및-결론)
  - [5.1 본 연구의 핵심 발견 종합](#51-본-연구의-핵심-발견-종합)
  - [5.2 표준학적 함의](#52-표준학적-함의)
    - 5.2.1 다국가 표준 비교의 가치 (RQ3 답변)
    - 5.2.2 메타데이터 표준화의 영양소별 우선순위 (RQ2 답변)
    - 5.2.3 룰 기반 접근의 적합성평가 실무 함의 (RQ1 답변)
  - [5.3 본 연구의 한계 (결과 해석상)](#53-본-연구의-한계-결과-해석상)
    - 5.3.1 한국 식품 일반화 가능성
    - 5.3.2 인과 추론의 한계
    - 5.3.3 데이터 한계
  - [5.4 향후 연구 방향](#54-향후-연구-방향)
    - 5.4.1 표준 확장
    - 5.4.2 데이터 확장
    - 5.4.3 분석 확장
  - [5.5 결론](#55-결론)

---

## 그림 목록 (List of Figures)

> 페이지 번호는 PDF 변환 후 수동 보강 예정.

- **[그림 3.1]** ERD — 데이터베이스 스키마 관계도 ([docs/ERD.png](../ERD.png))
- **[그림 4.1]** 카테고리 × 영양소 위반률 히트맵 (US, FDA DV ≥ 20 %)
- **[그림 4.2]** Q8 forest plot — 카테고리 메타데이터의 영양소별 차별적 영향 (US, n = 2,493)
- **[그림 4.3]** sodium Other − Trusted 격차의 단조 확대 (EU 480 → US 460 → CODEX 400 mg/100 g)
- **[그림 4.4]** sodium 함량 분포와 3 국 임계값 — 한국 가공식품의 400 mg/100 g 클러스터

---

## 표 목록 (List of Tables)

> 페이지 번호는 PDF 변환 후 수동 보강 예정.

- **[표 4.1]** 영양소별 high 판정 분포 (US, FDA DV ≥ 20 %)
- **[표 4.2]** Q8 비례 z-검정 결과 — Trusted vs Other (US, 4 영양소, 95 % Wald CI)
- **[표 4.3]** sodium Other − Trusted 격차의 단조 패턴 — 3 국 비교 (US/EU/CODEX)
- **[표 4.4]** 영양소별 cross-country 판정 차이 빈도 (US/EU/CODEX 3 국 비교)
- **[표 4.5]** 한국 식품 2,493 건의 시장별 라벨 표시 의무 분포 (Q11-A)
- **[표 4.6]** 국가 × 영양소별 high 판정 빈도 (Q11-B)
- **[표 4.7]** 한국 식품 2,493 건의 3 국 라벨 부담 cross-tab 패턴 (Q11-C)
- **[표 4.8]** 한국 식품 대표 사례 — 시장별 라벨 부담 비교 (Q11-D 발췌)
- **[표 4.9]** 1차 프로젝트(ML 변수 중요도) vs 본 연구(룰 기반 위반율) 의 4 영양소 비교

---

"""


SEPARATOR = "\n\n---\n\n"


def main() -> None:
    title = TITLE_BLOCK
    abstract = (REPORT_DIR / ABSTRACT).read_text(encoding="utf-8").rstrip() + "\n\n---\n\n"
    toc_figs = TOC_AND_FIGLIST

    parts = [title, abstract, toc_figs]
    for i, ch in enumerate(CHAPTERS):
        text = (REPORT_DIR / ch).read_text(encoding="utf-8")
        parts.append(text.rstrip() + "\n")
        if i < len(CHAPTERS) - 1:
            parts.append(SEPARATOR)

    out = REPORT_DIR / "full_report.md"
    out.write_text("".join(parts), encoding="utf-8")

    content = out.read_text(encoding="utf-8")
    chars = len(content)
    lines = content.count("\n") + 1
    size = out.stat().st_size
    print(f"[saved] {out}")
    print(f"        {chars:,} chars / {lines:,} lines / {size:,} bytes")
    # 분량 추정: 한글 1자 = UTF-8 3바이트, A4 한 페이지 ≈ 1,500~1,800자
    pages_est = chars / 1700
    print(f"        approx pages: {pages_est:.1f} (excl. figures, 1,700 chars/page basis)")


if __name__ == "__main__":
    main()
