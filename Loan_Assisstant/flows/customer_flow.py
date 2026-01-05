"""
Customer Flow Responsibility:
- Authentication (login/register)
- Loan selection
- Gold loan application (Steps 1–6)
- Document upload & verification trigger
- Application submission & confirmation

NOTE:
Final approval is always done by Loan Officer.
"""

import streamlit as st
import csv
import uuid
import os
from datetime import date, datetime

from core.vision_kyc import extract_identity_from_image
from core.config import GOLD_RATE_PER_GRAM, MAX_LTV, PURITY_FACTOR
from core.masking import mask_dob, mask_pan, mask_mobile
from core.emi_agent import emi_calculation_agent
from core.doc_verification import (
    ocr_tool,
    ner_entity_extraction,
    identity_consistency_check
)

from core.validation import *

CUSTOMER_FILE = "data/customers.csv"

def render_customer_flow():

    # ---------- LOGIN ----------
    if st.session_state.page == "login":
        customer_type = st.radio("Customer Type", ["New Customer", "Existing Customer"])

        if customer_type == "New Customer":
            st.subheader("🆕 New Customer Registration")

            name = st.text_input("Full Name")
            dob = st.date_input("Date of Birth", min_value=date(1950, 1, 1))
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            mobile = st.text_input("Mobile Number")
            email = st.text_input("Email")
            address = st.text_area("Residential Address")
            pan = st.text_input("PAN").upper()
            aadhaar = st.text_input("Aadhaar")
            pin = st.text_input("Create 4-digit PIN", type="password")

            if st.button("Register"):
                errors = []

                if not valid_name(name): errors.append("Invalid Name")
                if not valid_mobile(mobile): errors.append("Invalid Mobile")
                if not valid_email(email): errors.append("Invalid Email")
                if not valid_pan(pan): errors.append("Invalid PAN")
                if not valid_aadhaar(aadhaar): errors.append("Invalid Aadhaar")
                if not valid_pin(pin): errors.append("Invalid PIN")

                if errors:
                    for e in errors:
                        st.error(e)
                else:
                    customer_id = str(uuid.uuid4())

                    with open(CUSTOMER_FILE, "a", newline="", encoding="utf-8") as f:
                        csv.writer(f).writerow([
                            customer_id,
                            name,
                            dob.strftime("%Y-%m-%d"),
                            gender,
                            mobile,
                            email,
                            address,
                            pan,
                            aadhaar,
                            pin
                        ])

                    # ✅ AUTO-LOGIN AFTER REGISTRATION
                    st.session_state.logged_customer = {
                        "Customer_ID": customer_id,
                        "Full_Name": name,
                        "DOB": dob.strftime("%Y-%m-%d"),
                        "Gender": gender,
                        "Mobile": mobile,
                        "Email": email,
                        "Address": address,
                        "PAN": pan,
                        "Aadhaar": aadhaar
                    }

                    st.session_state.page = "home"
                    st.rerun()

        else:
            st.subheader("🔐 Existing Customer Login")
            mobile = st.text_input("Registered Mobile Number")
            pin = st.text_input("Safety PIN", type="password")

            if st.button("Login"):
                with open(CUSTOMER_FILE, encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        if row["Mobile"] == mobile and row["PIN"] == pin:
                            st.session_state.logged_customer = row
                            st.session_state.page = "home"
                            st.rerun()
                st.error("Invalid credentials")

    # ---------- HOME ----------
    elif st.session_state.page == "home":

        # -----------------------------
        # Application Status Banner
        # -----------------------------
        if st.session_state.application_status:
            st.info(
                f"📌 Application Status: {st.session_state.application_status}"
            )
        # -----------------------------
        # Notifications from Loan Officer
        # -----------------------------
        NOTIFY_FILE = "data/notifications.csv"
        customer_id = st.session_state.logged_customer["Customer_ID"]

        notifications = []
        if os.path.exists(NOTIFY_FILE):
            with open(NOTIFY_FILE, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    if row["Customer_ID"] == customer_id:
                        notifications.append(row)

        if notifications:
            st.markdown("### 🔔 Notifications")
            for n in reversed(notifications):
                st.success(
                    f"""
                    **Application ID:** {n['Application_ID']}  
                    **Message:** {n['Message']}  
                    🕒 {n['Created_At']}
                    """
                )
        else:
            st.info("No notifications yet. Please check back later.")



        c = st.session_state.logged_customer
        st.subheader("👤 Customer Details")
        st.write(f"**Name:** {c['Full_Name']}")
        st.write(f"**Aadhaar:** XXXX XXXX {c['Aadhaar'][-4:]}")
        st.write(f"**PAN:** {c['PAN']}")

        if st.button("📄 Loans"):
            st.session_state.page = "loan_list"
            st.rerun()

    # ---------- LOAN LIST ----------
    elif st.session_state.page == "loan_list":
        loan = st.radio(
            "Select Loan Type",
            ["Gold Loan", "Personal Loan", "Education Loan", "Home Loan"]
        )
        if loan == "Gold Loan" and st.button("Proceed"):
            st.session_state.page = "gold_loan"
            st.rerun()

    # ---------- GOLD LOAN INFO ----------
    elif st.session_state.page == "gold_loan":
        st.subheader("💰 Gold Loan")
        st.caption("Apply for a gold loan in 4 easy steps")

        if st.button("Apply Now"):
            st.session_state.page = "gold_step1"
            st.rerun()

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Features", "Eligibility", "Documents",
            "Interest & Fees", "Security & Gold Handling"
        ])

        with tab1:
            st.markdown("""
            • Loan against pledge of gold jewellery  
            • Demand loan for personal / business / medical needs  
            • Maximum tenure up to **12 months**  
            • Loan amount based on **net weight & purity (22 carat)**  
            • Loan-to-Value (LTV) as per **RBI norms**  
            • Bullet repayment & scheme-based repayment options  
            """)

        with tab2:
            st.markdown("""
            • Individuals aged **18 years and above**  
            • Borrower must be the **lawful owner** of the gold  
            • Ownership declaration mandatory  
            • KYC compliance as per RBI guidelines  
            • Third-party pledge allowed only with **Notarized POA**  
            """)

        with tab3:
            st.markdown("""
            • Gold Loan Application Form  
            • Demand Promissory Note  
            • Loan Agreement  

            **Identity Proof:** Aadhaar / Passport / DL / Voter ID  
            **Address Proof:** Utility bill / Tax receipt / Govt letter  
            • Aadhaar mandatory for **e-KYC / Offline KYC**  
            """)

        with tab4:
            st.markdown("""
            **Interest**  
            • Calculated on actual days outstanding  
            • Minimum interest of **7 days**  
            • Year reckoned as **365 days**  

            **Charges**  
            • Processing charges  
            • Appraisal charges  
            • Penal charges for delay  
            • Auction & safe-keeping charges  
            • Stamp duty as per State laws  
            """)

        with tab5:
            st.markdown("""
            • Only **22 carat gold jewellery** accepted  
            • Net weight after deducting stones / alloys  
            • Appraisal through approved purity methods  
            • Jewellery stored in **strong rooms / FBR safes**  
            • Branches secured with **CCTV & alarms**  
            • Items in negative list not accepted as security  
            • Jewellery released only after **full repayment**  
            """)

        st.button("⬅ Back", on_click=lambda: st.session_state.update(page="loan_list"))

    # ---------- STEP 1 (FULLY RESTORED) ----------
    elif st.session_state.page == "gold_step1":
        c = st.session_state.logged_customer

        st.markdown("## GOLD LOAN — Step 1 of 6")
        st.markdown("### Personal Details")
        st.caption("Home Branch: PALAMANER BAZAR | Branch Code: 16429")
        st.divider()

        st.markdown(f"**Name**  \n{c['Full_Name']}")
        st.markdown(f"**Date of Birth**  \n{mask_dob(c['DOB'])}")
        st.markdown(f"**Gender**  \n{c['Gender']}")
        st.markdown(f"**PAN**  \n{mask_pan(c['PAN'])}")
        st.markdown(f"**Mobile Number**  \n{mask_mobile(c['Mobile'])}")
        st.markdown(f"**Permanent Address**  \n{c['Address']}")

        st.selectbox(
            "Residential Type",
            ["Employer Provided Accommodation", "Own House",
             "Parental House", "Rented/Others"]
        )

        st.selectbox(
            "Occupation Type",
            ["Businessman/Professional", "Housewife/Retired/Others",
             "Salaried - CSP", "Salaried - Non CSP"]
        )

        st.number_input("Net Monthly Income (in INR)", min_value=0, step=1000)

        confirm = st.checkbox(
            "I confirm that my personal details mentioned above are correct."
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Back"):
                st.session_state.page = "gold_loan"
                st.rerun()

        with col2:
            if st.button("Next"):
                if not confirm:
                    st.error("Please confirm details")
                else:
                    st.session_state.page = "gold_step2"
                    st.rerun()

    # ---------- STEP 2 (MULTIPLE ORNAMENTS) ----------
    elif st.session_state.page == "gold_step2":

        st.markdown("## GOLD LOAN — Step 2 of 6")

        st.markdown("### Gold Ornament Details")
        st.caption("Add one or more gold ornaments")
        st.divider()

        ornament_type = st.selectbox("Ornament Type", [
            "Anklet", "Any Other", "Bangle", "Bracelet", "Chain",
            "Ear ring", "Gold Coin", "Locket", "Mang tika",
            "Necklace", "Nose ring", "Ring", "Toe ring"
        ])

        col1, col2 = st.columns(2)
        with col1:
            qty = st.selectbox("Qty. (2 for Pair)", list(range(1, 17)))
        with col2:
            carat = st.selectbox("Carat", [18, 20, 22, 24])

        net_weight = st.number_input("Net Weight (g)", min_value=0.0, step=0.1)

        if st.button("➕ Add Ornament"):
            if net_weight > 0:
                st.session_state.ornaments.append({
                    "Ornament": ornament_type,
                    "Qty": qty,
                    "Carat": carat,
                    "Weight (g)": net_weight
                })
                st.success("Ornament added")
            else:
                st.error("Net weight must be greater than zero")

        if st.session_state.ornaments:
            st.subheader("Added Ornaments")
            st.table(st.session_state.ornaments)
            total_weight = sum(o["Weight (g)"] for o in st.session_state.ornaments)
            st.info(f"**Total Net Weight:** {total_weight} g")

        certify = st.checkbox(
            "I certify that above gold ornament(s) are my bonafide property."
        )

        colb1, colb2 = st.columns(2)
        with colb1:
            if st.button("Back"):
                st.session_state.page = "gold_step1"
                st.rerun()

        with colb2:
            if st.button("Next"):
                if certify and st.session_state.ornaments:

                    # ✅ Calculate total net weight
                    total_weight = sum(
                        o["Weight (g)"] for o in st.session_state.ornaments
                    )

                    # ✅ Take minimum carat for conservative valuation
                    min_carat = min(
                        o["Carat"] for o in st.session_state.ornaments
                    )

                    # ✅ Store for Step 3
                    st.session_state.net_weight = total_weight
                    st.session_state.carat = min_carat

                    # ✅ Navigate to Step 3
                    st.session_state.page = "gold_step3"
                    st.rerun()
                else:
                    st.error("Add at least one ornament and certify")




    # ---------- STEP 3 ----------
    elif st.session_state.page == "gold_step3":

        # 🔐 Session safety check (prevents broken navigation / refresh issues)
        if "net_weight" not in st.session_state or "carat" not in st.session_state:
            st.error("Session expired. Please restart the loan application.")
            st.stop()

        st.markdown("## GOLD LOAN — Step 3 of 6")
        st.markdown("### Loan Details")
        st.divider()

        gold_value = (
            st.session_state.net_weight *
            GOLD_RATE_PER_GRAM *
            PURITY_FACTOR[st.session_state.carat]
        )

        st.write("Gold Value:", int(gold_value))

        with st.expander("Monthly EMI Gold Loan (Demo)", expanded=True):

            st.warning(
                "Note: EMI scheme shown for academic demonstration only."
            )

            max_amt = int(gold_value * 0.75)

            if max_amt < 20000:
                st.error("Gold value insufficient for minimum loan eligibility.")
                st.stop()

            loan_amt = st.slider(
                "Loan Amount",
                min_value=20000,
                max_value=max_amt,
                value=max_amt,
                step=1000
            )

            tenure = st.slider("Tenure (Months)", 1, 36, 36)

            emi, explanation = emi_calculation_agent(
                loan_amt, 9.95, tenure
            )

            st.write("EMI:", emi)
            st.info(explanation.get("Decision Rationale", ""))

        if st.button("Next"):
            st.session_state.loan_summary = {
            "gold_value": int(gold_value),
            "loan_amount": loan_amt,
            "tenure_months": tenure,
            "emi": emi,
            "interest_rate": 9.95
            }
            st.session_state.page = "gold_step4"
            st.rerun()

    # ---------- STEP 4 ----------
    elif st.session_state.page == "gold_step4":

        st.subheader("📄 Document Upload & Identity Check")
        st.caption("Upload Aadhaar / PAN / identity document")

        uploaded = st.file_uploader(
        "Upload identity document (Aadhaar / PAN / Bill)",
        type=["png", "jpg", "jpeg"]
    )

        if uploaded:
            file_bytes = uploaded.getvalue()

            extracted, error = extract_identity_from_image(file_bytes)

            if error:
                st.error("❌ Document could not be processed. Manual verification required.")
                st.session_state.verification_result = None
            else:
                # STORE SILENTLY (customer never sees this)
                st.session_state.verification_result = extracted

                # OPTIONAL: auto-fail if nothing extracted
                if not extracted["name"] and not extracted["aadhaar_last4"]:
                    st.session_state.document_failure_reason = (
                        "Identity details could not be confidently extracted from document."
                    )

                st.success("✅ Document uploaded successfully")

        if st.button("Next"):
            st.session_state.page = "gold_step5"
            st.rerun()

    # ---------- STEP 5 : SUMMARY & SUBMIT ----------

    elif st.session_state.page == "gold_step5":

        st.markdown("## GOLD LOAN — Step 5 of 6")
        st.markdown("### Application Summary")
        st.caption("Please review your details before submitting the application")
        st.divider()

        # -----------------------------
        # Personal Details
        # -----------------------------
        c = st.session_state.logged_customer
        st.subheader("👤 Personal Details")
        st.write(f"**Name:** {c['Full_Name']}")
        st.write(f"**Date of Birth:** {c['DOB']}")
        st.write(f"**Mobile:** {c['Mobile']}")
        st.write(f"**Address:** {c['Address']}")
        st.write(f"**Aadhaar:** XXXX XXXX {c['Aadhaar'][-4:]}")

        st.divider()

        # -----------------------------
        # Gold Details
        # -----------------------------
        st.subheader("💍 Gold Details")
        st.table(st.session_state.ornaments)
        st.write(f"**Total Net Weight:** {st.session_state.net_weight} g")
        st.write(f"**Carat Considered:** {st.session_state.carat}")

        st.divider()

        # -----------------------------
        # Loan Details
        # -----------------------------
        s = st.session_state.loan_summary
        st.subheader("💰 Loan Details")
        st.write(f"**Assessed Gold Value:** ₹{s['gold_value']}")
        st.write(f"**Requested Loan Amount:** ₹{s['loan_amount']}")
        st.write(f"**Tenure:** {s['tenure_months']} months")
        st.write(f"**Estimated EMI:** ₹{s['emi']}")
        st.write(f"**Interest Rate:** {s['interest_rate']}% p.a.")

        st.divider()

        # -----------------------------
        # Document Status
        # -----------------------------
        st.subheader("📄 Document Verification")
        st.success("Identity document submitted successfully")
        st.caption(
            "Your document will be reviewed by a loan officer. "
            "You will be notified after verification is completed."
        )

        st.divider()

        # -----------------------------
        # Important Note
        # -----------------------------
        st.warning(
            "⚠️ This is not a loan approval. "
            "Final approval is subject to document verification "
            "and physical gold verification at the branch."
        )

        # -----------------------------
        # Submit Application
        # -----------------------------
        if st.button("Submit Application"):

            application_id = f"GL-{uuid.uuid4().hex[:8].upper()}"
            customer = st.session_state.logged_customer
            summary = st.session_state.loan_summary

            extracted = st.session_state.get("verification_result", {}) or {}
            failure_reason = st.session_state.get(
                "document_failure_reason", ""
            )

            with open("data/applications.csv", "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    application_id,
                    customer["Customer_ID"],
                    summary["loan_amount"],
                    summary["tenure_months"],
                    st.session_state.net_weight,
                    st.session_state.carat,
                    "SUBMITTED",
                    failure_reason,
                    extracted.get("name", ""),
                    extracted.get("dob", ""),
                    extracted.get("aadhaar_last4", ""),
                    datetime.now().isoformat()
                ])


            st.session_state.application_id = application_id
            st.session_state.application_status = "SUBMITTED"
            st.session_state.page = "gold_step6"
            st.rerun()

    # ---------- STEP 6 : CONFIRMATION ----------
    elif st.session_state.page == "gold_step6":

        st.markdown("## GOLD LOAN — Step 6 of 6")
        st.success("🎉 Your Gold Loan Application Has Been Submitted")

        st.markdown(f"""
        ### 📄 Application Reference ID  
        **{st.session_state.application_id}**

        Please keep this reference ID for future communication.
        """)

        st.info("""
        🏦 **Next Steps**
        - A loan officer will review your application
        - If eligible, you will receive a branch visit notification
        - Physical gold verification is mandatory
        """)


        st.warning(
            "📌 Please keep the following documents ready for branch visit:\n\n"
            "• Original gold ornaments\n"
            "• Identity proof\n"
            "• Address proof\n"
            "• Two passport-size photographs"
        )