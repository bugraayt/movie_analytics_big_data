# DATA INGESTION LAYER
#
# Purpose: Collects movie data from the TMDB (The Movie Database) API
# and saves it in three formats:
#   - JSON  (raw data lake format)
#   - CSV   (flat file format)
#   - Parquet (columnar format)
#
# This script fetches a list of popular movies, then enriches each
# movie with additional details (budget, revenue, runtime, director)
# by making extra API calls.

import requests       # for making HTTP requests to the TMDB API
import pandas as pd   # for converting data into tables and saving to CSV/Parquet
import json           # for saving raw API responses as JSON
import time           # for adding delays between API calls (rate limiting)
import os             # for creating folders and reading environment variables
from dotenv import load_dotenv  # for loading secrets from the .env file

# Load environment variables from .env (contains our TMDB API key)
load_dotenv()
API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"


def fetch_movies(total_pages=20):
    """
    Fetches a list of popular movies from TMDB, page by page.
    Each page returns 20 movies, so total_pages=20 gives ~400 movies.

    A short delay (time.sleep) is added between requests to avoid
    overwhelming the API and to respect rate limits.
    """
    all_movies = []
    print("Fetching movies from TMDB API...")

    for page in range(1, total_pages + 1):
        url = f"{BASE_URL}/movie/popular"
        params = {"api_key": API_KEY, "language": "en-US", "page": page}
        response = requests.get(url, params=params)

        # If the request failed, log it and stop fetching further pages
        if response.status_code != 200:
            print(f"Error on page {page}: {response.status_code}")
            break

        movies = response.json()["results"]
        all_movies.extend(movies)
        print(f"  Page {page}/{total_pages} done — {len(all_movies)} movies collected")

        # Small pause to avoid hitting API rate limits
        time.sleep(0.3)

    return all_movies


def fetch_movie_details(movie_id):
    """
    Fetches additional details for a single movie:
    runtime, budget, revenue, status, and tagline.
    These fields are NOT included in the basic 'popular movies' list,
    so a separate API call per movie is required.
    """
    url = f"{BASE_URL}/movie/{movie_id}"
    params = {"api_key": API_KEY, "language": "en-US"}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    return {}


def fetch_movie_credits(movie_id):
    """
    Fetches the cast and crew for a single movie.
    Used to extract the director's name, which is part of the 'crew' list.
    """
    url = f"{BASE_URL}/movie/{movie_id}/credits"
    params = {"api_key": API_KEY}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    return {}


def enrich_movies(movies, sample_size=400):
    """
    Adds extra details (runtime, budget, revenue, director, etc.) to each movie.

    Each enriched movie requires 2 extra API calls (details + credits),
    so this is the slowest part of the script. sample_size controls how
    many movies get enriched — any movies beyond this get the extra
    fields set to None instead of making more API calls.
    """
    print(f"\nEnriching first {sample_size} movies with extra details...")
    enriched = []

    for i, movie in enumerate(movies[:sample_size]):
        movie_id = movie["id"]

        # Get budget, revenue, runtime, status, tagline
        details = fetch_movie_details(movie_id)
        movie["runtime"] = details.get("runtime", None)
        movie["budget"] = details.get("budget", None)
        movie["revenue"] = details.get("revenue", None)
        movie["status"] = details.get("status", None)
        movie["tagline"] = details.get("tagline", None)

        # Get the director's name from the crew list
        # (a movie can have multiple crew members; we filter for job == "Director")
        credits = fetch_movie_credits(movie_id)
        crew = credits.get("crew", [])
        directors = [p["name"] for p in crew if p["job"] == "Director"]
        movie["director"] = directors[0] if directors else None

        enriched.append(movie)

        # Print progress every 10 movies so we can track how far along we are
        if (i + 1) % 10 == 0:
            print(f"  Enriched {i + 1}/{sample_size} movies")

        # Pause between requests to respect API rate limits
        time.sleep(0.25)

    # Any movies beyond sample_size don't get enriched —
    # set their extra fields to None so the DataFrame has consistent columns
    for movie in movies[sample_size:]:
        movie["runtime"] = None
        movie["budget"] = None
        movie["revenue"] = None
        movie["status"] = None
        movie["tagline"] = None
        movie["director"] = None
        enriched.append(movie)

    return enriched


def save_data(movies):
    """
    Saves the collected movie data in three formats, demonstrating
    different file types used in the data ingestion layer:

    1. JSON     -> raw, unprocessed data (data lake style)
    2. CSV      -> flat file format
    3. Parquet  -> columnar format, efficient for analytics
    """
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)

    # 1. Save raw JSON exactly as received from the API
    json_path = "data/raw/movies_raw.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(movies, f, ensure_ascii=False, indent=2)
    print(f"\nSaved JSON:    {json_path}")

    # Convert to a DataFrame (table) for easier processing
    df = pd.DataFrame(movies)

    # genre_ids comes back as a list (e.g. [28, 12, 16]) — convert it
    # to a comma-separated string so it can be stored in CSV/Parquet/SQL
    df["genre_ids"] = df["genre_ids"].apply(
        lambda x: ",".join(map(str, x)) if isinstance(x, list) else ""
    )

    # 2. Save as CSV (flat file)
    csv_path = "data/raw/movies.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"Saved CSV:     {csv_path}")

    # 3. Save as Parquet (columnar format)
    parquet_path = "data/processed/movies.parquet"
    df.to_parquet(parquet_path, index=False)
    print(f"Saved Parquet: {parquet_path}")

    return df


def show_summary(df):
    """Prints a quick overview of the collected data for sanity checking."""
    print(f"\n--- Summary ---")
    print(f"Total movies : {len(df)}")
    print(f"Columns      : {list(df.columns)}")
    print(f"Sample titles: {list(df['title'].head(5))}")



# MAIN EXECUTION
if __name__ == "__main__":
    # Step 1: Fetch ~400 popular movies (20 pages x 20 movies)
    movies = fetch_movies(total_pages=20)

    # Step 2: Enrich all movies with budget, revenue, runtime, director
    movies = enrich_movies(movies, sample_size=400)

    # Step 3: Save the data as JSON, CSV, and Parquet
    df = save_data(movies)

    # Step 4: Print a summary so we can verify everything looks correct
    show_summary(df)

    print("\nAll done! Check your data/ folder.")