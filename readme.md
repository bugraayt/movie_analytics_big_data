# Movie Analytics System

A big data analytics pipeline that ingests, transforms, and visualizes movie data to uncover insights about ratings, genres, budgets, revenue, and trends over time.

## Project Goal and Thesis

This project investigates patterns in the movie industry by analyzing ~400 movies sourced from The Movie Database (TMDB). It aims to answer questions such as:
- Which genres dominate, and do they correlate with higher ratings?
- Does a higher budget lead to a higher rating or higher revenue (ROI)?
- How have average ratings and movie output changed over time?
- Which directors are consistently associated with highly-rated films?

## Architecture

### 1. Data Ingestion Layer
- `01_ingest.py` — Fetches ~400 movies from the TMDB API, enriches them with budget/revenue/director details. Saves data as JSON (raw), CSV (flat file), and Parquet (columnar)

### 2. Data Transformation Layer
- `02_database.py` — Loads data into PostgreSQL using a star schema:
  - `fact_movies` — main fact table with 400 movies
  - `dim_genre` — genre dimension
  - `dim_date` — date dimension (year, month, decade)
  - Includes derived features: `budget_category` (Low/Medium/High/Blockbuster) and `rating_category` (Poor/Average/Good/Excellent)

### 3. Data Serving Layer
- `03_queries.sql` / `03_run_queries.py` — 10+ analytical SQL queries covering top-rated movies, genre breakdowns, yearly trends, ROI, and director performance
- `04_export_for_powerbi.py` — Exports clean datasets for Power BI
- Power BI dashboard with multiple pages: overview, genres, trends, budget vs revenue, directors — with slicers and cross-filtering for interactive exploration

## Power BI Dashboard

The interactive dashboard is available here: [Movie Analytics Dashboard](https://app.powerbi.com/view?r=eyJrIjoiODJlMmNiMDItMmU3ZS00MDllLWEzYmEtMzdiNjBlMTUyMTkwIiwidCI6IjMyN2M5ZDQwLWIzODUtNGE3Ni1hNjg2LTc0ZDBiMzU0YWQ0NyIsImMiOjh9)

## Data Quality Notes
- 396/400 movies include director information
- 262/400 movies include budget and revenue figures (TMDB does not report this for all titles — documented rather than treated as an error)
- 400/400 movies include runtime
Note: TMDB does not report budget/revenue for all movies (262/400 have this data) — this is expected and accounted for via the "Unknown" budget category, not a data error.

## Tech Stack
- Python (pandas, requests, SQLAlchemy)
- PostgreSQL (star schema data warehouse)
- Power BI (dashboards)

## Machine Learning

`05_ml.py` trains a regression model (Random Forest) to predict a movie's
rating (`vote_average`) using features such as budget, runtime, popularity,
release year, language, and budget category.

**First attempt** (without `vote_count`): the model explained only ~5.6% of
the variation in ratings (R² = 0.056). This suggests that basic production
metadata alone is a weak predictor of audience rating — movie quality
depends heavily on factors not captured here, such as story, acting, and
critical reception.

**Second attempt** (adding `vote_count`): performance improved substantially
(R² = 0.698, MAE = 0.589). However, `vote_count` accounted for ~77% of the
model's predictive power. This indicates the improvement largely reflects
that well-known, frequently-voted movies tend to have more stable and
often higher ratings — i.e., the model is detecting popularity/longevity
rather than identifying intrinsic "movie quality" from production stats
alone.

This comparison is presented as a finding in itself: it demonstrates that
predicting movie quality from structured metadata is inherently limited,
and highlights which features (runtime, popularity, budget, release year)
have the most influence within that limitation.

## Setup
1. Clone this repo

2. Create a `.env` file with your TMDB API key and database credentials:

TMDB_API_KEY=your_key_here

DB_NAME=movies_db

DB_USER=your_db_username

DB_HOST=localhost

DB_PORT=5432
3. Install dependencies: `pip install -r requirements.txt`

4. Run scripts in order:
python 01_ingest.py

python 02_database.py

python 03_run_queries.py

python 04_export_for_powerbi.py

## Team
- Bugra Ayten
- Cerenay Kuzu
- Egehan Arslan