import streamlit as st
import requests
import pandas as pd
from frontend.config import API_URL
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

st.title("Admin Dashboard")

users = requests.get(f"{API_URL}/admin/users").json()
st.subheader("Users & Tokens")

if isinstance(users, list):
    st.table(pd.DataFrame(users))

elif "users" in users:
    st.table(pd.DataFrame(users["users"]))


else:
    st.table(pd.DataFrame([users]))