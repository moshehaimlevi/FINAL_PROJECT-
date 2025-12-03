from fastapi import FastAPI, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.neighbors import KNeighborsRegressor
from db import get_conn
from models_ml import save_model, load_model
from auth import create_token, verify_token, hash_pwd, verify_pwd
from logging_config import logger

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

####################### TOKENS #######################
def use_tokens(email, amount):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE ml_user
        SET tokens = tokens - %s
        WHERE email=%s AND tokens >= %s
        RETURNING tokens;
    """, (amount, email, amount))

    row = cur.fetchone()
    conn.commit()
    return row is not None

####################### USER CREATION #######################
@app.post("/user/create")
async def create_user(email: str = Form(...), pwd: str = Form(...)):
    conn = get_conn()
    cur = conn.cursor()

    hashed = hash_pwd(pwd)

    try:
        cur.execute(
            "INSERT INTO ml_user (email, pwd, tokens) VALUES (%s, %s, 20)",
            (email, hashed)
        )
        conn.commit()
        logger.info(f"User created: {email}")
        return {"status": "OK"}
    except:
        return {"status": "FAIL", "reason": "User exists"}

####################### USER LOG-IN #######################
@app.post("/user/login")
async def login(email: str = Form(...), pwd: str = Form(...)):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT pwd FROM ml_user WHERE email=%s", (email,))
    row = cur.fetchone()

    if not row or not verify_pwd(pwd, row[0]):
        return {"status": "FAIL"}

    token = create_token({"sub": email})
    return {"status": "OK", "token": token}

####################### TRAINING THE MODEL ( LIN-REG ) #######################
@app.post("/create/linearregression")
async def create_lr(
        model_name: str = Form(...),
        features: str = Form(...),
        label: str = Form(...),
        file: UploadFile = File(...),
        email: str = Depends(verify_token)
):
    if not use_tokens(email, 1):
        return {"status": "NO_TOKENS"}

    df = pd.read_csv(file.file)
    X = df[features.split(",")]
    y = df[label]

    model = LinearRegression().fit(X, y)
    save_model(model_name, model, {"features": features.split(","), "label": label})

    logger.info(f"{email} trained LR model {model_name}")
    return {"status": "OK"}

####################### PREDICTING THE MODEL ( LIN-REG ) #######################
@app.post("/predict/linearregression")
async def predict_lr(
        model_name: str = Form(...),
        data: str = Form(...),
        email: str = Depends(verify_token)
):
    if not use_tokens(email, 5):
        return {"status": "NO_TOKENS"}

    model, meta = load_model(model_name)

    values = list(map(float, data.split(",")))
    df = pd.DataFrame([values], columns=meta["features"])

    pred = model.predict(df)[0]
    return {"prediction": float(pred)}

####################### TRAINING THE KNN #######################
@app.post("/create/knn")
async def create_knn(
        model_name: str = Form(...),
        features: str = Form(...),
        label: str = Form(...),
        k: int = Form(3),
        file: UploadFile = File(...),
        email: str = Depends(verify_token)
):
    if not use_tokens(email, 1):
        return {"status": "NO_TOKENS"}

    df = pd.read_csv(file.file)
    X = df[features.split(",")]
    y = df[label]

    model = KNeighborsRegressor(n_neighbors=k).fit(X, y)
    save_model(model_name, model, {"features": features.split(","), "label": label})

    logger.info(f"{email} trained KNN model {model_name}")
    return {"status": "OK"}

####################### PREDICTING THE KNN #######################
@app.post("/predict/knn")
async def predict_knn(
        model_name: str = Form(...),
        data: str = Form(...),
        email: str = Depends(verify_token)
):
    if not use_tokens(email, 5):
        return {"status": "NO_TOKENS"}

    model, meta = load_model(model_name)
    values = list(map(float, data.split(",")))

    df = pd.DataFrame([values], columns=meta["features"])
    pred = model.predict(df)[0]

    return {"prediction": float(pred)}

####################### LISTING ALL USERS & TOKENS #######################
@app.get("/admin/users")
async def admin_users():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT email, tokens FROM ml_user")
    rows = cur.fetchall()
    return [{"email": r[0], "tokens": r[1]} for r in rows]

####################### LISTING ALL MODELS #######################
import os
@app.get("/models")
async def list_models():
    files = os.listdir("models")
    models = [f.replace(".pkl", "") for f in files if not f.endswith("_meta.pkl")]
    return {"models": models}








