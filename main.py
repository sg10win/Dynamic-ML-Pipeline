import pandas as pd
import numpy as np
import shap
import joblib
import optuna
import nltk
import arabic_reshaper
from bidi.algorithm import get_display
from nltk.corpus import stopwords
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.feature_selection import VarianceThreshold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier
from sklearn.metrics import classification_report, roc_auc_score

# Download stopwords for Arabic text preprocessing
nltk.download("stopwords")
arabic_stopwords = set(stopwords.words("arabic"))

# Load dataset
def load_data(file_path):
    df = pd.read_csv(file_path)
    print("✅ Data Loaded:", df.shape)
    return df

# Detect column types
def detect_column_types(df):
    text_cols = df.select_dtypes(include="object").columns.tolist()
    num_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
    return text_cols, num_cols

# Clean and reshape Arabic text
def clean_arabic_text(text):
    text = str(text)  # Ensure text format
    text = arabic_reshaper.reshape(text)  # Fix Arabic letter disconnections
    text = get_display(text)  # Correct RTL display issues
    words = text.split()
    words = [word for word in words if word not in arabic_stopwords]  # Remove stopwords
    return " ".join(words)

# Preprocess data
def preprocess_data(df, target_column):
    text_cols, num_cols = detect_column_types(df)
    
    # Handle missing values
    imputer = SimpleImputer(strategy="most_frequent")
    df[num_cols] = imputer.fit_transform(df[num_cols])

    # Process text columns
    for col in text_cols:
        df[col].fillna("", inplace=True)  # Fill missing text with empty string
        df[col] = df[col].apply(clean_arabic_text)

    # Normalize numerical features
    scaler = StandardScaler()
    df[num_cols] = scaler.fit_transform(df[num_cols])

    print("✅ Data Preprocessed:", df.shape)
    return df, text_cols, num_cols

# Convert Arabic text features using TF-IDF
def text_vectorization(df, text_cols):
    vectorizers = {col: TfidfVectorizer(stop_words=arabic_stopwords, max_features=100) for col in text_cols}
    text_features = [vectorizers[col].fit_transform(df[col]).toarray() for col in text_cols]
    text_features = np.hstack(text_features) if text_features else np.array([])
    
    # Convert text features to DataFrame
    if text_features.size > 0:
        text_df = pd.DataFrame(text_features, columns=[f"text_{i}" for i in range(text_features.shape[1])])
        df = df.drop(columns=text_cols).reset_index(drop=True)
        df = pd.concat([df, text_df], axis=1)
    
    print("✅ Arabic Text Vectorization Complete:", text_df.shape if text_features.size > 0 else "No text columns")
    return df

# Train & evaluate models
def train_models(X_train, y_train):
    models = {
        "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42),
        "XGBoost": XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42),
        "LightGBM": LGBMClassifier(random_state=42),
        "CatBoost": CatBoostClassifier(verbose=0, random_state=42)
    }

    best_model, best_score = None, 0
    for name, model in models.items():
        score = cross_val_score(model, X_train, y_train, cv=5, scoring="roc_auc").mean()
        print(f"🔍 {name} AUC: {score:.4f}")
        if score > best_score:
            best_model, best_score = model, score

    print(f"✅ Best Model: {best_model.__class__.__name__} with AUC: {best_score:.4f}")
    best_model.fit(X_train, y_train)
    joblib.dump(best_model, "best_model.pkl")
    return best_model

# Explainability using SHAP
def explain_model(model, X_train, X_test):
    explainer = shap.Explainer(model, X_train)
    shap_values = explainer(X_test)
    shap.summary_plot(shap_values, X_test)

# Run full pipeline
def main(file_path, target_column):
    df = load_data(file_path)
    df, text_cols, num_cols = preprocess_data(df, target_column)
    
    # Vectorize Arabic text features
    df = text_vectorization(df, text_cols)

    X = df.drop(target_column, axis=1)
    y = df[target_column]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    best_model = train_models(X_train, y_train)
    
    y_pred = best_model.predict(X_test)
    print("\n📊 Classification Report:\n", classification_report(y_test, y_pred))
    print("🔵 AUC Score:", roc_auc_score(y_test, best_model.predict_proba(X_test)[:, 1]))

    explain_model(best_model, X_train, X_test)

# Run script
if __name__ == "__main__":
    main("data.csv", "target")  # Change 'target' to your actual label column
