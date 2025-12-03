import streamlit as st
import requests
from config import API_URL

st.title("User Registration / Login")

tab1, tab2 = st.tabs(["Register", "Login"])

with tab1:
    email = st.text_input("Email", key="reg_email")
    pwd = st.text_input("Password", type="password", key="reg_pwd")

    if st.button("Register"):
        r = requests.post(f"{API_URL}/user/create",
                          data={"email": email, "pwd": pwd})
        st.write(r.json())

with tab2:
    email = st.text_input("Email", key="log_email")
    pwd = st.text_input("Password", type="password", key="log_pwd")

    if st.button("Login"):
        r = requests.post(f"{API_URL}/user/login",
                          data={"email": email, "pwd": pwd})
        res = r.json()
        st.write(res)

        if res["status"] == "OK":
            st.session_state["token"] = res["token"]
            st.success("Logged in successfully")