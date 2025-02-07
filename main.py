import asyncio
import json
import datetime
from playwright.async_api import async_playwright
from playwright._impl._errors import Error as PlaywrightError

HEADLESS = True  # Set to False to see browser actions
NUM_PAGES = 1  # Number of pages to scrape

async def try_goto_with_retry(page, url, max_retries=3):
    """Attempts to navigate to a URL with retries on failure."""
    for attempt in range(max_retries):
        try:
            await page.goto(url, timeout=60000)
            return True
        except PlaywrightError as e:
            if "ERR_NETWORK_CHANGED" in str(e):
                print(f"[WARN] Network changed during attempt {attempt + 1}. Retrying...")
                await asyncio.sleep(5)
            else:
                print(f"[ERROR] Unexpected error: {e}")
                raise
    return False

async def extract_text(element, default=""):
    """Extracts text from a Playwright element safely."""
    return await element.inner_text() if element else default

async def extract_attribute(element, attribute, default=None):
    """Extracts an attribute from a Playwright element safely."""
    return await element.get_attribute(attribute) if element else default

async def scrape_game_details(page, game_url):
    """Scrapes detailed information from a game page."""
    print(f"\n[INFO] Visiting game page: {game_url}")
    if not await try_goto_with_retry(page, game_url):
        return None

    try:
        await page.wait_for_selector("div.container div.GameViewLayout div.DataLayout", timeout=50000)
        slug = game_url.split("/")[-1]

        # Extract core details
        game_title = await extract_text(await page.query_selector("div.__GameDetail span:nth-child(1)"))
        game_about = await extract_text(await page.query_selector("div.GameAboutText"))

        # Extract contract details
        contracts = []
        table_element = await page.query_selector("div.TableLayout")
        if table_element:
            rows = await table_element.query_selector_all("tbody tr")
            for row in rows:
                cells = await row.query_selector_all("td")
                if len(cells) >= 3:
                    blockchain = await extract_text(cells[1])
                    address = await extract_text(cells[2])
                    contracts.append({"blockchain": blockchain.strip(), "address": address.strip()})

        # Extract social links
        social_links = {}
        for link in await page.query_selector_all("div.GameLinkItems a"):
            text = await extract_text(link)
            href = await extract_attribute(link, "href")
            if text and href:
                social_links[text.strip().lower()] = href

        # Extract categories
        categories = [await extract_text(cat) for cat in await page.query_selector_all("div.GameCategoryItems .__CategoryItem")]

        # Extract NFT info
        nft_info = {}
        for element in await page.query_selector_all("div.GameNftInfos .__InfoItem"):
            spans = await element.query_selector_all("span")
            if len(spans) == 2:
                key = await extract_text(spans[0])
                value = await extract_text(spans[1])
                nft_info[key.strip()] = value.strip()

        # Extract play link
        play_button = await page.query_selector("div.__PlayButton")
        play_link = None
        if play_button:
            onclick = await play_button.get_attribute("onclick")
            if onclick and "window.open(" in onclick:
                play_link = onclick.split("'")[1]

        # Extract gallery images
        gallery_items = [await extract_attribute(slide, "src") for slide in await page.query_selector_all("div.GameGallerySlider .swiper-slide img")]
        
        # Extract blockchains
        blockchains = [await extract_text(el) for el in await page.query_selector_all("div.GameBlockListItems .__Item .__TextView b")]

        # Construct final data object
        game_data = {
            "title": game_title,
            "slug": slug,
            "description": game_about,
            "categories": categories,
            "nft_info": nft_info,
            "social_links": social_links,
            "play_link": play_link,
            "gallery": gallery_items,
            "blockchains": blockchains,
            "contracts": contracts,
            "updated_at": datetime.datetime.utcnow().isoformat()
        }

        # Save to file
        with open(f"game_details_{slug}.json", "w", encoding="utf-8") as f:
            json.dump(game_data, f, indent=4, ensure_ascii=False)

        print(f"[SUCCESS] Game details saved to game_details_{slug}.json")
        return game_data

    except Exception as e:
        print(f"[ERROR] Error scraping game details: {e}")
        return None

async def scrape_playtoearn():
    """Scrapes games from PlayToEarn with pagination."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        context = await browser.new_context()
        page = await context.new_page()

        base_url = "https://playtoearn.com/blockchaingames?page={}"
        all_links = []

        for page_num in range(1, NUM_PAGES + 1):
            url = base_url.format(page_num)
            print(f"[INFO] Loading page {page_num}: {url}")

            if not await try_goto_with_retry(page, url):
                print(f"[ERROR] Failed to load page {page_num}")
                continue

            try:
                await page.wait_for_selector("div.container div.TableLayoutItems table.SnowTable tbody.__TableItemsSwiper tr", timeout=50000)
                rows = await page.query_selector_all("div.container div.TableLayoutItems table.SnowTable tbody.__TableItemsSwiper tr")

                for row in rows:
                    third_td = await row.query_selector("td:nth-child(3)")
                    if third_td:
                        anchors = await third_td.query_selector_all("a")
                        for anchor in anchors:
                            href = await extract_attribute(anchor, "href")
                            if href:
                                all_links.append(href)

                print(f"[INFO] Found {len(all_links)} total game links so far...")

            except Exception as e:
                print(f"[ERROR] Failed to scrape page {page_num}: {e}")

        print(f"\n[INFO] Found {len(all_links)} game links across {NUM_PAGES} pages. Scraping now...")

        # Scrape game details (sequential for stability)
        for link in all_links:
            await scrape_game_details(page, link)
            await asyncio.sleep(2)  # Small delay to avoid rate limiting

        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_playtoearn())
