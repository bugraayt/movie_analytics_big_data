#MACHINE LEARNING
#
# Trains a regression model to predict a movie's rating (vote_average)
# based on features like budget, popularity, runtime, vote_count, and genre.
#
# This demonstrates the optional ML extension mentioned in the project
# spec, using the same fact_movies data already loaded into PostgreSQL.


import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, r2_score

import matplotlib.pyplot as plt

load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

ENGINE_URL = f"postgresql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(ENGINE_URL)


def load_data():
    """
    Loads movie data with the features we'll use for prediction.
    Only includes movies with a valid vote_average (our target).
    """
    query = """
        SELECT
            title,
            vote_average,
            popularity,
            runtime,
            budget,
            vote_count,
            release_year,
            original_language,
            budget_category
        FROM fact_movies
        WHERE vote_average IS NOT NULL
          AND runtime IS NOT NULL
          AND popularity IS NOT NULL
    """
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)
    print(f"Loaded {len(df)} movies for training")
    return df


def prepare_features(df):
    """
    Splits the data into features (X) and target (y).
    'title' is kept separately (for displaying example predictions later)
    but is NOT used as a model feature.

    Numeric features: popularity, runtime, budget, vote_count, release_year
    Categorical features: original_language, budget_category
        -> these get one-hot encoded (turned into 0/1 columns)
    """
    df = df.dropna(subset=["release_year"])

    titles = df["title"]
    X = df[["popularity", "runtime", "budget", "vote_count", "release_year",
            "original_language", "budget_category"]]
    y = df["vote_average"]

    return X, y, titles


def build_pipeline():
    """
    Builds a preprocessing + model pipeline:
      - Numeric columns pass through unchanged
      - Categorical columns are one-hot encoded
      - RandomForestRegressor predicts vote_average
    """
    numeric_features = ["popularity", "runtime", "budget", "vote_count", "release_year"]
    categorical_features = ["original_language", "budget_category"]

    preprocessor = ColumnTransformer(transformers=[
        ("num", "passthrough", numeric_features),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features)
    ])

    model = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("regressor", RandomForestRegressor(n_estimators=100, random_state=42))
    ])

    return model


def train_and_evaluate(X, y, titles):
    """
    Splits data into train/test sets, trains the model, and
    evaluates it using Mean Absolute Error (MAE) and R-squared.

    titles is split alongside X and y so we can show example
    predictions later with movie names attached.
    """
    X_train, X_test, y_train, y_test, titles_train, titles_test = train_test_split(
        X, y, titles, test_size=0.2, random_state=42
    )

    model = build_pipeline()
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)

    print(f"\n--- Model Evaluation ---")
    print(f"Mean Absolute Error: {mae:.3f}  (avg. rating prediction is off by this much)")
    print(f"R² Score:            {r2:.3f}  (1.0 = perfect, 0.0 = no better than guessing average)")

    return model, X_test, y_test, titles_test, predictions


def show_feature_importance(model, X):
    """
    Prints which features the model relied on most when predicting ratings.
    """
    regressor = model.named_steps["regressor"]
    preprocessor = model.named_steps["preprocessor"]

    cat_features = preprocessor.named_transformers_["cat"].get_feature_names_out(
        ["original_language", "budget_category"]
    )
    all_features = ["popularity", "runtime", "budget", "vote_count", "release_year"] + list(cat_features)

    importances = regressor.feature_importances_

    feature_importance_df = pd.DataFrame({
        "feature": all_features,
        "importance": importances
    }).sort_values("importance", ascending=False).head(10)

    print(f"\n--- Top 10 Most Important Features ---")
    print(feature_importance_df.to_string(index=False))


def show_example_predictions(titles_test, y_test, predictions, n=10):
    """
    Shows real examples: movie title, actual rating vs. predicted rating.
    This makes the model's output concrete — instead of just an R² number,
    we can see exactly what it predicts for specific movies.
    """
    examples = pd.DataFrame({
        "title": titles_test.values,
        "actual_rating": y_test.values,
        "predicted_rating": predictions.round(2),
    })
    examples["difference"] = (examples["actual_rating"] - examples["predicted_rating"]).round(2)

    print(f"\n--- Example Predictions (first {n} test movies) ---")
    print(examples.head(n).to_string(index=False))


def predict_new_movie(model):
    """
    Predicts the rating for a hypothetical new movie, given its details.
    This demonstrates the practical use case: estimating a rating for
    a movie before it's released, based on its planned attributes.

    NOTE: vote_count=0 for a new movie since it hasn't been released yet.
    Since vote_count was the most important feature in our model (~77%),
    predictions for brand-new movies will lean heavily on the remaining
    features (runtime, budget, popularity, language, year) and may
    regress toward the average rating.
    """
    new_movie = pd.DataFrame([{
        "popularity": 50.0,
        "runtime": 120,
        "budget": 80000000,
        "vote_count": 0,
        "release_year": 2026,
        "original_language": "en",
        "budget_category": "High"
    }])

    predicted_rating = model.predict(new_movie)[0]

    print(f"\n--- Predicting a New (Hypothetical) Movie ---")
    print(new_movie.to_string(index=False))
    print(f"\nPredicted rating: {predicted_rating:.2f}")


def plot_predictions(y_test, predictions):
    """
    Saves a scatter plot comparing actual vs predicted ratings.
    A perfect model would have all points on the diagonal line.
    """
    os.makedirs("data/ml", exist_ok=True)

    plt.figure(figsize=(6, 6))
    plt.scatter(y_test, predictions, alpha=0.5)
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--')
    plt.xlabel("Actual Rating")
    plt.ylabel("Predicted Rating")
    plt.title("Actual vs Predicted Movie Ratings")
    plt.tight_layout()

    path = "data/ml/actual_vs_predicted.png"
    plt.savefig(path)
    print(f"\nSaved plot: {path}")


if __name__ == "__main__":
    df = load_data()
    X, y, titles = prepare_features(df)
    model, X_test, y_test, titles_test, predictions = train_and_evaluate(X, y, titles)
    show_feature_importance(model, X)
    show_example_predictions(titles_test, y_test, predictions)
    predict_new_movie(model)
    plot_predictions(y_test, predictions)

    print("\nML model complete! Check data/ml/actual_vs_predicted.png")