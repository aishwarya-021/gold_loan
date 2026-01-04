import re

def ocr_tool(file):
    """
    Simulated OCR (SAFE for capstone).
    Replace with real OCR later if needed.
    """
    try:
        text = file.read().decode("utf-8", errors="ignore")
        return text
    except:
        return ""


def ner_entity_extraction(text):
    """
    Lightweight NER using regex (NO external dependency).
    """
    extracted = {
        "name": None,
        "dob": None,
        "id_number": None
    }

    name_match = re.search(r"Name[:\- ]+([A-Za-z ]+)", text)
    dob_match = re.search(r"\b\d{2}[-/]\d{2}[-/]\d{4}\b", text)
    aadhaar_match = re.search(r"\b\d{4}\s?\d{4}\s?\d{4}\b", text)

    if name_match:
        extracted["name"] = name_match.group(1).strip()

    if dob_match:
        extracted["dob"] = dob_match.group()

    if aadhaar_match:
        extracted["id_number"] = aadhaar_match.group()

    return extracted


def identity_consistency_check(extracted, customer):
    """
    Assistive document screening (NOT approval).
    """
    result = {
        "name_match": False,
        "dob_match": False,
        "id_partial_match": False,
        "document_valid": False,
        "risk_flag": "HIGH"
    }

    if extracted["name"] and extracted["name"].lower() in customer["Full_Name"].lower():
        result["name_match"] = True

    if extracted["dob"] and extracted["dob"] in str(customer["DOB"]):
        result["dob_match"] = True

    if extracted["id_number"]:
        last4 = extracted["id_number"][-4:]
        if last4 == customer["Aadhaar"][-4:]:
            result["id_partial_match"] = True

    if result["name_match"] and result["dob_match"] and result["id_partial_match"]:
        result["document_valid"] = True
        result["risk_flag"] = "LOW"

    return result
