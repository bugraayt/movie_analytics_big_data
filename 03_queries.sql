-- 03_queries.sql
-- PURPOSE: Analytical queries for the Movie Analytics System
-- These are the end-user output queries for Layer 3

-- 1. Top 10 highest rated movies
SELECT title, vote_average, vote_count, release_year, director
FROM fact_movies
WHERE vote_count > 100
ORDER BY vote_average DESC
LIMIT 10;


-- 2. Number of movies per genre
SELECT g.genre_name, COUNT(*) AS movie_count
FROM fact_movies f
JOIN dim_genre g ON f.genre_ids LIKE '%' || g.genre_id::text || '%'
GROUP BY g.genre_name
ORDER BY movie_count DESC;


-- 3. Average rating by release year
SELECT release_year, 
       ROUND(AVG(vote_average)::numeric, 2) AS avg_rating,
       COUNT(*) AS total_movies
FROM fact_movies
WHERE release_year IS NOT NULL
GROUP BY release_year
ORDER BY release_year DESC;


-- 4. Movies by budget category
SELECT budget_category,
       COUNT(*) AS movie_count,
       ROUND(AVG(vote_average)::numeric, 2) AS avg_rating,
       ROUND(AVG(revenue)::numeric, 0) AS avg_revenue
FROM fact_movies
GROUP BY budget_category
ORDER BY movie_count DESC;

-- 5. Most popular movies this decade
SELECT f.title, f.popularity, f.vote_average, d.decade
FROM fact_movies f
JOIN dim_date d ON f.date_id = d.date_id
WHERE d.decade = '2020s'
ORDER BY f.popularity DESC
LIMIT 10;


-- 6. Top directors by average rating
SELECT director,
       COUNT(*) AS movie_count,
       ROUND(AVG(vote_average)::numeric, 2) AS avg_rating
FROM fact_movies
WHERE director IS NOT NULL
AND vote_count > 50
GROUP BY director
HAVING COUNT(*) >= 2
ORDER BY avg_rating DESC
LIMIT 10;


-- 7. Movies by rating category breakdown
SELECT rating_category,
       COUNT(*) AS total,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS percentage
FROM fact_movies
GROUP BY rating_category
ORDER BY total DESC;


-- 8. Revenue vs budget analysis
SELECT title,
       budget,
       revenue,
       (revenue - budget) AS profit,
       ROUND((revenue::float / NULLIF(budget, 0))::numeric, 2) AS roi
FROM fact_movies
WHERE budget > 0 AND revenue > 0
ORDER BY roi DESC
LIMIT 10;


-- 9. Movies per decade
SELECT d.decade,
       COUNT(*) AS movie_count,
       ROUND(AVG(f.vote_average)::numeric, 2) AS avg_rating
FROM fact_movies f
JOIN dim_date d ON f.date_id = d.date_id
GROUP BY d.decade
ORDER BY d.decade;


-- 10. Most common original languages
SELECT original_language,
       COUNT(*) AS movie_count,
       ROUND(AVG(vote_average)::numeric, 2) AS avg_rating
FROM fact_movies
GROUP BY original_language
ORDER BY movie_count DESC
LIMIT 10;