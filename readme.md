# Movie Analytics System

A big data analytics pipeline that collects, transforms, and visualizes movie data.

## Project Goal
Analyze movie data to uncover insights about ratings, genres, budgets, revenue trends, and director performance over time.

## Architecture

### 1. Data Ingestion Layer
- `01_ingest.py` — Fetches ~400 movies from the TMDB API (JSON), saves as CSV (flat file) and Parquet (columnar)
- `04_pdf_ingest.py` — Generates and parses a PDF report using pdfplumber
- `05_stream.py` — Simulates a real-time data stream by polling TMDB's "now playing" and "trending" endpoints

### 2. Data Transformation Layer
- `02_database.py` — Loads data into PostgreSQL using a star schema:
  - `fact_movies` — main fact table with 400 movies
  - `dim_genre` — genre dimension
  - `dim_date` — date dimension (year, month, decade)
  - Includes derived features: `budget_category` and `rating_category`

### 3. Data Serving Layer
- `03_queries.sql` / `03_run_queries.py` — 10+ analytical SQL queries
- `06_export_for_powerbi.py` — Exports clean datasets for Power BI
- Power BI dashboard with multiple pages: ratings, genres, trends, budget vs revenue, directors

## Tech Stack
- Python (pandas, requests, sqlalchemy, pdfplumber)
- PostgreSQL (star schema data warehouse)
- Power BI (dashboards)

## Setup
1. Clone this repo
2. Create a `.env` file with your TMDB API key and database credentials
3. Install dependencies: `pip install -r requirements.txt`
4. Run scripts in order: `01_ingest.py` → `02_database.py` → `04_pdf_ingest.py` → `05_stream.py` → `06_export_for_powerbi.py`

## Author
Bugra Ayten