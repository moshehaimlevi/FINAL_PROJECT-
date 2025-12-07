import streamlit as st
import requests
from frontend.config import API_URL
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

st.title("Train Models")

token = st.session_state.get("token", None)
if not token:
    st.warning("Please login first")
    st.stop()

headers = {"Authorization": f"Bearer {token}"}

model_name = st.text_input("Model Name")
features = st.text_input("Features (comma-separated)")
label = st.text_input("Label Column")
uploaded_file = st.file_uploader("Upload CSV")

algorithm = st.selectbox("Model Type", ["Linear Regression", "KNN"])

if algorithm == "KNN":
    k = st.number_input("k", min_value=1, value=3)

if st.button("Train Model"):
    if uploaded_file:
        if algorithm == "Linear Regression":
            data = {
                "model_name": model_name,
                "features": features,
                "label": label
            }
            files = {"file": uploaded_file}
            r = requests.post(f"{API_URL}/create/linearregression",
                              data=data, files=files, headers=headers)
            st.write(r.json())

        else:
            data = {
                "model_name": model_name,
                "features": features,
                "label": label,
                "k": k
            }
            files = {"file": uploaded_file}
            r = requests.post(f"{API_URL}/create/knn",
                              data=data, files=files, headers=headers)
            st.write(r.json())
