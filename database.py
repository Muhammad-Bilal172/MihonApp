import psycopg2
from fastapi import HTTPException, status, Depends
from psycopg2.extensions import cursor as Cursor
from config import *
from typing import Generator


def get_db_cursor() -> Generator[Cursor, None, None]:
    connection = None
    cursor = None
    try:
        connection = psycopg2.connect(DATABASE_URL)
        cursor = connection.cursor()

        yield cursor

        connection.commit()

    except psycopg2.Error as e:
        if connection:
            connection.rollback()

        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred during transaction processing.",
        )
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def setup_database():
    connection = None
    try:
        connection = psycopg2.connect(DATABASE_URL)
        cursor = connection.cursor()

        cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS users(
                    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_name VARCHAR(255) NOT NULL,
                    user_email VARCHAR(255) NOT NULL,
                    user_password VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    search_vector TSVECTOR
                )
            """
        )

        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS installed_extensions(
                    extension_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
                    extension_name TEXT,
                    extension_link TEXT,
                    total_mangas INTEGER,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    search_vector TSVECTOR
                )
            """
        )

        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS MangaNames(
                    manga_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
                    extension_id UUID REFERENCES installed_extensions(extension_id) ON DELETE CASCADE,
                    image_url TEXT,
                    title TEXT,
                    chapter TEXT,
                    rating REAL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    search_vector TSVECTOR
                )
            """
        )

        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS MangaChapters(
                    chapter_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
                    manga_id UUID REFERENCES MangaNames(manga_id) ON DELETE CASCADE,
                    chapter_link TEXT,
                    chapter_number REAL,
                    chapter_upload_date TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    search_vector TSVECTOR
                )
            """
        )

        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS MangaImages(
                    image_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    chapter_id UUID REFERENCES MangaChapters(chapter_id) ON DELETE CASCADE,
                    manga_id UUID REFERENCES MangaNames(manga_id) ON DELETE CASCADE,
                    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
                    image_url TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """
        )

        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS manga_view_history(
                    view_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
                    manga_id UUID REFERENCES MangaNames(manga_id) ON DELETE CASCADE,
                    chapter_id UUID REFERENCES MangaChapters(chapter_id) ON DELETE CASCADE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE (user_id, manga_id)
                )
            """
        )

        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS incognito_mode(
                    incognito_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
                    incognito_mode BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """
        )

        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS download_only(
                    downloaded_only_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
                    downloaded_only_mode BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """
        )

        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS library_categories(
                    category_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
                    category_name TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """
        )

        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS library(
                    library_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    manga_id UUID REFERENCES MangaNames(manga_id) ON DELETE CASCADE,
                    category_id UUID REFERENCES library_categories(category_id) ON DELETE CASCADE,
                    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE (manga_id, category_id)
                )
            """
        )

        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS day_formatter(
                    day_formatter_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
                    day_formatter TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """
        )

        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS relative_timestamps(
                    relative_timestamp_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
                    relative_timestamp BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """
        )
        
        connection.commit()

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Database Error As: {e}"
        )
    finally:
        if connection:
            connection.close()

