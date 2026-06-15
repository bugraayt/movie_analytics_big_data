#DATA SERVING LAYER
#
# Exports pre-aggregated, analysis-ready tables from PostgreSQL
# as CSV files for use in Power BI dashboards.


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
    """Runs a SQL query and saves the result as a CSV in data/powerbi/."""
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)
    path = f"data/powerbi/{filename}"
    df.to_csv(path, index=False, encoding="utf-8")
    print(f"Exported {label}: {len(df)} rows → {path}")
    return df


if __name__ == "__main__":
    print("Exporting data for Power BI...\n")

    # Main movies table — joined with dim_date to include the 'decade'
    # column, used across multiple dashboard pages
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

    # Genre breakdown — one row per genre with counts and averages.
    # Note: a movie can belong to multiple genres, so movie_count totals
    # across genres can exceed the total number of movies — expected.
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

    # Yearly trends — used for the "ratings/output over time" charts.
    # Limited to 1990+ to avoid sparse early-decade data skewing averages.
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

    # Budget vs revenue — used for the ROI scatter chart.
    # Only includes movies with both budget and revenue reported.
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

    # Top directors by average rating.
    # No vote_count / movie count filters here — with enrichment covering
    # 396/400 movies, most directors only appear once, so requiring
    # multiple movies would exclude almost everyone.
    export_table("""
        SELECT
            director,
            COUNT(*) AS movie_count,
            ROUND(AVG(vote_average)::numeric, 2) AS avg_rating,
            ROUND(AVG(popularity)::numeric, 2) AS avg_popularity
        FROM fact_movies
        WHERE director IS NOT NULL
        GROUP BY director
        ORDER BY avg_rating DESC
        LIMIT 30
    """, "directors.csv", "directors")

    # Rating vs budget category matrix — used for the budget category
    # breakdown chart (movie_count here is used as the chart's "count of movies")
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