# 06_export_for_powerbi.py
# PURPOSE: Export all tables from PostgreSQL to CSV files
# Power BI will read these CSV files to build dashboards

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

os.makedirs("data/powerbi", exist_ok=True)

def export_table(query, filename, label):
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)
    path = f"data/powerbi/{filename}"
    df.to_csv(path, index=False, encoding="utf-8")
    print(f"Exported {label}: {len(df)} rows → {path}")
    return df

if __name__ == "__main__":
    print("Exporting data for Power BI...\n")

    # Main movies table with all details
    export_table("""
        SELECT
            f.movie_id,
            f.title,
            f.original_language,
            f.popularity,
            f.vote_average,
            f.vote_count,
            f.runtime,
            f.budget,
            f.revenue,
            f.director,
            f.release_date,
            f.release_year,
            f.release_month,
            f.budget_category,
            f.rating_category,
            f.status,
            f.tagline,
            f.overview,
            d.decade
        FROM fact_movies f
        LEFT JOIN dim_date d ON f.date_id = d.date_id
    """, "movies.csv", "movies")

    # Genre breakdown
    export_table("""
        SELECT
            g.genre_name,
            COUNT(*) AS movie_count,
            ROUND(AVG(f.vote_average)::numeric, 2) AS avg_rating,
            ROUND(AVG(f.popularity)::numeric, 2) AS avg_popularity
        FROM fact_movies f
        JOIN dim_genre g ON f.genre_ids LIKE '%' || g.genre_id::text || '%'
        GROUP BY g.genre_name
        ORDER BY movie_count DESC
    """, "genres.csv", "genres")

    # Yearly trends
    export_table("""
        SELECT
            release_year,
            COUNT(*) AS movie_count,
            ROUND(AVG(vote_average)::numeric, 2) AS avg_rating,
            ROUND(AVG(popularity)::numeric, 2) AS avg_popularity,
            SUM(CASE WHEN budget > 0 THEN budget ELSE 0 END) AS total_budget,
            SUM(CASE WHEN revenue > 0 THEN revenue ELSE 0 END) AS total_revenue
        FROM fact_movies
        WHERE release_year IS NOT NULL AND release_year >= 1990
        GROUP BY release_year
        ORDER BY release_year
    """, "yearly_trends.csv", "yearly trends")

    # Budget vs revenue
    export_table("""
        SELECT
            title,
            budget,
            revenue,
            (revenue - budget) AS profit,
            ROUND((revenue::float / NULLIF(budget,0))::numeric, 2) AS roi,
            budget_category,
            vote_average,
            release_year
        FROM fact_movies
        WHERE budget > 0 AND revenue > 0
        ORDER BY revenue DESC
    """, "budget_revenue.csv", "budget vs revenue")

    # Top directors
    export_table("""
        SELECT
            director,
            COUNT(*) AS movie_count,
            ROUND(AVG(vote_average)::numeric, 2) AS avg_rating,
            ROUND(AVG(popularity)::numeric, 2) AS avg_popularity
        FROM fact_movies
        WHERE director IS NOT NULL AND vote_count > 50
        GROUP BY director
        HAVING COUNT(*) >= 2
        ORDER BY avg_rating DESC
        LIMIT 30
    """, "directors.csv", "directors")

    # Rating categories
    export_table("""
        SELECT
            rating_category,
            budget_category,
            COUNT(*) AS movie_count,
            ROUND(AVG(vote_average)::numeric, 2) AS avg_rating,
            ROUND(AVG(revenue)::numeric, 0) AS avg_revenue
        FROM fact_movies
        GROUP BY rating_category, budget_category
        ORDER BY rating_category, budget_category
    """, "rating_budget_matrix.csv", "rating/budget matrix")

    print("\nAll files saved to data/powerbi/")
    print("Now upload these files to Power BI Service.")