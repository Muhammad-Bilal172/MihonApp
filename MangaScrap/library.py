from fastapi import Request, Depends
from fastapi.templating import Jinja2Templates
from psycopg2.extensions import cursor as Cursor
from database import *
from security import *

templates = Jinja2Templates(directory="templates")

def library_func(app):

    # For showing all the mangas that are added in library
    @app.get("/library")
    def library(
        request: Request,
        cursor: Cursor = Depends(get_db_cursor),
        user_id: str = Depends(get_current_user_uuid),
    ):

        cursor.execute("SELECT * FROM library_categories WHERE user_id = %s", (user_id,))
        categories = cursor.fetchone()
        if categories is None:
            cursor.execute("INSERT INTO library_categories (user_id, category_name) VALUES (%s, %s)", (user_id, "Default Library"))

        theme = request.cookies.get("theme")

        cursor.execute("SELECT downloaded_only_mode FROM download_only WHERE user_id = %s", (user_id,))
        download_only_mode = cursor.fetchone()

        if download_only_mode is not None:
            download_only_mode = download_only_mode[0]
        else:
            download_only_mode = False

        if download_only_mode is True:
            try:
                cursor.execute("SELECT chapter_id FROM MangaImages WHERE user_id = %s", (user_id,))

            except Exception as e:
                return templates.TemplateResponse("library_page.html", {"request": request, "library_names": "Library", "theme": theme})

            chapter_id = cursor.fetchall()
            if chapter_id is None:
                return "No Data Found"

            try:
                cursor.execute("SELECT manga_id FROM MangaChapters WHERE user_id = %s AND chapter_id IN %s", (user_id, tuple([i[0] for i in chapter_id])))
            except Exception as e:
                return templates.TemplateResponse("library_page.html", {"request": request, "library_names": "Library", "theme": theme})

            manga_id = cursor.fetchall()
            if manga_id is None:
                return "No Data Found"

            # cursor.execute("SELECT * FROM MangaNames WHERE manga_id IN %s AND user_id = %s AND add_to_library = true", (tuple([i[0] for i in manga_id]), user_id))
            # MangaData = cursor.fetchall()

            # cursor.execute("SELECT * FROM MangaNames WHERE user_id = %s AND manga_id IN %s", (user_id, tuple([i[0] for i in manga_id])))
            # MangaData = cursor.fetchall()

            cursor.execute("SELECT category_id, category_name FROM library_categories WHERE user_id = %s", (user_id,))
            categories_data = cursor.fetchall()

            libraries = []

            if categories_data:
                category_ids = [i[0] for i in categories_data]

                cursor.execute("SELECT category_id, manga_id FROM library WHERE user_id = %s AND category_id IN %s AND manga_id IN %s", (user_id, tuple(category_ids), tuple([i[0] for i in manga_id])))
                library_rows = cursor.fetchall()

                cat_manga_map = {}
                all_manga_ids = set()
                for cat_id, m_id in library_rows:
                    cat_manga_map.setdefault(cat_id, []).append(m_id)
                    all_manga_ids.add(m_id)

                manga_details_map = {}
                if all_manga_ids:
                    cursor.execute("SELECT * FROM MangaNames WHERE manga_id IN %s AND user_id = %s", (tuple(all_manga_ids), user_id))
                    manga_rows = cursor.fetchall()
                    for row in manga_rows:
                        manga_details_map[row[0]] = row

                for cat_id, cat_name in categories_data:
                    mangas = []
                    if cat_id in cat_manga_map:
                        for m_id in cat_manga_map[cat_id]:
                            if m_id in manga_details_map:
                                mangas.append(manga_details_map[m_id])
                    
                    libraries.append({
                        "category_name": cat_name,
                        "manga_data": mangas
                    })

        else:
            # cursor.execute("SELECT * FROM MangaNames WHERE user_id = %s", (user_id,))
            # MangaData = cursor.fetchall()

            cursor.execute("SELECT category_id, category_name FROM library_categories WHERE user_id = %s", (user_id,))
            categories_data = cursor.fetchall()

            libraries = []

            if categories_data:
                category_ids = [i[0] for i in categories_data]

                cursor.execute("SELECT category_id, manga_id FROM library WHERE user_id = %s AND category_id IN %s", (user_id, tuple(category_ids)))
                library_rows = cursor.fetchall()

                cat_manga_map = {}
                all_manga_ids = set()
                for cat_id, m_id in library_rows:
                    cat_manga_map.setdefault(cat_id, []).append(m_id)
                    all_manga_ids.add(m_id)

                manga_details_map = {}
                if all_manga_ids:
                    cursor.execute("SELECT * FROM MangaNames WHERE manga_id IN %s AND user_id = %s", (tuple(all_manga_ids), user_id))
                    manga_rows = cursor.fetchall()
                    for row in manga_rows:
                        manga_details_map[row[0]] = row

                for cat_id, cat_name in categories_data:
                    mangas = []
                    if cat_id in cat_manga_map:
                        for m_id in cat_manga_map[cat_id]:
                            if m_id in manga_details_map:
                                mangas.append(manga_details_map[m_id])
                    
                    libraries.append({
                        "category_name": cat_name,
                        "manga_data": mangas
                    })

        return templates.TemplateResponse("library_page.html", {"request": request, "libraries": libraries, "library_names": "Library", "theme": theme})

def soruce_func(app):

    # For showing all the extensions means websites that are downloaded
    @app.get("/source")
    def source(
        request: Request,
        cursor: Cursor = Depends(get_db_cursor),
        user_id: str = Depends(get_current_user_uuid),
    ):
        theme = request.cookies.get("theme")

        cursor.execute("SELECT extension_id FROM MangaNames WHERE user_id = %s", (user_id,))
        extension_ids_data = cursor.fetchone()

        if extension_ids_data is None:
            return templates.TemplateResponse("source_page.html", {"request": request, "theme": theme})

        cursor.execute("SELECT extension_id FROM MangaNames WHERE user_id = %s", (user_id,))
        extension_ids_data = cursor.fetchall()

        extension_ids_data = [i[0] for i in extension_ids_data]

        unique_extension_ids = list(dict.fromkeys(extension_ids_data))

        cursor.execute("SELECT * FROM installed_extensions WHERE extension_id IN %s AND user_id = %s", (tuple(unique_extension_ids), user_id,))
        installed_extensions_data = cursor.fetchall()

        # cursor.execute("SELECT manga_id FROM MangaChapters")
        # manga_id = cursor.fetchone()
        # if manga_id is None:
        #     return "No Data Found"

        # all_manga_ids = cursor.fetchall()
        
        # all_manga_ids = [i[0] for i in all_manga_ids]

        # unique_manga_ids = list(dict.fromkeys(all_manga_ids))

        # cursor.execute("SELECT * FROM MangaNames WHERE manga_id IN %s", (tuple(unique_manga_ids),))
        
        # MangaData = cursor.fetchall()

        return templates.TemplateResponse("source_page.html", {"request": request, "manga_data": installed_extensions_data, "theme": theme})
    