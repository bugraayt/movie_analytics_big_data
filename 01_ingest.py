import requests
import pandas as pd
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"

def fetch_movies(total_pages=20):
    all_movies = []
    print("Fetching movies from TMDB API...")
    for page in range(1, total_pages + 1):
        url = f"{BASE_URL}/movie/popular"
        params = {"api_key": API_KEY, "language": "en-US", "page": page}
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"Error on page {page}: {response.status_code}")
            break
        movies = response.json()["results"]
        all_movies.extend(movies)
        print(f"  Page {page}/{total_pages} done — {len(all_movies)} movies collected")
        time.sleep(0.3)
    return all_movies

def fetch_movie_details(movie_id):
    url = f"{BASE_URL}/movie/{movie_id}"
    params = {"api_key": API_KEY, "language": "en-US"}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    return {}

def fetch_movie_credits(movie_id):
    url = f"{BASE_URL}/movie/{movie_id}/credits"
    params = {"api_key": API_KEY}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    return {}

def enrich_movies(movies, sample_size=100):
    print(f"\nEnriching first {sample_size} movies with extra details...")
    enriched = []
    for i, movie in enumerate(movies[:sample_size]):
        movie_id = movie["id"]
        details = fetch_movie_details(movie_id)
        movie["runtime"] = details.get("runtime", None)
        movie["budget"] = details.get("budget", None)
        movie["revenue"] = details.get("revenue", None)
        movie["status"] = details.get("status", None)
        movie["tagline"] = details.get("tagline", None)
        credits = fetch_movie_credits(movie_id)
        crew = credits.get("crew", [])
        directors = [p["name"] for p in crew if p["job"] == "Director"]
        movie["director"] = directors[0] if directors else None
        enriched.append(movie)
        if (i + 1) % 10 == 0:
            print(f"  Enriched {i + 1}/{sample_size} movies")
        time.sleep(0.25)
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
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)
    json_path = "data/raw/movies_raw.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(movies, f, ensure_ascii=False, indent=2)
    print(f"\nSaved JSON:    {json_path}")
    df = pd.DataFrame(movies)
    df["genre_ids"] = df["genre_ids"].apply(lambda x: ",".join(map(str, x)) if isinstance(x, list) else "")
    csv_path = "data/raw/movies.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"Saved CSV:     {csv_path}")
    parquet_path = "data/processed/movies.parquet"
    df.to_parquet(parquet_path, index=False)
    print(f"Saved Parquet: {parquet_path}")
    return df

def show_summary(df):
    print(f"\n--- Summary ---")
    print(f"Total movies : {len(df)}")
    print(f"Columns      : {list(df.columns)}")
    print(f"Sample titles: {list(df['title'].head(5))}")

if __name__ == "__main__":
    movies = fetch_movies(total_pages=20)
    movies = enrich_movies(movies, sample_size=100)
    df = save_data(movies)
    show_summary(df)
    print("\nAll done! Check your data/ folder.")