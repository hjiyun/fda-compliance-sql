"""Streamlit 앱 화면 캡쳐 — PDF 보고서 부록용.

실행 전: streamlit run app/app.py --server.port 8502 (headless) 가 떠 있어야 함.
산출: docs/figures/app_shin_ramyun.png, app_seoul_milk.png
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:8502"
OUT = Path(__file__).resolve().parents[1] / "figures"

SHOTS = [
    # (filename, sodium, sugars, saturated_fat, energy)
    ("app_shin_ramyun.png", "1490", "3.3", "6.7", "421"),  # 복수경고 예시
    ("app_seoul_milk.png",  "50",   "5.0", "2.5", "70"),   # 안전 예시
]


def set_inputs(page, vals):
    boxes = page.get_by_role("spinbutton")
    for i, v in enumerate(vals):
        b = boxes.nth(i)
        b.click()
        b.fill(v)
        b.press("Tab")
    # 마지막 입력 commit + rerun 대기
    page.wait_for_timeout(2500)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1440, "height": 1000},
                                  device_scale_factor=2)
        page = ctx.new_page()
        for fname, na, su, sf, en in SHOTS:
            page.goto(URL, wait_until="networkidle")
            page.wait_for_selector("h1", timeout=30000)
            # Streamlit 헤더·툴바(Deploy 메뉴) 숨김 — 보고서용 정돈
            page.add_style_tag(content=(
                "[data-testid='stHeader'],[data-testid='stToolbar'],"
                "header,#MainMenu,footer{display:none!important}"
            ))
            page.wait_for_timeout(1500)
            set_inputs(page, [na, su, sf, en])
            # plotly 렌더 대기
            try:
                page.wait_for_selector(".main-svg", timeout=8000)
            except Exception:
                pass
            page.wait_for_timeout(1500)
            out = OUT / fname
            page.screenshot(path=str(out), full_page=True)
            print(f"[saved] {out}")
        browser.close()


if __name__ == "__main__":
    main()
