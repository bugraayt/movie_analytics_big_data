# DATA TRANSFORMATION LAYER
#
# This script loads the cleaned movie data (from 01_ingest.py) into
# PostgreSQL, organized as a star schema data warehouse:
#
#   fact_movies   -> main table, one row per movie (the "facts")
#   dim_genre     -> dimension table: genre IDs and names
#   dim_date      -> dimension table: release dates broken into
#                    year, month, day, decade for time-based analysis
#
# It also computes two derived categorical features required by the
# project spec ("appropriately transformed features"):
#   - budget_category: groups raw budget numbers into Low/Medium/High/Blockbuster
#   - rating_category: groups vote_average into Poor/Average/Good/Excellent

import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection details, loaded from .env
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

ENGINE_URL = f"postgresql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def get_engine():
    """Creates a SQLAlchemy engine — this is our connection to PostgreSQL."""
    engine = create_engine(ENGINE_URL)
    print("Connected to PostgreSQL!")
    return engine


def create_tables(engine):
    """
    Creates the star schema tables.

    We DROP the tables first so this script can be safely re-run from
    scratch each time (e.g. after re-fetching data with new sample sizes).
    """
    print("Creating tables...")
    with engine.connect() as conn:
        # Drop in this order because fact_movies depends on dim_date (foreign key)
        conn.execute(text("DROP TABLE IF EXISTS fact_movies CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS dim_genre CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS dim_date CASCADE"))

        # --- Dimension table: genres ---
        # A simple lookup table mapping TMDB's genre IDs to genre names.
        conn.execute(text("""
            CREATE TABLE dim_genre (
                genre_id   INTEGER PRIMARY KEY,
                genre_name VARCHAR(100)
            )
        """))

        # --- Dimension table: dates ---
        # Each unique release date gets its own row, broken down into
        # year/month/day/decade so we can group and filter by time period
        # without repeating date-parsing logic in every query.
        conn.execute(text("""
            CREATE TABLE dim_date (
                date_id       SERIAL PRIMARY KEY,
                full_date     DATE,
                release_year  INTEGER,
                release_month INTEGER,
                release_day   INTEGER,
                decade        VARCHAR(10)
            )
        """))

        # --- Fact table: movies ---
        # One row per movie. date_id links to dim_date (foreign key).
        # budget_category and rating_category are the derived/transformed
        # features computed in load_movie_data() below.
        conn.execute(text("""
            CREATE TABLE fact_movies (
                movie_id          INTEGER PRIMARY KEY,
                title             VARCHAR(500),
                original_language VARCHAR(10),
                overview          TEXT,
                popularity        FLOAT,
                vote_average      FLOAT,
                vote_count        INTEGER,
                runtime           INTEGER,
                budget            BIGINT,
                revenue           BIGINT,
                status            VARCHAR(50),
                tagline           TEXT,
                director          VARCHAR(200),
                genre_ids         VARCHAR(200),
                date_id           INTEGER REFERENCES dim_date(date_id),
                release_date      DATE,
                release_year      INTEGER,
                release_month     INTEGER,
                budget_category   VARCHAR(20),
                rating_category   VARCHAR(20)
            )
        """))

        conn.commit()
        print("Tables created!")


def load_genre_data(engine):
    """
    Loads dim_genre with TMDB's official genre ID -> name mapping.
    This is a fixed reference list (TMDB doesn't change these often),
    so it's hardcoded here rather than fetched via API.
    """
    print("Loading genres...")
    genres = [
        (28, "Action"), (12, "Adventure"), (16, "Animation"),
        (35, "Comedy"), (80, "Crime"), (99, "Documentary"),
        (18, "Drama"), (10751, "Family"), (14, "Fantasy"),
        (36, "History"), (27, "Horror"), (10402, "Music"),
        (9648, "Mystery"), (10749, "Romance"), (878, "Science Fiction"),
        (10770, "TV Movie"), (53, "Thriller"), (10752, "War"),
        (37, "Western")
    ]
    df_genres = pd.DataFrame(genres, columns=["genre_id", "genre_name"])
    df_genres.to_sql("dim_genre", engine, if_exists="append", index=False)
    print(f"  Loaded {len(df_genres)} genres")


def load_date_data(engine, df):
    """
    Builds dim_date from the unique release dates found in the movie data.

    Steps:
      1. Extract unique, non-null release dates from the movies DataFrame
      2. Break each date into year, month, day, and decade
      3. Insert into dim_date (PostgreSQL auto-generates date_id via SERIAL)
      4. Read the table back so we have the date_id -> full_date mapping,
         which we need later to link movies to their date row
    """
    print("Loading dates...")
    df_dates = df[["release_date"]].dropna().drop_duplicates().copy()
    df_dates["release_date"] = pd.to_datetime(df_dates["release_date"], errors="coerce")
    df_dates = df_dates.dropna()
    df_dates["release_year"]  = df_dates["release_date"].dt.year
    df_dates["release_month"] = df_dates["release_date"].dt.month
    df_dates["release_day"]   = df_dates["release_date"].dt.day
    # Decade, e.g. 1994 -> "1990s"
    df_dates["decade"]        = (df_dates["release_year"] // 10 * 10).astype(str) + "s"
    df_dates = df_dates.rename(columns={"release_date": "full_date"})

    df_dates.to_sql("dim_date", engine, if_exists="append", index=False)
    print(f"  Loaded {len(df_dates)} dates")

    # date_id is auto-generated by PostgreSQL (SERIAL), so we read it back
    # here to use it when linking fact_movies to dim_date
    df_dates_db = pd.read_sql("SELECT date_id, full_date FROM dim_date", engine)
    df_dates_db["full_date"] = pd.to_datetime(df_dates_db["full_date"])
    return df_dates_db


def load_movie_data(engine, df, df_dates_db):
    """
    Loads the final fact_movies table.

    Two transformations happen here:
      - budget_category: bins raw budget values into Low/Medium/High/Blockbuster
        (movies with budget == 0 or missing are marked "Unknown" — TMDB
        doesn't report budgets for all movies)
      - rating_category: bins vote_average into Poor/Average/Good/Excellent

    Then movies are joined to dim_date on release_date == full_date to get
    the correct date_id (foreign key).
    """
    print("Loading movies...")
    df = df.copy()

    df["release_date"]  = pd.to_datetime(df["release_date"], errors="coerce")
    df["release_year"]  = df["release_date"].dt.year
    df["release_month"] = df["release_date"].dt.month

    def budget_category(b):
        if pd.isna(b) or b == 0: return "Unknown"
        elif b < 10000000:       return "Low"
        elif b < 50000000:       return "Medium"
        elif b < 150000000:      return "High"
        else:                    return "Blockbuster"

    def rating_category(r):
        if pd.isna(r):  return "Unknown"
        elif r < 5:     return "Poor"
        elif r < 7:     return "Average"
        elif r < 8:     return "Good"
        else:           return "Excellent"

    df["budget_category"] = df["budget"].apply(budget_category)
    df["rating_category"] = df["vote_average"].apply(rating_category)

    # Match each movie's release_date to the corresponding row in dim_date
    # to get its date_id (this is the star schema "fact links to dimension" join)
    df = df.merge(
        df_dates_db[["full_date", "date_id"]],
        left_on="release_date",
        right_on="full_date",
        how="left"
    )

    # Select only the columns that match the fact_movies table structure
    fact_cols = [
        "id", "title", "original_language", "overview",
        "popularity", "vote_average", "vote_count",
        "runtime", "budget", "revenue", "status", "tagline",
        "director", "genre_ids", "date_id", "release_date",
        "release_year", "release_month",
        "budget_category", "rating_category"
    ]

    df_fact = df[fact_cols].copy()
    df_fact = df_fact.rename(columns={"id": "movie_id"})
    # Safety check: avoid inserting duplicate movie_ids (would violate PRIMARY KEY)
    df_fact = df_fact.drop_duplicates(subset=["movie_id"])

    df_fact.to_sql("fact_movies", engine, if_exists="append", index=False)
    print(f"  Loaded {len(df_fact)} movies")


def main():
    print("Reading movies.csv...")
    df = pd.read_csv("data/raw/movies.csv")
    print(f"  Found {len(df)} movies")

    engine = get_engine()
    create_tables(engine)
    load_genre_data(engine)
    df_dates_db = load_date_data(engine, df)
    load_movie_data(engine, df, df_dates_db)

    print("\nAll done! Star schema is ready in PostgreSQL.")


if __name__ == "__main__":
    main()