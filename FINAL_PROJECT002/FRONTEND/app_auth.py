import streamlit as st
import requests
from config import API_URL

st.title("User Registration / Login")

tab1, tab2 = st.tabs(["Register", "Login"])

def handle_response(res):
    """Show friendly messages based on backend response"""

    if res.get("status") != "OK":
        reason = res.get("reason") or res.get("detail") or "Unknown error"
        st.error(f"❌ Failed: {reason}")
        return

    # SUCCESS path
    if "token" in res:
        # login success
        st.session_state["token"] = res["token"]
        st.session_state["tokens"] = res.get("tokens", 0)
        st.success(f"✅ Logged in! Tokens: {res.get('tokens', 0)}")

    else:
        # registration success
        st.session_state["tokens"] = res.get("tokens", 5)
        st.success(f"✅ User registered! Tokens: {res.get('tokens', 5)}")


######################  Registration Tab ######################
with tab1:
    reg_email = st.text_input("Email", key="reg_email")
    reg_pwd = st.text_input("Password", type="password", key="reg_pwd")

    if st.button("Register"):
        if not reg_email or not reg_pwd:
            st.warning("Please enter both email and password")
        else:
            try:
                r = requests.post(
                    f"{API_URL}/user/create",
                    data={"email": reg_email, "pwd": reg_pwd}
                )
                st.write("DEBUG:", r.text)   # OPTIONAL REMOVE LATER
                handle_response(r.json())
            except Exception as e:
                st.error(f"Network error: {e}")


######################  Login Tab ######################
with tab2:
    log_email = st.text_input("Email", key="log_email")
    log_pwd = st.text_input("Password", type="password", key="log_pwd")

    if st.button("Login"):
        if not log_email or not log_pwd:
            st.warning("Please enter both email and password")
        else:
            try:
                r = requests.post(
                    f"{API_URL}/user/login",
                    data={"email": log_email, "pwd": log_pwd}
                )
                st.write("DEBUG:", r.text)   # OPTIONAL REMOVE LATER
                handle_response(r.json())
            except Exception as e:
                st.error(f"Network error: {e}")
