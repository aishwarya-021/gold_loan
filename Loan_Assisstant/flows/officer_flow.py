import streamlit as st
import csv
from datetime import date, datetime

# =============================
# FILE PATHS
# =============================
APP_FILE = "data/applications.csv"
AUDIT_FILE = "data/audit_logs.csv"
VISIT_FILE = "data/branch_visits.csv"
NOTIFY_FILE = "data/notifications.csv"
OFFICER_FILE = "data/loan_officers.csv"


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
        return


    # -----------------------------
    # DASHBOARD
    # -----------------------------
    st.subheader("📋 Officer Dashboard")
    st.caption("AI assists with explanations only — decisions remain human.")


    # -----------------------------
    # PENDING APPLICATIONS
    # -----------------------------
    st.markdown("## 🗂 Pending Applications")

    pending_apps = []
    with open(APP_FILE, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["Status"] in ["SUBMITTED", "UNDER_REVIEW"]:
                pending_apps.append(r)


    if not pending_apps and not st.session_state.evaluated_app:
        st.info("No pending applications.")



    for i, app in enumerate(pending_apps):
        with st.container():
            st.markdown(f"""
            **Application ID:** {app['Application_ID']}  
            **Customer ID:** {app['Customer_ID']}  
            **Amount:** ₹{app['Requested_Amount']}  
            **Tenure:** {app['Tenure']} months  
            **Gold:** {app['Net_Weight']} g | {app['Carat']}K
            """)

            if st.button("Evaluate", key=f"eval_{i}"):
                st.session_state.evaluated_app = app
                update_application_status(app["Application_ID"], "UNDER_REVIEW")
                st.rerun()

        st.divider()


    # -----------------------------
    # LOAD SELECTED APPLICATION
    # -----------------------------
    if not st.session_state.evaluated_app:
        return

    app = st.session_state.evaluated_app

    st.info(f"🕒 Reviewing Application: {app['Application_ID']} (Status: {app['Status']})")


    # -----------------------------
    # CUSTOMER MASTER DETAILS
    # -----------------------------
    customer_data = None

    with open("data/customers.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["Customer_ID"] == app["Customer_ID"]:
                customer_data = r
                break
    if not customer_data:
        st.error("Customer master data not found. Escalate to operations.")
        return

    st.markdown("## 🧾 Identity Verification (Officer Review)")


    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 👤 Customer Provided")
        st.write("**Name:**", customer_data["Full_Name"])
        st.write("**DOB:**", customer_data["DOB"])
        st.write("**Aadhaar:**", "XXXX XXXX " + customer_data["Aadhaar"][-4:])

    with col2:
        st.markdown("### 📄 Document Extracted (AI)")
        st.write("**Name:**", app.get("Extracted_Name", "Not detected"))
        st.write("**DOB:**", app.get("Extracted_DOB", "Not detected"))
        st.write(
            "**Aadhaar:**",
            "XXXX XXXX " + app.get("Extracted_ID_Last4", "XXXX")
        )

    # -----------------------------
    # SMART AGENT ANALYSIS (RULE-BASED)
    # -----------------------------
    st.markdown("## 🧠 Agent Analysis")

    ex_name = app.get("Extracted_Name")
    ex_dob = app.get("Extracted_DOB")
    ex_id = app.get("Extracted_ID_Last4")

    cust_name = customer_data["Full_Name"]
    cust_dob = customer_data["DOB"]
    cust_id_last4 = customer_data["Aadhaar"][-4:]

    # ---------- REQUIRED FIELDS CHECK
    if ex_name and ex_dob and ex_id:
        st.success("✅ Required identity fields detected from document")
        required_ok = True
    else:
        st.error("❌ Required identity fields missing in document")
        required_ok = False

    # ---------- MATCH CHECKS
    name_match = ex_name and ex_name.lower() in cust_name.lower()
    dob_match = ex_dob and ex_dob in cust_dob
    id_match = ex_id and ex_id == cust_id_last4

    # ---------- RISK LOGIC
    if name_match and dob_match and id_match:
        risk = "LOW"
        risk_msg = "All identity fields match customer records."
    elif name_match and id_match:
        risk = "MEDIUM"
        risk_msg = "Name and ID match, but DOB mismatch or missing."
    else:
        risk = "HIGH"
        risk_msg = "Identity mismatch or insufficient document verification."

    # ---------- DISPLAY RESULTS
    st.write("🔍 Name Match:", "✅" if name_match else "❌")
    st.write("🔍 DOB Match:", "✅" if dob_match else "❌")
    st.write("🔍 ID Match:", "✅" if id_match else "❌")

    if risk == "LOW":
        st.success(f"🟢 Risk Level: LOW — {risk_msg}")
    elif risk == "MEDIUM":
        st.warning(f"🟡 Risk Level: MEDIUM — {risk_msg}")
    else:
        st.error(f"🔴 Risk Level: HIGH — {risk_msg}")


        # ---------------- COMPARISON ----------------
    st.markdown("## 📊 Application vs Policy Comparison")
    st.table([
        {"Parameter": "Requested Amount", "Application": app["Requested_Amount"], "Policy": "Within LTV"},
        {"Parameter": "Gold Weight", "Application": app["Net_Weight"], "Policy": "Verified"},
        {"Parameter": "Gold Purity", "Application": app["Carat"], "Policy": "18K–24K"},
        {"Parameter": "Tenure", "Application": app["Tenure"], "Policy": "Allowed"},
        {"Parameter": "Risk", "Application": risk, "Policy": "Escalate if HIGH"}
    ])




    # -----------------------------
    # OFFICER DECISION
    # -----------------------------
    st.markdown("## 🧑‍⚖️ Officer Verification Decision")

    verification = st.radio(
    "Officer Decision",
    ["Approve for Branch Visit", "Reject Application"]
    )

    rejection_reason = None
    remarks = ""

    if verification == "Reject Application":

        rejection_reason = st.selectbox(
            "Select rejection reason",
            [
                "Identity mismatch (Name / DOB / Aadhaar)",
                "Document unreadable or blurred",
                "Invalid or expired document",
                "Suspicious / tampered document",
                "Gold details mismatch with application",
                "Other compliance or risk concern"
            ]
        )

        remarks = st.text_area(
            "Additional remarks (optional)",
            placeholder="Any extra explanation for customer or audit"
        )


    # CASE- 1   [VERIFIED]

    if verification == "Approve for Branch Visit":

        if risk == "HIGH":
            st.error("High-risk case. Manual escalation required.")
            return

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
                    f"Branch visit scheduled at {branch} on {visit_date} at {visit_time}.",
                    datetime.now().isoformat()
                ])

            with open(AUDIT_FILE, "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow([
                    datetime.now().isoformat(),
                    st.session_state.officer_name,
                    app["Application_ID"],
                    "IDENTITY_MATCH_CONFIRMED",
                    "Proceed to branch visit"
                ])

            st.success("✅ Slot booked and customer notified")
            st.session_state.evaluated_app = None
            st.rerun()
   
    # CASE- 2   [REJECTION]

    if verification == "Reject Application":

        if st.button("Reject Application"):

            final_reason = rejection_reason
            if remarks.strip():
                final_reason += f" | Officer remarks: {remarks}"

            update_application_status(app["Application_ID"], "REJECTED")

            # ---- Notify Customer
            with open(NOTIFY_FILE, "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow([
                    app["Customer_ID"],
                    app["Application_ID"],
                    "LOAN_OFFICER",
                    f"Loan application rejected. Reason: {final_reason}",
                    datetime.now().isoformat()
                ])

            # ---- Audit Log (internal)
            with open(AUDIT_FILE, "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow([
                    datetime.now().isoformat(),
                    st.session_state.officer_name,
                    app["Application_ID"],
                    "APPLICATION_REJECTED",
                    final_reason
                ])

            st.error("❌ Application rejected and customer notified")
            st.session_state.evaluated_app = None
            st.rerun()

