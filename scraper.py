import asyncio
import json
import datetime
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
        await page.wait_for_selector("div.container div.GameViewLayout div.DataLayout", timeout=50000)
        
        # Extract core details
        title_element = await page.query_selector("div.__GameDetail span:nth-child(1)")
        game_title = await title_element.inner_text() if title_element else ""

        about_element = await page.query_selector("div.GameAboutText")
        game_about = await about_element.inner_text() if about_element else ""
        
        slug = game_url.split("/")[-1]

        # Extract social links
        social_links = {}
        links = await page.query_selector_all("div.GameLinkItems a")
        for link in links:
            href = await link.get_attribute("href")
            text = await link.inner_text()
            if href and text:
                social_links[text.strip().lower()] = href

        # Extract categories
        category_elements = await page.query_selector_all("div.GameCategoryItems .__CategoryItem")
        categories = []
        for cat in category_elements:
            cat_text = await cat.inner_text()
            categories.append(cat_text)

        # Extract NFT info
        nft_elements = await page.query_selector_all("div.GameNftInfos .__InfoItem")
        nft_info = {}
        for element in nft_elements:
            spans = await element.query_selector_all("span")
            if len(spans) == 2:
                key = await spans[0].inner_text()
                value = await spans[1].inner_text()
                nft_info[key.strip()] = value.strip()

        # Extract play link
        play_button = await page.query_selector("div.__PlayButton")
        play_link = None
        if play_button:
            onclick = await play_button.get_attribute("onclick")
            if onclick and "window.open(" in onclick:
                play_link = onclick.split("'")[1]

        # Construct final data object
        game_data = {
            "title": game_title,
            "slug": slug,
            "description": game_about,
            "categories": categories,
            "nft_info": nft_info,
            "social_links": social_links,
            "play_link": play_link,
            "updated_at": datetime.datetime.utcnow().isoformat()
        }

        # Save to file
        with open(f"game_details_{slug}.json", "w", encoding="utf-8") as f:
            json.dump(game_data, f, indent=4, ensure_ascii=False)

        print(f"Game details saved to game_details_{slug}.json")
        return game_data

    except Exception as e:
        print(f"Error scraping game details: {e}")
        import traceback
        traceback.print_exc()
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
                print(f"\nFound {len(links)} game links")
                for link in links[:5]:  # Scrape only first 5 games
                    await scrape_game_details(page, link)
            
        except Exception as e:
            print(f"An error occurred while scraping: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await asyncio.sleep(5)
            await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_playtoearn())
