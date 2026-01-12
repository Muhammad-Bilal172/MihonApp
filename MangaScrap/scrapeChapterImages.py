import re
import traceback
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from fastapi import Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
from database import *
from security import *
from psycopg2.extensions import cursor as Cursor
import uuid
from selenium.common.exceptions import TimeoutException, WebDriverException
from typing import Dict, List

templates = Jinja2Templates(directory="templates")

PAGE_RE = re.compile(r"chapter\s+page\s+(\d+)", re.I)


def scrape_chapter_images_in_order(url: str) -> List[str]:
    """
    Loads the chapter page in a headless Chrome session and collects page image URLs in order.
    Returns [] on failure (never returns None).
    """

    def build_driver(headless_mode: str) -> webdriver.Chrome:
        opts = webdriver.ChromeOptions()

        # Headless mode
        if headless_mode == "old":
            opts.add_argument("--headless=old")
        else:
            opts.add_argument("--headless=new")

        # IMPORTANT: isolate selenium from your normal Chrome profile
        opts.add_argument(f"--user-data-dir=/tmp/selenium-{uuid.uuid4().hex}")

        # Reduce GPU/compositor involvement
        opts.add_argument("--window-size=1280,720")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--disable-gpu-rasterization")

        # Misc
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--remote-allow-origins=*")

        # NOTE: mainly for Linux containers; harmless on macOS but not required
        opts.add_argument("--no-sandbox")

        service = Service(log_output="chromedriver.log")
        return webdriver.Chrome(service=service, options=opts)

    driver = None
    last_launch_error = None

    # Try headless=new first, fallback to headless=old
    for mode in ("new", "old"):
        try:
            driver = build_driver(mode)
            break
        except Exception as e:
            last_launch_error = e
            traceback.print_exc()

    if driver is None:
        print(f"Could not start ChromeDriver: {last_launch_error}")
        return []

    img_css = "div.w-full.mx-auto.center img"

    try:
        driver.set_page_load_timeout(30)

        # Load page (avoid getting stuck forever)
        try:
            driver.get(url)
        except TimeoutException:
            driver.execute_script("window.stop();")

        wait = WebDriverWait(driver, 25)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, img_css)))

        pages: Dict[int, str] = {}

        stable_rounds = 0
        last_count = 0

        max_scroll_rounds = 150  # increase if chapters are long
        for _ in range(max_scroll_rounds):
            imgs = driver.find_elements(By.CSS_SELECTOR, img_css)

            # Collect all currently discovered image URLs
            for img in imgs:
                alt = (img.get_attribute("alt") or "").strip()
                m = PAGE_RE.search(alt)
                if not m:
                    continue

                page_num = int(m.group(1))

                # Prefer currentSrc (best for <picture>/srcset), then src, then lazy attrs
                src = (
                    img.get_attribute("currentSrc")
                    or img.get_attribute("src")
                    or img.get_attribute("data-src")
                    or img.get_attribute("data-lazy-src")
                )

                if src:
                    pages[page_num] = src

            # Stability detection (stop when no new pages for a few rounds)
            current_count = len(pages)
            if current_count == last_count:
                stable_rounds += 1
            else:
                stable_rounds = 0
                last_count = current_count

            if stable_rounds >= 4 and current_count > 0:
                break

            # Scroll in smaller steps to trigger lazy-load gently
            driver.execute_script("window.scrollBy(0, Math.floor(window.innerHeight * 0.9));")
            time.sleep(0.4)

        # Return ordered by page number
        return [pages[p] for p in sorted(pages.keys())]

    except (WebDriverException, Exception):
        traceback.print_exc()
        return []
    finally:
        try:
            driver.quit()
        except Exception:
            pass

def scrape_chapters_func(app):

    # For scraping the images of a specific chapter of a manga
    @app.get("/chapterImages/manga_id/{manga_id}/chapter_id/{chapter_id}/chapter_number/{chapter_number}")
    def scrape_chapters(
        chapter_id: str,
        manga_id: str,
        chapter_number: str,
        request: Request,
        cursor: Cursor = Depends(get_db_cursor),
        user_id: str = Depends(get_current_user_uuid),
    ):
        theme = request.cookies.get("theme")

        cursor.execute("SELECT * FROM MangaImages WHERE chapter_id = %s AND manga_id = %s AND user_id = %s", (chapter_id, manga_id, user_id))

        if cursor.rowcount == 0:
            cursor.execute("SELECT chapter_link FROM MangaChapters WHERE chapter_id = %s AND manga_id = %s AND user_id = %s", (chapter_id, manga_id, user_id))
            chapter_link = cursor.fetchone()
            if chapter_link is not None:
                chapter_link = chapter_link[0]
            else:
                cursor.execute("SELECT manga_id FROM MangaChapters WHERE chapter_id = %s AND user_id = %s", (chapter_id, user_id))
                manga_id = cursor.fetchone()

                cursor.execute("SELECT title FROM MangaNames WHERE manga_id = %s AND user_id = %s", (manga_id, user_id))
                manga_name = cursor.fetchone()

                if manga_name is not None:
                    manga_name = manga_name[0]
                if manga_id is not None:
                    manga_id = manga_id[0]

                params = urlencode({"error": "Chapter not found"})
                return RedirectResponse(
                    url=f"/manga/{manga_name}/{manga_id}?{params}",
                    status_code=303
                )
            data = scrape_chapter_images_in_order(chapter_link)

            if data is None:
                cursor.execute("SELECT manga_id FROM MangaChapters WHERE chapter_id = %s AND user_id = %s", (chapter_id, user_id))
                manga_id = cursor.fetchone()

                cursor.execute("SELECT title FROM MangaNames WHERE manga_id = %s AND user_id = %s", (manga_id, user_id))
                manga_name = cursor.fetchone()
                if manga_name is not None:
                    manga_name = manga_name[0]
                if manga_id is not None:
                    manga_id = manga_id[0]

                params = urlencode({"error": "Chapter not found"})
                return RedirectResponse(
                    url=f"/manga/{manga_name}/{manga_id}?{params}",
                    status_code=303
                )
            for i in data:
                cursor.execute("INSERT INTO MangaImages (user_id, chapter_id, manga_id, image_url) VALUES (%s, %s, %s, %s)", (user_id, chapter_id, manga_id, i))

        else:
            cursor.execute("SELECT image_url FROM MangaImages WHERE chapter_id = %s AND manga_id = %s AND user_id = %s", (chapter_id, manga_id, user_id))
            data = cursor.fetchall()
            data = [i[0] for i in data]

        cursor.execute("SELECT incognito_mode FROM incognito_mode WHERE user_id = %s", (user_id,))
        incognito_mode = cursor.fetchone()

        if incognito_mode is not None:
            incognito_mode = incognito_mode[0]

        if incognito_mode is not True:
            cursor.execute(
                """
                INSERT INTO manga_view_history (user_id, manga_id, chapter_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, manga_id)
                DO UPDATE SET chapter_id = EXCLUDED.chapter_id, created_at = NOW()
                """,
                (user_id, manga_id, chapter_id),
            )

        return templates.TemplateResponse("single_chapter_page.html", {"request": request, "urls": data, "theme": theme})
