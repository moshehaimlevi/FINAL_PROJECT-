import streamlit as st
import requests
from config import API_URL

st.title("Make Predictions")

token = st.session_state.get("token", None)
if not token:
    st.warning("Please login first")
    st.stop()

headers = {"Authorization": f"Bearer {token}"}

# Fetch models
models = requests.get(f"{API_URL}/models").json()["models"]

model_name = st.selectbox("Model Name", models)
data = st.text_input("Comma-separated input values")

if st.button("Predict"):
    payload = {"model_name": model_name, "data": data}

    if "knn" in model_name.lower():
        r = requests.post(f"{API_URL}/predict/knn", data=payload, headers=headers)
    else:
        r = requests.post(f"{API_URL}/predict/linearregression", data=payload, headers=headers)

    st.write(r.json())




    