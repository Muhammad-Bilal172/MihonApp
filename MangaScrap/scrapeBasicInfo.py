from bs4 import BeautifulSoup
import requests

def scrapeWebsites(link: str):
    url = "https://asuracomic.net/series"

    return url

from bs4 import BeautifulSoup
import requests
import logging

logging.basicConfig(level=logging.INFO)

def scrapeWebsites(link: str):
    url = "https://asuracomic.net/series"
    return url


def scrapeMangaMainDetails(link: str):
    url = link
    html = ""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        html = response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch initial page {url}: {e}")
        return []

    images_list = []
    titles_list = []
    chapters_list = []
    ratings_list = []
    manga_url_list = []

    is_next_available = True
    page = 1

    while is_next_available:
        try:
            soup = BeautifulSoup(html, "html.parser")

            titles = soup.select(
                "div[class*='items-center'] span[class*='font-bold']"
            )
            if not titles:
                break
            for t in titles:
                titles_list.append(t.text.strip())

            images = soup.select(
                "div[class*='overflow-hidden'] img[class*='rounded-md']"
            )
            for i in images:
                images_list.append(i.get("src"))

            chapters = soup.select(
                "div[class*='items-center'] span[class*='text-[13px] text-[#999]']"
            )
            for c in chapters:
                chapters_list.append(c.text.strip())

            ratings = soup.select(
                "div[class*='flex justify-between'] span[class*='ml-1 text-xs']"
            )
            for r in ratings:
                ratings_list.append(r.text.strip())

            manga_detail_links = soup.select(
                "div[class*='grid grid-cols-2 sm:grid-cols-2 md:grid-cols-5 gap-3 p-4'] a"
            )
            if not manga_detail_links:
                break
            for m in manga_detail_links:
                total = "https://asuracomic.net/" + m.get("href")
                manga_url_list.append(total)

            page += 1
            newUrl = f"https://asuracomic.net/series?page={page}"
            response = requests.get(newUrl, timeout=15)
            response.raise_for_status()
            html = response.text

        except requests.exceptions.RequestException as e:
            logging.warning(f"Stopping pagination due to network error on page {page}: {e}")
            is_next_available = False # Stop loop gracefully
        except Exception as e:
            logging.error(f"A parsing error occurred on page {page}: {e}")
            is_next_available = False # Stop loop gracefully

    mangaData = []
    
    # A final check to prevent data corruption from lists of different lengths
    if not (len(images_list) == len(titles_list) == len(chapters_list) == len(ratings_list) == len(manga_url_list)):
        logging.error("Scraping resulted in mismatched data lists. Returning empty.")
        return []

    for i,j,k,l,m in zip(images_list, titles_list, chapters_list, ratings_list, manga_url_list):
        mangaData.append([i,j,k,l,m])

    return mangaData


