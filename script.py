import asyncio
import json
from playwright.async_api import async_playwright

async def scrape_playtoearn():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = await context.new_page()

        url = "https://playtoearn.com/blockchaingames"
        await page.goto(url, timeout=60000)

        print("Waiting for content to load...")
        # Wait for the table rows to be present
        await page.wait_for_selector("div.container div.TableLayoutItems table.SnowTable tbody.__TableItemsSwiper tr", timeout=50000)
        
        # Get all rows
        rows = await page.query_selector_all("div.container div.TableLayoutItems table.SnowTable tbody.__TableItemsSwiper tr")
        
        # Extract third td from each row
        third_column_contents = []
        for row in rows:
            third_td = await row.query_selector("td:nth-child(3)")
            if third_td:
                html_content = await third_td.inner_html()
                third_column_contents.append(html_content)
        
        # Print and save results
        print("\nThird column contents:")
        for content in third_column_contents:
            print(f"\n--- Row Content ---\n{content}")
        
        # Save the HTML to a file for inspection
        with open("table_content.html", "w", encoding="utf-8") as f:
            f.write("\n".join(third_column_contents))
        
        await asyncio.sleep(5)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_playtoearn())
