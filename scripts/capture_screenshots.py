"""Capture full-page dashboard screenshots for the README.

One-off dev helper. Requires the dashboard running on http://localhost:8501
(`.venv/Scripts/python.exe -m streamlit run app.py`) and Playwright + Chromium
(`pip install playwright && python -m playwright install chromium`).

Run: .venv/Scripts/python.exe scripts/capture_screenshots.py
"""

from __future__ import annotations

import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8501"
OUT = Path(__file__).resolve().parent.parent / "assets" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

PAGES = [
    ("", "landing.png", ".ribbon-bar"),
    ("/City_Overview", "city-overview.png", ".js-plotly-plot"),
    ("/Pollutant_Breakdown", "pollutants.png", ".js-plotly-plot"),
    ("/Ask_AI", "ask-ai.png", "[data-testid='stChatInput']"),
]


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900},
                                device_scale_factor=2)
        for path, name, wait_sel in PAGES:
            page.goto(BASE + path, wait_until="networkidle", timeout=60000)
            try:
                page.wait_for_selector(wait_sel, timeout=30000)
            except Exception:
                print(f"  (selector {wait_sel} not found on {path}; capturing anyway)")
            time.sleep(3.5)  # let Plotly finish drawing / agent settle
            page.screenshot(path=str(OUT / name), full_page=True)
            print(f"saved {name}")
        browser.close()


if __name__ == "__main__":
    main()
