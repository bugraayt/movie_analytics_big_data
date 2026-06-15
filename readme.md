# Movie Analytics System

A big data analytics pipeline that collects, transforms, and visualizes movie data.

## Project Goal
Analyze movie data to uncover insights about ratings, genres, budgets, revenue trends, and director performance over time.

## Architecture

### 1. Data Ingestion Layer
- `01_ingest.py` — Fetches ~400 movies from the TMDB API (JSON), saves as CSV (flat file) and Parquet (columnar)
- `04_stream.py` — Simulates a real-time data stream by polling TMDB's "now playing" and "trending" endpoints

### 2. Data Transformation Layer
- `02_database.py` — Loads data into PostgreSQL using a star schema:
  - `fact_movies` — main fact table with 400 movies
  - `dim_genre` — genre dimension
  - `dim_date` — date dimension (year, month, decade)
  - Includes derived features: `budget_category` and `rating_category`

### 3. Data Serving Layer
- `03_queries.sql` / `03_run_queries.py` — 10+ analytical SQL queries
- `05_export_for_powerbi.py` — Exports clean datasets for Power BI
- Power BI dashboard with multiple pages: ratings, genres, budget vs revenue, directors

## Power BI Dashboard

The interactive dashboard is available here: [Movie Analytics Dashboard](https://app.powerbi.com/view?r=eyJrIjoiODJlMmNiMDItMmU3ZS00MDllLWEzYmEtMzdiNjBlMTUyMTkwIiwidCI6IjMyN2M5ZDQwLWIzODUtNGE3Ni1hNjg2LTc0ZDBiMzU0YWQ0NyIsImMiOjh9)

## Tech Stack
- Python (pandas, requests, sqlalchemy)
- PostgreSQL (star schema data warehouse)
- Power BI (dashboards)

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

python 04_stream.py

python 05_export_for_powerbi.py
5. Upload the CSV files from `data/powerbi/` to Power BI for dashboard creation


## Team
- Bugra Ayten
- Cerenay Kuzu
- Egehan Arslan