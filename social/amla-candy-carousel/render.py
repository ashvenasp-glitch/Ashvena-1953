"""Render each .slide in index.html to a 1080x1350 PNG in out/ (Instagram 4:5)."""
import pathlib, asyncio
from playwright.async_api import async_playwright

HERE = pathlib.Path(__file__).resolve().parent

async def main():
    out = HERE / "out"; out.mkdir(exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1080, "height": 1350})
        await pg.goto((HERE / "index.html").as_uri(), wait_until="networkidle")
        await pg.evaluate("document.fonts.ready")
        for i, s in enumerate(await pg.query_selector_all(".slide"), 1):
            await s.screenshot(path=str(out / f"ashvena-amla-carousel-{i:02d}.png"))
        await b.close()

asyncio.run(main())
