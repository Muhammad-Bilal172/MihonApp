from fastapi import Depends, Request
from security import *
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from psycopg2.extensions import cursor as Cursor
from urllib.parse import urlencode
from typing import Dict, List, Optional
from database import *
from bs4 import BeautifulSoup
import requests
import logging
from network import client
import httpx
from network_setttings import *

async def scrapeChapters(link: str):
    try:
        # response = requests.get(link, timeout=15)
        # response.raise_for_status()
        # html = response.text
        # try:
        #     response = await client.get(link)
        #     response.raise_for_status()
        #     html = response.text
        # except httpx.RequestError as e:
        #     logging.error(f"Network error while fetching {link}: {e}")
        #     return []

        # except httpx.HTTPStatusError as e:
        #     logging.error(f"HTTP error {e.response.status_code} for {link}")
        #     return []

        html = await limited_fetch(link)
        if not html:
            logging.error(f"Failed to fetch page: {link}")
            return []
        # html = response.text

        soup = BeautifulSoup(html, "html.parser")

        chapter_details_link_list = []
        chapter_number_list = []
        chapter_upload_date_list = []

        chapter_details_link = soup.select(
            "div[class*='pl-4 py-2 border rounded-md group w-full hover:bg-[#343434] cursor-pointer border-[#A2A2A2]/20 relative'] a"
        )

        for c in chapter_details_link:
            href = c.get("href", "")
            total = "https://asuracomic.net/series" + (href if href.startswith('/') else '/' + href)
            chapter_details_link_list.append(total)

        chapter_numbers = soup.select(
            "div[class*='pl-4 py-2 border rounded-md group w-full hover:bg-[#343434] cursor-pointer border-[#A2A2A2]/20 relative'] a h3[class*='text-sm']"
        )
        for c in chapter_numbers:
            chapter_number_list.append(c.text.strip())

        chapter_upload_dates = soup.select(
            "div[class*='pl-4 py-2 border rounded-md group w-full hover:bg-[#343434] cursor-pointer border-[#A2A2A2]/20 relative'] a h3[class*='text-xs text-[#A2A2A2]']"
        )
        for c in chapter_upload_dates:
            chapter_upload_date_list.append(c.text.strip())

        chapters_list = []

        if not (len(chapter_details_link_list) == len(chapter_number_list) == len(chapter_upload_date_list)):
            logging.error(f"Mismatched chapter data lengths for link {link}. Returning empty list.")
            return []

        for i,j,k in zip(chapter_details_link_list, chapter_number_list, chapter_upload_date_list):
            chapters_list.append([i,j,k])

        return chapters_list

    except httpx.RequestError as e:
        logging.error(f"Network error while scraping chapters from {link}: {e}")
        return []
    except Exception as e:
        logging.error(f"An unexpected parsing error occurred for link {link}: {e}")
        return []

templates = Jinja2Templates(directory="templates")

def scrape_chapter_list_func(app):

    # For scraping the list of chapters of a specific manga
    @app.get("/manga/{manga_name}/{manga_id}")
    async def scrape_chapter_list(
        request: Request,
        manga_name: str,
        manga_id: str,
        cursor: Cursor = Depends(get_db_cursor),
        user_id: str = Depends(get_current_user_uuid),
    ):
        theme = request.cookies.get("theme")
        
        cursor.execute("SELECT detail_link FROM MangaNames WHERE manga_id = %s AND user_id = %s", (manga_id, user_id))
        manga_detail_link = cursor.fetchone()

        if manga_detail_link is not None:
            manga_detail_link = manga_detail_link[0]

        else:
            cursor.execute("SELECT extension_id FROM MangaNames WHERE manga_id = %s AND user_id = %s", (manga_id, user_id))
            extension_id = cursor.fetchone()
            if extension_id is not None:
                extension_id = extension_id[0]

            params = urlencode({"error": "Manga not found"})
            return RedirectResponse(
                url=f"/all_manga/{extension_id}?{params}",
                status_code=303
            )

        cursor.execute("SELECT image_url, title, chapter, rating FROM MangaNames WHERE manga_id = %s AND user_id = %s", (manga_id, user_id))
        manga_data = cursor.fetchone()

        cursor.execute("SELECT chapter_link, chapter_number, chapter_upload_date, chapter_id FROM MangaChapters WHERE manga_id = %s AND user_id = %s", (manga_id, user_id))

        if cursor.rowcount == 0:
            chapters_data = await scrapeChapters(manga_detail_link)
            for i in chapters_data:
                cursor.execute("INSERT INTO MangaChapters (user_id, manga_id, chapter_link, chapter_number, chapter_upload_date, search_vector) VALUES (%s, %s, %s, %s, %s, to_tsvector('english', %s))", (user_id, manga_id, i[0], i[1], i[2], i[1]))

            cursor.execute("SELECT chapter_link, chapter_number, chapter_upload_date, chapter_id FROM MangaChapters WHERE manga_id = %s AND user_id = %s", (manga_id, user_id)) 
            all_chapters_data = cursor.fetchall()
        else:
            all_chapters_data = cursor.fetchall()


        try:
            cursor.execute("SELECT * FROM library_categories WHERE user_id = %s", (user_id,))
            categories = cursor.fetchall()
        except Exception as e:
            return e

        cursor.execute(
            """
            SELECT lc.category_name
            FROM library l
            JOIN library_categories lc ON l.category_id = lc.category_id
            WHERE l.user_id = %s AND l.manga_id = %s
            """,
            (user_id, manga_id),
        )
        selected_rows = cursor.fetchall()
        selected_categories = [row[0] for row in selected_rows] if selected_rows else []

        return templates.TemplateResponse(
            "single_manga_page.html",
            {
                "request": request,
                "manga_data": manga_data,
                "chapter_data": all_chapters_data,
                "manga_id": manga_id,
                "library_categories": categories,
                "selected_categories": selected_categories,
                "theme": theme
            },
        )

    @app.post("/toggle")
    async def toggle(
        request: Request,
        cursor: Cursor = Depends(get_db_cursor),
        user_id: str = Depends(get_current_user_uuid),
    ):
        theme = request.cookies.get("theme")
        try:
            payload = await request.json()
        except Exception:
            payload = {}

        if payload:
            manga_id = payload.get("manga_id")
            categories = payload.get("categories") or []
        else:
            form = await request.form()
            manga_id = form.get("manga_id")
            categories = form.getlist("categories")

        # Load all categories for this user so we can return true/false for each.
        try:
            cursor.execute("SELECT category_name FROM library_categories WHERE user_id = %s", (user_id,))
            rows = cursor.fetchall()
            all_labels = [row[0] for row in rows] if rows else []
        except Exception:
            all_labels = []

        if not all_labels:
            all_labels = categories

        full_state = {label: (label in categories) for label in all_labels}
        enabled = any(full_state.values())

        try:
            cursor.execute("SELECT title FROM MangaNames WHERE manga_id = %s AND user_id = %s", (manga_id, user_id))
            manga_name = cursor.fetchone()
            if manga_name is not None:
                manga_name = manga_name[0]
        except Exception:
            manga_name = None

        try:
            cursor.execute("SELECT category_id, category_name FROM library_categories WHERE user_id = %s", (user_id,))
            all_category_rows = cursor.fetchall() or []

            for category_id, category_name in all_category_rows:
                if full_state.get(category_name, False):
                    cursor.execute(
                        "INSERT INTO library (user_id, manga_id, category_id) VALUES (%s, %s, %s) ON CONFLICT (manga_id, category_id) DO NOTHING",
                        (user_id, manga_id, category_id),
                    )
                else:
                    cursor.execute(
                        "DELETE FROM library WHERE manga_id = %s AND category_id = %s AND user_id = %s",
                        (manga_id, category_id, user_id),
                    )
        except Exception as e:
            return e

        return RedirectResponse("/manga/" + manga_name + "/" + manga_id, status_code=303)
