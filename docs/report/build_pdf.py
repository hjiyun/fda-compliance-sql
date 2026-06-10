"""full_report.md → full_report.pdf 빌드.

산출물 결과를 모두 포함:
    - 본문 5 개 장 (full_report.md)
    - 그림 5 종 인라인 임베드 (ERD + Fig 4.1~4.4) — 첫 참조 문단 직후 삽입
    - 표 (마크다운 표 렌더링)
    - 부록 A: Streamlit 앱 화면 캡쳐 2 종

소스 .md 는 변경하지 않으며(SSoT 보존), 그림은 base64 로 임베드하여 단일 PDF 자급.
한글 폰트는 Win11 'Malgun Gothic'. 페이지 번호는 Chromium 푸터로 자동 삽입.

실행:
    python build_pdf.py
"""
import base64
import re
from pathlib import Path

import markdown
from playwright.sync_api import sync_playwright

REPORT_DIR = Path(__file__).resolve().parent
DOCS_DIR = REPORT_DIR.parent
FIG_DIR = DOCS_DIR / "figures"
SRC = REPORT_DIR / "full_report.md"
OUT_PDF = REPORT_DIR / "full_report.pdf"

# 그림 임베드 설정 — 본문 인라인 참조 위치(해당 그림을 설명하는 문단) 직후에 삽입.
#   anchor: HTML 내 검색 문자열,  occ: 몇 번째 등장에 삽입(그림 목록 항목 건너뛰기용)
FIGURES = [
    {"anchor": "전체 테이블 관계와 컬럼 정의는", "occ": 1,
     "file": DOCS_DIR / "ERD.png",
     "cap": "그림 3.1 ERD — 데이터베이스 스키마 관계도"},
    {"anchor": "[그림 4.1]", "occ": 2,
     "file": FIG_DIR / "fig03_category_heatmap.png",
     "cap": "그림 4.1 카테고리 × 영양소 위반률 히트맵 (US, FDA DV ≥ 20 %)"},
    {"anchor": "[그림 4.2]", "occ": 2,
     "file": FIG_DIR / "fig02_q8_forest.png",
     "cap": "그림 4.2 Q8 forest plot — 카테고리 메타데이터의 영양소별 차별적 영향 (US, n = 2,493)"},
    {"anchor": "[그림 4.3]", "occ": 2,
     "file": FIG_DIR / "fig01_sodium_monotonic.png",
     "cap": "그림 4.3 sodium Other − Trusted 격차의 단조 확대 (EU 480 → US 460 → CODEX 400 mg/100 g)"},
    {"anchor": "[그림 4.4]", "occ": 2,
     "file": FIG_DIR / "fig04_sodium_400_cluster.png",
     "cap": "그림 4.4 sodium 함량 분포와 3 국 임계값 — 한국 가공식품의 400 mg/100 g 클러스터"},
]

APP_SHOTS = [
    (FIG_DIR / "app_shin_ramyun.png",
     "부록 A-1. 복수경고 예시 — 신라면(나트륨 · 포화지방 · 에너지 동시 위반), 3 국 모두 multiple_warning. "
     "입력값은 Q11 전수 진단 결과(4.4절)에서 추출."),
    (FIG_DIR / "app_seoul_milk.png",
     "부록 A-2. 안전 예시 — 서울우유, 3 국 모두 safe (글로벌 수출 안전권). "
     "입력값은 Q11 전수 진단 결과(4.4절)에서 추출."),
]


def data_uri(path: Path) -> str:
    b = path.read_bytes()
    return "data:image/png;base64," + base64.b64encode(b).decode("ascii")


def figure_html(path: Path, caption: str) -> str:
    return (f'<figure class="fig"><img src="{data_uri(path)}"/>'
            f'<figcaption>{caption}</figcaption></figure>')


def find_nth(s: str, sub: str, n: int) -> int:
    i = -1
    for _ in range(n):
        i = s.find(sub, i + 1)
        if i == -1:
            return -1
    return i


def inject_figures(html: str) -> str:
    """각 그림을 본문 인라인 참조 문단(</p>) 직후에 삽입."""
    for fig in FIGURES:
        path, anchor, occ, caption = fig["file"], fig["anchor"], fig["occ"], fig["cap"]
        if not path.exists():
            print(f"[warn] 그림 파일 누락: {path}")
            continue
        idx = find_nth(html, anchor, occ)
        if idx == -1:  # occ 번째가 없으면 1번째로 폴백
            idx = html.find(anchor)
        if idx == -1:
            print(f"[warn] 본문에 앵커 없음: {anchor}")
            continue
        close = html.find("</p>", idx)
        if close == -1:
            print(f"[warn] 앵커 뒤 </p> 없음: {anchor}")
            continue
        insat = close + len("</p>")
        html = html[:insat] + figure_html(path, caption) + html[insat:]
        print(f"[fig] {caption[:24]}… 삽입 @ {anchor[:12]} (occ {occ})")
    return html


def appendix_html() -> str:
    parts = ['<div class="appendix"><h2 id="부록-a-streamlit-화면">부록 A. Streamlit 사전 점검 도구 화면</h2>']
    parts.append('<p>본 연구의 SQL 룰 엔진을 Streamlit 으로 확장한 부속 산출물(<code>app/</code>)의 실행 화면이다. '
                 '영양 성분 4 종(100 g 기준)을 입력하면 미국 FDA · 유럽 EU · 국제 CODEX 3 국의 '
                 '라벨 표시 의무를 실시간 판정한다. 상세는 <code>app/README_app.md</code> 참조.</p>')
    for path, caption in APP_SHOTS:
        if not path.exists():
            print(f"[warn] 캡쳐 누락: {path}")
            continue
        parts.append(figure_html(path, caption))
    parts.append("</div>")
    return "".join(parts)


CSS = """
@page { size: A4; }
* { box-sizing: border-box; }
body {
  font-family: 'Malgun Gothic', '맑은 고딕', sans-serif;
  font-size: 10.5pt; line-height: 1.65; color: #111;
  margin: 0;
}
h1 { font-size: 19pt; line-height: 1.3; margin: 0 0 8pt; }
h1:not(:first-of-type) { page-break-before: always; padding-top: 4pt; }
h2 { font-size: 14pt; margin: 18pt 0 7pt; border-bottom: 1.5px solid #333; padding-bottom: 3pt; }
h3 { font-size: 12pt; margin: 14pt 0 5pt; }
h4 { font-size: 11pt; margin: 11pt 0 4pt; color: #333; }
p { margin: 5pt 0; text-align: justify; }
ul, ol { margin: 5pt 0; padding-left: 20pt; }
li { margin: 2pt 0; }
strong { color: #000; }
em { color: #222; }
a { color: #0b5; text-decoration: none; }
hr { border: none; border-top: 1px solid #ccc; margin: 14pt 0; }
code {
  font-family: 'Consolas', monospace; font-size: 9pt;
  background: #f3f3f3; padding: 0.5pt 3pt; border-radius: 3px;
}
pre {
  background: #f6f6f6; border: 1px solid #ddd; border-radius: 4px;
  padding: 8pt; font-size: 8.5pt; line-height: 1.4;
  white-space: pre-wrap; word-break: break-word; page-break-inside: avoid;
}
pre code { background: none; padding: 0; }
table {
  border-collapse: collapse; width: 100%; margin: 8pt 0;
  font-size: 8.6pt; page-break-inside: avoid;
}
th, td { border: 1px solid #b0b0b0; padding: 3pt 5pt; text-align: left; vertical-align: top; word-break: break-word; }
th { background: #eef1f4; font-weight: bold; }
tr:nth-child(even) td { background: #fafbfc; }
figure.fig { margin: 12pt 0; text-align: center; page-break-inside: avoid; }
figure.fig img { max-width: 100%; height: auto; border: 1px solid #ddd; }
figure.fig figcaption { font-size: 9pt; color: #555; margin-top: 4pt; }
.appendix { page-break-before: always; }
.appendix figure.fig img { border: 1px solid #ccc; box-shadow: 0 0 3px rgba(0,0,0,0.15); }
"""

FOOTER = ('<div style="font-size:9px;width:100%;text-align:center;color:#666;'
          'font-family:Malgun Gothic,sans-serif;">'
          '<span class="pageNumber"></span> / <span class="totalPages"></span></div>')


def main():
    md_text = SRC.read_text(encoding="utf-8")
    body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists", "toc", "attr_list"],
    )
    body = inject_figures(body)
    body += appendix_html()

    html = (f"<!doctype html><html lang='ko'><head><meta charset='utf-8'>"
            f"<style>{CSS}</style></head><body>{body}</body></html>")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until="networkidle")
        page.wait_for_timeout(800)
        page.pdf(
            path=str(OUT_PDF),
            format="A4",
            print_background=True,
            display_header_footer=True,
            header_template="<div></div>",
            footer_template=FOOTER,
            margin={"top": "16mm", "bottom": "16mm", "left": "15mm", "right": "15mm"},
        )
        browser.close()

    size = OUT_PDF.stat().st_size
    print(f"[saved] {OUT_PDF}")
    print(f"        {size:,} bytes")


if __name__ == "__main__":
    main()
