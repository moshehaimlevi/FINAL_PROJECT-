from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.openapi.models import Example
from pydantic import RootModel
from pydantic import BaseModel
from typing import List, Dict, Optional
import pandas as pd
import pickle
import os
import json
from datetime import datetime
from sklearn.linear_model import LinearRegression
import sqlite3

app = FastAPI(title="ML Model Training and Prediction API")

MODELS_DIR = "models"
DB_FILE = "usage.db"
os.makedirs(MODELS_DIR, exist_ok=True)

############ DATASET ############
df = pd.read_csv("employee_data.csv")

print(df.head())

print("CSV columns:", df.columns.tolist())

############ Database Setup ############
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            action TEXT NOT NULL,
            model_name TEXT,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def log_action(user_id: str, action: str, model_name: Optional[str] = None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO usage_logs (user_id, action, model_name, timestamp)
        VALUES (?, ?, ?, ?)
    """, (user_id, action, model_name, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def get_usage_summary(user_id: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM usage_logs WHERE user_id=? AND action='train'", (user_id,))
    trained = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM usage_logs WHERE user_id=? AND action='predict'", (user_id,))
    predictions = c.fetchone()[0]
    conn.close()
    return {"models_trained": trained, "predictions_made": predictions}

init_db()

############ Model save/load ############
def save_model(model_name: str, model, features: List[str], label: str):
    model_path = os.path.join(MODELS_DIR, f"{model_name}.pkl")
    meta_path = os.path.join(MODELS_DIR, f"{model_name}_meta.json")
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    metadata = {
        "model_name": model_name,
        "features": features,
        "label": label,
        "type": type(model).__name__,
        "trained_at": datetime.utcnow().isoformat()
    }
    with open(meta_path, "w") as f:
        json.dump(metadata, f)

def load_model(model_name: str):
    model_path = os.path.join(MODELS_DIR, f"{model_name}.pkl")
    meta_path = os.path.join(MODELS_DIR, f"{model_name}_meta.json")
    if not os.path.exists(model_path) or not os.path.exists(meta_path):
        raise HTTPException(status_code=404, detail="Model not found")
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    with open(meta_path, "r") as f:
        metadata = json.load(f)
    return model, metadata

############ Pydantic Models ############
class PredictRequest(RootModel[Dict[str, float]]):
    pass

############ API Endpoints ############
@app.post("/train")
async def train_model(
    file: UploadFile = File(...),
    model_name: str = Form(...),
    features: str = Form(...),
    label: str = Form(...),
    user_id: str = Form(...),
    model_params: Optional[str] = Form(None),
):
    # --- Load CSV ---
    df = pd.read_csv(file.file)

    # --- Clean CSV columns ---
    df.columns = df.columns.str.strip()  # remove spaces
    print("CSV columns after strip:", df.columns.tolist())

    # --- Parse features string ---
    try:
        features = features.strip()
        if features.startswith("["):  # JSON list
            features_list = json.loads(features)
        else:  # comma-separated string
            features_list = [f.strip() for f in features.split(",") if f.strip()]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid features format: {str(e)}")

    print("Parsed features_list:", features_list)

    # --- Clean label ---
    label = label.strip()

    # --- Optional: lowercase everything to avoid case issues ---
    df.columns = df.columns.str.lower()
    features_list = [f.lower() for f in features_list]
    label = label.lower()

    # --- Validate label ---
    if label not in df.columns:
        raise HTTPException(status_code=400, detail=f"Label '{label}' not found in CSV columns: {df.columns.tolist()}")

    # --- Validate features ---
    missing_features = [f for f in features_list if f not in df.columns]
    if missing_features:
        raise HTTPException(status_code=400, detail=f"Features not found in CSV: {missing_features}. CSV columns: {df.columns.tolist()}")

    # --- Train model ---
    X = df[features_list]
    y = df[label]

    model = LinearRegression()
    model.fit(X, y)

    # --- Save model ---
    save_model(model_name, model, features_list, label)

    # --- Log action ---
    log_action(user_id, "train", model_name)

    return {
        "status": "model trained successfully",
        "features": features_list,
        "label": label,
        "user": user_id
    }



class PredictRequest(BaseModel):
    user_id: str
    features: Dict[str, float]

@app.post("/predict/{model_name}")
async def predict(model_name: str, request: PredictRequest):
    model, metadata = load_model(model_name)
    required_features = metadata["features"]
    data = request.features

    # Check for missing features
    missing = [f for f in required_features if f not in data]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing features: {missing}")

    # Predict
    X = pd.DataFrame([data])
    pred = model.predict(X)[0]

    # Log usage
    log_action(request.user_id, "predict", model_name)

    return {"prediction": float(pred), "model": model_name}

@app.get("/models")
async def list_models():
    models = []
    for file in os.listdir(MODELS_DIR):
        if file.endswith("_meta.json"):
            with open(os.path.join(MODELS_DIR, file)) as f:
                models.append(json.load(f))
    return models

@app.get("/usage/{user_id}")
async def user_usage(user_id: str):
    summary = get_usage_summary(user_id)
    return {"user": user_id, **summary}


