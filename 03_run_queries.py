# DATA SERVING LAYER
#
# Runs a set of analytical SQL queries against the fact_movies /
# dim_genre star schema (built by 02_database.py) and prints the
# results. These are the "output queries" for end users.


import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

ENGINE_URL = f"postgresql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(ENGINE_URL)

# Each entry: a human-readable name -> the SQL query that answers it
queries = {

    # Highest rated movies (filtered to vote_count > 100 to avoid
    # obscure movies with very few votes skewing the ranking)
    "Top 10 highest rated movies": """
        SELECT title, vote_average, vote_count, release_year, director
        FROM fact_movies WHERE vote_count > 100
        ORDER BY vote_average DESC LIMIT 10
    """,

    # Movie count per genre. genre_ids is stored as a comma-separated
    # string (e.g. "28,12,16"), so we match each genre_id against it
    # using LIKE — this means one movie can count toward multiple genres
    "Movies per genre": """
        SELECT g.genre_name, COUNT(*) AS movie_count
        FROM fact_movies f
        JOIN dim_genre g ON f.genre_ids LIKE '%' || g.genre_id::text || '%'
        GROUP BY g.genre_name ORDER BY movie_count DESC
    """,

    # Trend analysis: how average ratings and movie counts changed by year
    "Average rating by year": """
        SELECT release_year,
               ROUND(AVG(vote_average)::numeric, 2) AS avg_rating,
               COUNT(*) AS total_movies
        FROM fact_movies WHERE release_year IS NOT NULL
        GROUP BY release_year ORDER BY release_year DESC LIMIT 10
    """,

    # Uses the budget_category feature created in 02_database.py
    "Budget category breakdown": """
        SELECT budget_category, COUNT(*) AS movie_count,
               ROUND(AVG(vote_average)::numeric, 2) AS avg_rating
        FROM fact_movies GROUP BY budget_category ORDER BY movie_count DESC
    """,

    # ROI = revenue / budget. Only includes movies with both values > 0
    # to avoid division by zero or meaningless ratios
    "Top 10 by ROI": """
        SELECT title, budget, revenue,
               ROUND((revenue::float / NULLIF(budget,0))::numeric, 2) AS roi
        FROM fact_movies WHERE budget > 0 AND revenue > 0
        ORDER BY roi DESC LIMIT 10
    """
}

# Run each query and print its results as a formatted table
with engine.connect() as conn:
    for name, query in queries.items():
        print(f"\n{'='*50}")
        print(f" {name}")
        print('='*50)
        df = pd.read_sql(text(query), conn)
        print(df.to_string(index=False))