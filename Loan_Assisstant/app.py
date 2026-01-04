import streamlit as st
import os
import sys

# ==================================================
# PAGE CONFIG (MUST BE FIRST)
# ==================================================
st.set_page_config(
    page_title="Gold Loan Assistant",
    layout="wide"
)

# ==================================================
# PROJECT ROOT SAFETY
# Ensures Streamlit runs from project root
# ==================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

# ==================================================
# SAFE IMPORTS (NO BLANK SCREENS)
# ==================================================
customer_error = None
officer_error = None

try:
    from flows.customer_flow import render_customer_flow
except Exception as e:
    render_customer_flow = None
    customer_error = e

try:
    from flows.officer_flow import render_officer_flow
except Exception as e:
    render_officer_flow = None
    officer_error = e

# ==================================================
# APP HEADER
# ==================================================
st.title("🏦 Gold Loan Assistant")
st.caption("Customer & Loan Officer Workflow")

# ==================================================
# SIDEBAR NAVIGATION
# (This is NOT st.session_state.page)
# ==================================================
st.sidebar.title("Navigation")

portal = st.sidebar.radio(
    "Select Portal",
    ["Customer", "Loan Officer"]
)

# ==================================================
# ROUTING
# ==================================================
if portal == "Customer":

    st.subheader("👤 Customer Portal")

    if render_customer_flow is None:
        st.error("❌ Customer module failed to load")
        st.exception(customer_error)
    else:
        try:
            render_customer_flow()
        except Exception as e:
            st.error("❌ Customer flow crashed during execution")
            st.exception(e)

else:

    st.subheader("🧑‍💼 Loan Officer Portal")

    if render_officer_flow is None:
        st.error("❌ Officer module failed to load")
        st.exception(officer_error)
    else:
        try:
            render_officer_flow()
        except Exception as e:
            st.error("❌ Officer flow crashed during execution")
            st.exception(e)

# ==================================================
# FOOTER
# ==================================================
st.sidebar.markdown("---")
st.sidebar.caption("Gold Loan Assistant • Streamlit Application")
