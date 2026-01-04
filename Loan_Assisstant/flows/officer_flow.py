import streamlit as st
import csv
import os
from datetime import date, datetime

# =============================
# FILE PATH SAFETY
# =============================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

APP_FILE = os.path.join(DATA_DIR, "applications.csv")
AUDIT_FILE = os.path.join(DATA_DIR, "audit_logs.csv")
VISIT_FILE = os.path.join(DATA_DIR, "branch_visits.csv")
NOTIFY_FILE = os.path.join(DATA_DIR, "notifications.csv")
OFFICER_FILE = os.path.join(DATA_DIR, "loan_officers.csv")

# =============================
# FILE INITIALIZATION
# =============================
def ensure_file(path, headers):
    if not os.path.exists(path):
        with open(path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(headers)

# Ensure all required files exist
ensure_file(APP_FILE, [
    "Application_ID","Customer_ID","Requested_Amount",
    "Tenure","Net_Weight","Carat",
    "Status","Document_Failure_Reason","Created_At"
])

ensure_file(OFFICER_FILE, ["Officer_ID","Name","EmpCode","PIN"])
ensure_file(NOTIFY_FILE, ["Customer_ID","Application_ID","Sender","Message","Created_At"])
ensure_file(AUDIT_FILE, ["Timestamp","Actor","Application_ID","Action","Remarks"])
ensure_file(VISIT_FILE, ["Application_ID","Branch","Branch_Code","Visit_Date","Visit_Time","Status"])

# =============================
# HELPERS
# =============================
def update_application_status(application_id, new_status):
    with open(APP_FILE, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for r in rows:
        if r["Application_ID"] == application_id:
            r["Status"] = new_status

    with open(APP_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def branches():
    return {
        "Mumbai Main Branch": "BR001",
        "Delhi Central Branch": "BR002",
        "Bengaluru City Branch": "BR003"
    }

# =============================
# SAFE AGENTS (EXPLANATION ONLY)
# =============================
def document_validation_agent(app):
    required = ["Requested_Amount", "Net_Weight", "Carat"]
    return [f for f in required if not app.get(f)]


def policy_compliance_agent(app):
    return 0.82, (
        "The requested loan amount falls within permissible "
        "Loan-to-Value thresholds for the given gold purity."
    )


def risk_evaluation_agent(app):
    amount = float(app["Requested_Amount"])
    if amount > 500000:
        return "HIGH", "Requested amount exceeds retail gold loan limits."
    elif amount > 200000:
        return "MEDIUM", "Moderate exposure based on loan amount."
    return "LOW", "Low exposure based on conservative loan amount."

# =============================
# OFFICER FLOW
# =============================
def render_officer_flow():

    # -----------------------------
    # SESSION STATE
    # -----------------------------
    if "officer_logged_in" not in st.session_state:
        st.session_state.officer_logged_in = False

    if "officer_name" not in st.session_state:
        st.session_state.officer_name = None

    if "evaluated_app" not in st.session_state:
        st.session_state.evaluated_app = None

    # -----------------------------
    # LOGIN
    # -----------------------------
    if not st.session_state.officer_logged_in:
        st.subheader("🔐 Loan Officer Login")

        emp = st.text_input("Employee Code")
        pin = st.text_input("PIN", type="password")

        if st.button("Login"):
            with open(OFFICER_FILE, newline="", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    if r["EmpCode"] == emp and r["PIN"] == pin:
                        st.session_state.officer_logged_in = True
                        st.session_state.officer_name = r["Name"]
                        st.success(f"Welcome {r['Name']}")
                        st.rerun()
            st.error("Invalid credentials")
        return

    # -----------------------------
    # DASHBOARD
    # -----------------------------
    st.subheader("📋 Officer Dashboard")
    st.caption("AI assists with explanations only — decisions remain human.")

    # -----------------------------
    # LOAD APPLICATIONS
    # -----------------------------
    with open(APP_FILE, newline="", encoding="utf-8") as f:
        all_apps = list(csv.DictReader(f))

    pending_apps = [
        r for r in all_apps
        if r["Status"] in ["SUBMITTED", "UNDER_REVIEW"]
    ]

    st.markdown("## 🗂 Pending Applications")

    if not pending_apps:
        st.info("No pending applications.")
    else:
        for i, app in enumerate(pending_apps):
            with st.container():
                st.markdown(f"""
                **Application ID:** {app['Application_ID']}  
                **Customer ID:** {app['Customer_ID']}  
                **Amount:** ₹{app['Requested_Amount']}  
                **Tenure:** {app['Tenure']} months  
                **Gold:** {app['Net_Weight']}g | {app['Carat']}K  
                **Status:** {app['Status']}
                """)

                if st.button("Evaluate", key=f"eval_{i}"):
                    st.session_state.evaluated_app = app
                    st.rerun()
            st.divider()

    # -----------------------------
    # LOAD SELECTED APPLICATION
    # -----------------------------
    if not st.session_state.evaluated_app:
        return

    app = st.session_state.evaluated_app

    # -----------------------------
    # AGENT ANALYSIS
    # -----------------------------
    st.markdown("## 🧠 Agent Analysis")

    missing = document_validation_agent(app)
    policy_score, policy_msg = policy_compliance_agent(app)
    risk, risk_msg = risk_evaluation_agent(app)

    if not missing:
        st.success("✅ Required fields present")
    else:
        st.error(f"❌ Missing fields: {', '.join(missing)}")

    st.info(f"📘 Policy Score: {policy_score}")
    st.caption(policy_msg)

    st.warning(f"⚠️ Risk Level: {risk}")
    st.caption(risk_msg)

    # -----------------------------
    # OFFICER DECISION
    # -----------------------------
    st.markdown("## 🧑‍⚖️ Officer Decision")

    decision = st.radio(
        "Decision",
        ["Proceed to Branch Visit", "Reject Application"]
    )

    remarks = st.text_area(
        "Remarks (visible to customer)",
        placeholder="Mandatory if rejecting the application"
    )

    # -----------------------------
    # REJECT APPLICATION
    # -----------------------------
    if decision == "Reject Application" and st.button("Reject Application"):

        if not remarks.strip():
            st.warning("Please provide rejection reason.")
            return

        update_application_status(app["Application_ID"], "REJECTED")

        with open(NOTIFY_FILE, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                app["Customer_ID"],
                app["Application_ID"],
                "LOAN_OFFICER",
                f"Loan application rejected. Reason: {remarks}",
                datetime.now().isoformat()
            ])

        with open(AUDIT_FILE, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                datetime.now().isoformat(),
                st.session_state.officer_name,
                app["Application_ID"],
                "REJECTED",
                remarks
            ])

        st.error("❌ Application rejected and customer notified")
        st.session_state.evaluated_app = None
        st.rerun()

    # -----------------------------
    # PROCEED TO BRANCH VISIT
    # -----------------------------
    if decision == "Proceed to Branch Visit" and risk != "HIGH":

        st.markdown("### 🏦 Schedule Branch Visit")

        with st.form("slot_form"):
            branch = st.selectbox("Branch", list(branches().keys()))
            visit_date = st.date_input("Visit Date", min_value=date.today())
            visit_time = st.time_input("Visit Time")
            submit = st.form_submit_button("Confirm Slot")

        if submit:
            update_application_status(app["Application_ID"], "VISIT_SCHEDULED")

            with open(VISIT_FILE, "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow([
                    app["Application_ID"],
                    branch,
                    branches()[branch],
                    visit_date.isoformat(),
                    visit_time.strftime("%H:%M"),
                    "BRANCH_VISIT_SCHEDULED"
                ])

            with open(NOTIFY_FILE, "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow([
                    app["Customer_ID"],
                    app["Application_ID"],
                    "SYSTEM",
                    f"Please visit {branch} on {visit_date} at {visit_time} for gold verification.",
                    datetime.now().isoformat()
                ])

            with open(AUDIT_FILE, "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow([
                    datetime.now().isoformat(),
                    st.session_state.officer_name,
                    app["Application_ID"],
                    "VISIT_SCHEDULED",
                    f"Branch={branch}, Date={visit_date}, Time={visit_time}, Risk={risk}"
                ])

            st.success("✅ Branch visit scheduled & customer notified")
            st.session_state.evaluated_app = None
            st.rerun()
