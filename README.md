# Dynamic ML Pipeline

Dynamic ML Pipeline is a simple experimental program for automated machine learning (AutoML) that can handle different datasets, including text. It performs:

- **Data Cleaning** (Handling missing values, normalizing numerical features)
- **Feature Engineering** (TF-IDF for text, scaling for numbers)
- **Model Selection** (RandomForest, XGBoost, LightGBM, CatBoost)
- **Explainability** (SHAP for model interpretation)

### How to Use
1. Place your dataset (`data.csv`) in the project directory.
2. Run the script and specify the target column.
3. The best model is selected and saved as `best_model.pkl`.

This project is experimental and intended for testing different ML approaches.

