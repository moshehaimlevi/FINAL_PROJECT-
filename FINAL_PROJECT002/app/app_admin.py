import streamlit as st
import requests
import pandas as pd
from config import API_URL

st.title("Admin Dashboard")

# Fetch users & tokens
users = requests.get(f"{API_URL}/admin/users").json()
st.subheader("Users & Tokens")
st.table(pd.DataFrame(users))

# Fetch models
models = requests.get(f"{API_URL}/models").json()
st.subheader("Available Models")
st.write(models)
