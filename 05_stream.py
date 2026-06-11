# 05_stream.py
# PURPOSE: Simulate a real-time data stream by polling the TMDB API
# This covers the "data stream" requirement of the ingestion layer
# In a real big data system this would be Apache Kafka or AWS Kinesis
# Here we simulate it by fetching new movies every few seconds

import requests
import json
import time
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"

def fetch_now_playing():
    """
    Fetches movies that are currently playing in cinemas right now.
    This is our "live stream" source — it changes daily.
    """
    url = f"{BASE_URL}/movie/now_playing"
    params = {"api_key": API_KEY, "language": "en-US", "page": 1}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get("results", [])
    return []

def fetch_trending():
    """
    Fetches movies trending today.
    """
    url = f"{BASE_URL}/trending/movie/day"
    params = {"api_key": API_KEY}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get("results", [])
    return []

def process_event(movie, source):
    """
    Processes one movie as if it just arrived in the stream.
    In a real system this would be a Kafka consumer processing a message.
    """
    event = {
        "timestamp": datetime.now().isoformat(),
        "source": source,
        "movie_id": movie.get("id"),
        "title": movie.get("title"),
        "popularity": movie.get("popularity"),
        "vote_average": movie.get("vote_average"),
        "release_date": movie.get("release_date"),
    }
    return event

def save_stream_data(events):
    """Saves all stream events to a JSON file."""
    os.makedirs("data/raw", exist_ok=True)
    path = "data/raw/stream_events.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(events)} stream events to {path}")

def run_stream(rounds=3, interval=5):
    """
    Simulates a stream by polling the API every few seconds.
    rounds   = how many times to poll (3 rounds is enough to demonstrate)
    interval = seconds to wait between polls
    """
    all_events = []
    seen_ids = set()  # track movies we already processed

    print("Starting stream simulation...")
    print(f"Will poll {rounds} times, {interval} seconds apart\n")

    for round_num in range(1, rounds + 1):
        print(f"--- Round {round_num}/{rounds} --- {datetime.now().strftime('%H:%M:%S')}")

        # Fetch from two sources
        now_playing = fetch_now_playing()
        trending    = fetch_trending()

        new_events = 0

        for movie in now_playing:
            if movie["id"] not in seen_ids:
                event = process_event(movie, "now_playing")
                all_events.append(event)
                seen_ids.add(movie["id"])
                new_events += 1

        for movie in trending:
            if movie["id"] not in seen_ids:
                event = process_event(movie, "trending")
                all_events.append(event)
                seen_ids.add(movie["id"])
                new_events += 1

        print(f"  New events this round : {new_events}")
        print(f"  Total events so far   : {len(all_events)}")

        # Sample of what just came in
        if now_playing:
            sample = now_playing[0]
            print(f"  Sample movie          : {sample['title']} (popularity: {sample['popularity']:.1f})")

        # Wait before next poll (except after last round)
        if round_num < rounds:
            print(f"  Waiting {interval} seconds...\n")
            time.sleep(interval)

    return all_events

if __name__ == "__main__":
    # Run the stream for 3 rounds, 5 seconds apart
    events = run_stream(rounds=3, interval=5)

    # Save all collected events
    save_stream_data(events)

    print("\nStream simulation complete!")
    print(f"Check data/raw/stream_events.json to see the captured events.")