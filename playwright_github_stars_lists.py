#!/usr/bin/env python3
# $ pip install pandas playwright tabulate && python -m playwright install webkit
# $ GITHUB_REPOSITORY_OWNER=octocat python playwright_github_stars_lists.py
# Original source: https://gist.github.com/ddelange/f233237f91f23a158cea74f0f2f961c6/raw/3b9083f9283b5eadd3ea68e127ecc1613677eef8/playwright_github_stars_lists.py
import asyncio
import os
from contextlib import asynccontextmanager

import pandas as pd
from playwright.async_api import async_playwright
from playwright.async_api._generated import Browser, Locator

BROWSER = "webkit"  # chromium, firefox, webkit
HOST = "https://github.com"
USER = os.environ["GITHUB_REPOSITORY_OWNER"]


@asynccontextmanager
async def new_page(browser: Browser):
    """Render JS scripts in a pre-crawled HTML using a headless browser."""
    # many init options like proxy: https://playwright.dev/python/docs/api/class-browser#browser-new-page
    page = await browser.new_page()
    try:
        yield page
    finally:
        await page.close()


async def parse_stars_list(loc: Locator):
    data = {
        "name": loc.locator("//h3").text_content(),
        "link": loc.get_attribute("href"),
        "description": loc.locator("//span[contains(@class, 'text')]").text_content(),
        "stars": loc.locator("//div[contains(text(), 'repositories')]").text_content(),
    }
    data = dict(zip(data.keys(), await asyncio.gather(*data.values())))
    data["link"] = HOST + data["link"]
    data["description"] = data["description"].strip()
    data["stars"] = int(data["stars"].split()[0])
    return data


async def get_github_stars_lists(browser: Browser):
    async with new_page(browser) as page:
        await page.goto(f"{HOST}/{USER}?tab=stars")
        # print(await page.content())
        loc = page.locator("//a[contains(@href, '/lists/')]")
        coros = [parse_stars_list(loc.nth(i)) for i in range(await loc.count())]
        return await asyncio.gather(*coros)


async def main():
    async with async_playwright() as pw:
        browser: Browser = await getattr(pw, BROWSER).launch()  # await browser.close()
        data = await get_github_stars_lists(browser)
        df = pd.DataFrame(data)
        df["name"] = df.apply(lambda row: f"[{row['name']}]({row['link']})", axis=1)
        print(
            df.sort_values("stars", ascending=False)
            .drop(columns="link")
            .to_markdown(index=False, tablefmt="github")
        )


if __name__ == "__main__":
    asyncio.run(main())