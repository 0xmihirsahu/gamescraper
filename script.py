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
                await asyncio.sleep(5)
            else:
                print(f"Unexpected error: {e}")
                raise
    return False

async def scrape_game_details(page, game_url):
    print(f"\nVisiting game page: {game_url}")
    if not await try_goto_with_retry(page, game_url):
        return None

    try:
        # Wait for the content to load
        await page.wait_for_selector("div.container div.GameViewLayout div.DataLayout", timeout=50000)
        
        # Get the innerHTML of the left info section
        left_info = await page.locator("div.__Left div.InfoGameLayout ").inner_html()
        
        # Get the innerHTML of the right links section
        right_links = await page.locator("div.__Right div.GameLinkItems ").inner_html()
        
        # Save both sections to separate files
        with open("game_info.html", "w", encoding="utf-8") as f:
            f.write("=== Game Info ===\n")
            f.write(left_info)
            f.write("\n\n=== Game Links ===\n")
            f.write(right_links)
            
        print("Game details saved to game_info.html")
        return {
            "info": left_info,
            "links": right_links
        }
        
    except Exception as e:
        print(f"Error scraping game details: {e}")
        return None

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
                    anchors = await third_td.query_selector_all("a")
                    for anchor in anchors:
                        href = await anchor.get_attribute("href")
                        if href:
                            links.append(f"{href}")
            
            if links:
                print(f"\nFound {len(links)} links")
                print(f"Visiting first game link...")
                game_details = await scrape_game_details(page, links[0])
                if game_details:
                    print("Successfully scraped game details")
            
        except Exception as e:
            print(f"An error occurred while scraping: {e}")
        finally:
            await asyncio.sleep(5)
            await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_playtoearn())
