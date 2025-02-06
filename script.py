import asyncio
import json
from playwright.async_api import async_playwright
from playwright._impl._errors import Error as PlaywrightError

async def try_goto_with_retry(page, url, max_retries=3):
    for attempt in range(max_retries):
        try:
            await page.goto(url, timeout=60000)
            return True
        except PlaywrightError as e:
            if "ERR_NETWORK_CHANGED" in str(e):
                print(f"Network changed during attempt {attempt + 1}. Retrying...")
                await asyncio.sleep(5)  # Wait 5 seconds before retry
            else:
                print(f"Unexpected error: {e}")
                raise
    return False

async def scrape_playtoearn():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = await context.new_page()

        url = "https://playtoearn.com/blockchaingames"
        print("Attempting to load the page...")
        
        if not await try_goto_with_retry(page, url):
            print("Failed to load the page after multiple attempts")
            await browser.close()
            return

        print("Waiting for content to load...")
        try:
            await page.wait_for_selector("div.container div.TableLayoutItems table.SnowTable tbody.__TableItemsSwiper tr", timeout=50000)
            
            rows = await page.query_selector_all("div.container div.TableLayoutItems table.SnowTable tbody.__TableItemsSwiper tr")
            
            # Extract href links from third td of each row
            links = []
            for row in rows:
                third_td = await row.query_selector("td:nth-child(3)")
                if third_td:
                    # Find all 'a' tags in the third td
                    anchors = await third_td.query_selector_all("a")
                    for anchor in anchors:
                        href = await anchor.get_attribute("href")
                        if href:
                            links.append(f"{href}")
            
            # Print results
            print(f"\nFound {len(links)} links:")
            for link in links:
                print(link)
            
            # Save links to file
            with open("game_links.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(links))
            
            print(f"\nLinks have been saved to game_links.txt")
            
        except Exception as e:
            print(f"An error occurred while scraping: {e}")
        finally:
            await asyncio.sleep(5)
            await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_playtoearn())
