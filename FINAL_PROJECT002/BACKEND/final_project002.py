from fastapi import FastAPI, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.neighbors import KNeighborsRegressor
import os
from backend.db import get_conn
from backend.models import save_model, load_model
from backend.authorize import create_token, verify_token, hash_pwd, verify_pwd
from backend.logging_config import logger


app = FastAPI(title="ML Model API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

####################### TOKEN USAGE HELPER #######################
def use_tokens(email: str, amount: int) -> bool:
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
    cur.close()
    return row is not None

####################### USER ENDPOINTS #######################

############# USER CREATE ################
@app.post("/user/create", tags=["User"])
async def create_user(email: str = Form(...), pwd: str = Form(...)):
    import traceback
    try:
        conn = get_conn()
        cur = conn.cursor()

        hashed = hash_pwd(pwd)

        # Give new users 15 tokens
        cur.execute(
            "INSERT INTO ml_user (email, pwd, tokens) VALUES (%s, %s, %s)",
            (email, hashed, 15)
        )
        conn.commit()

        cur.close()
        conn.close()

        # Return 15 tokens to Streamlit
        return {"status": "OK", "tokens": 15}

    except Exception as e:
        return {"status": "FAIL", "reason": str(e)}

############### USER LOGIN ###############
@app.post("/user/login", tags=["User"])
async def login(email: str = Form(...), pwd: str = Form(...)):
    conn = get_conn()
    cur = conn.cursor()

    # Fetch password + current tokens
    cur.execute("SELECT pwd, tokens FROM ml_user WHERE email=%s", (email,))
    row = cur.fetchone()

    if not row or not verify_pwd(pwd, row[0]):
        cur.close()
        return {"status": "FAIL", "reason": "Invalid email or password"}

    current_tokens = row[1]

    # Add 5 tokens per login
    new_token_balance = current_tokens + 5

    cur.execute(
        "UPDATE ml_user SET tokens=%s WHERE email=%s",
        (new_token_balance, email)
    )
    conn.commit()

    # Generate JWT
    token = create_token({"sub": email})

    cur.close()
    conn.close()


    return {
        "status": "OK",
        "token": token,
        "tokens": new_token_balance
    }

####################### MODEL TRAINING / PREDICTION #######################
@app.post("/create/linearregression", tags=["LinearRegression"])
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

@app.post("/predict/linearregression", tags=["LinearRegression"])
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

@app.post("/create/knn", tags=["KNN"])
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

@app.post("/predict/knn", tags=["KNN"])
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

####################### ADMIN / MODEL LISTING #######################
@app.get("/admin/users", tags=["Admin"])
async def admin_users():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT email, tokens FROM ml_user")
    rows = cur.fetchall()
    cur.close()
    return [{"email": r[0], "tokens": r[1]} for r in rows]

@app.get("/models", tags=["Models"])
async def list_models():
    files = os.listdir("models")  # Relative to project root
    models = [f.replace(".pkl", "") for f in files if not f.endswith("_meta.pkl")]
    return {"models": models}






