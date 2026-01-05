"""
APPLICATION FLOW (Customer):
login
→ home
→ loan_list
→ gold_loan
→ gold_step1 (Personal Details)
→ gold_step2 (Gold Details)
→ gold_step3 (Loan & EMI)
→ gold_step4 (Document Upload)
→ gold_step5 (Summary & Submit)
→ gold_step6 (Confirmation)
"""
from core.doc_verification import (
    ocr_tool,
    ner_entity_extraction,
    identity_consistency_check
)

from flows.customer_flow import render_customer_flow
from flows.officer_flow import render_officer_flow

import streamlit as st
import csv
import os
import uuid
import re
from datetime import date

from core.masking import mask_dob, mask_pan, mask_mobile
from core.emi_agent import emi_calculation_agent


from core.validation import (
    valid_name,
    valid_mobile,
    valid_email,
    valid_pan,
    valid_aadhaar,
    valid_pin
)

# =============================
# SESSION STATE
# =============================
if "page" not in st.session_state:
    st.session_state.page = "login"

if "logged_customer" not in st.session_state:
    st.session_state.logged_customer = None

if "ornaments" not in st.session_state:
    st.session_state.ornaments = []

if "loan_summary" not in st.session_state:
    st.session_state.loan_summary = None

if "application_id" not in st.session_state:
    st.session_state.application_id = None

if "application_status" not in st.session_state:
    st.session_state.application_status = None

if "notifications" not in st.session_state:
    st.session_state.notifications = []

if "uploaded_document" not in st.session_state:
    st.session_state.uploaded_document = None

if "verification_result" not in st.session_state:
    st.session_state.verification_result = None


# =============================
# FILE PATHS
# =============================
CUSTOMER_FILE = "data/customers.csv"
OFFICER_FILE = "data/loan_officers.csv"


# =============================
# INITIALIZE FILES
# =============================
def init_files():
    if not os.path.exists(CUSTOMER_FILE):
        with open(CUSTOMER_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Customer_ID", "Full_Name", "DOB", "Gender",
                "Mobile", "Email", "Address",
                "PAN", "Aadhaar", "PIN"
            ])

    if not os.path.exists(OFFICER_FILE):
        with open(OFFICER_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Officer_ID", "Name", "EmpCode", "PIN"])
            writer.writerow(["OFF001", "Anita Sharma", "EMP1023", "9999"])

init_files()

# =============================
# UI CONFIG
# =============================
st.set_page_config(page_title="Gold Loan System", layout="centered")
st.title("🏦 Intelligent Loan Processing Assistant")
st.caption("Academic Demo | Policy-Driven UI | No Auto-Approval")

role = st.sidebar.selectbox("Select Role", ["Customer", "Loan Officer"])
st.divider()

if role == "Customer":
    render_customer_flow()
elif role == "Loan Officer":
    render_officer_flow()


# =============================
# FOOTER
# =============================
st.divider()
st.caption("⚠️ Academic demonstration only. No real banking data processed.")




