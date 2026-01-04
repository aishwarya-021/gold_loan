def emi_calculation_agent(loan_amount, annual_rate, tenure_months):
    """
    EMI Agent:
    - Calculates EMI using standard reducing balance formula
    - Returns EMI + transparent explanation (audit-friendly)
    """

    monthly_rate = annual_rate / 12 / 100

    emi = (
        loan_amount * monthly_rate * (1 + monthly_rate) ** tenure_months
    ) / (
        (1 + monthly_rate) ** tenure_months - 1
    )

    explanation = {
        "Loan Amount": loan_amount,
        "Tenure (Months)": tenure_months,
        "Annual Interest Rate (%)": annual_rate,
        "Monthly Interest Rate": round(monthly_rate, 6),
        "Formula": "EMI = P × r × (1+r)^n / ((1+r)^n − 1)",
        "Decision Rationale": (
            "EMI is calculated using RBI-standard reducing balance formula "
            "based on selected loan amount, tenure, and interest rate. "
            "This ensures transparent and audit-compliant repayment estimation."
        )
    }

    return int(emi), explanation