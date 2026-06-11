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

queries = {
    "Top 10 highest rated movies": """
        SELECT title, vote_average, vote_count, release_year, director
        FROM fact_movies WHERE vote_count > 100
        ORDER BY vote_average DESC LIMIT 10
    """,
    "Movies per genre": """
        SELECT g.genre_name, COUNT(*) AS movie_count
        FROM fact_movies f
        JOIN dim_genre g ON f.genre_ids LIKE '%' || g.genre_id::text || '%'
        GROUP BY g.genre_name ORDER BY movie_count DESC
    """,
    "Average rating by year": """
        SELECT release_year,
               ROUND(AVG(vote_average)::numeric, 2) AS avg_rating,
               COUNT(*) AS total_movies
        FROM fact_movies WHERE release_year IS NOT NULL
        GROUP BY release_year ORDER BY release_year DESC LIMIT 10
    """,
    "Budget category breakdown": """
        SELECT budget_category, COUNT(*) AS movie_count,
               ROUND(AVG(vote_average)::numeric, 2) AS avg_rating
        FROM fact_movies GROUP BY budget_category ORDER BY movie_count DESC
    """,
    "Top 10 by ROI": """
        SELECT title, budget, revenue,
               ROUND((revenue::float / NULLIF(budget,0))::numeric, 2) AS roi
        FROM fact_movies WHERE budget > 0 AND revenue > 0
        ORDER BY roi DESC LIMIT 10
    """
}

with engine.connect() as conn:
    for name, query in queries.items():
        print(f"\n{'='*50}")
        print(f" {name}")
        print('='*50)
        df = pd.read_sql(text(query), conn)
        print(df.to_string(index=False))