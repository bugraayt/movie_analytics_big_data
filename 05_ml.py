# MACHINE LEARNING
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

    Numeric features: popularity, runtime, budget, vote_count, release_year
    Categorical features: original_language, budget_category
        -> these get one-hot encoded (turned into 0/1 columns)
    """
    df = df.dropna(subset=["release_year"])

    X = df[["popularity", "runtime", "budget", "vote_count", "release_year",
            "original_language", "budget_category"]]
    y = df["vote_average"]

    return X, y


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


def train_and_evaluate(X, y):
    """
    Splits data into train/test sets, trains the model, and
    evaluates it using Mean Absolute Error (MAE) and R-squared.
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = build_pipeline()
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)

    print(f"\n--- Model Evaluation ---")
    print(f"Mean Absolute Error: {mae:.3f}  (avg. rating prediction is off by this much)")
    print(f"R² Score:            {r2:.3f}  (1.0 = perfect, 0.0 = no better than guessing average)")

    return model, X_test, y_test, predictions


def show_feature_importance(model, X):
    """
    Prints which features the model relied on most when predicting ratings.
    """
    regressor = model.named_steps["regressor"]
    preprocessor = model.named_steps["preprocessor"]

    # Get feature names after one-hot encoding
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
    X, y = prepare_features(df)
    model, X_test, y_test, predictions = train_and_evaluate(X, y)
    show_feature_importance(model, X)
    plot_predictions(y_test, predictions)

    print("\nML model complete! Check data/ml/actual_vs_predicted.png")