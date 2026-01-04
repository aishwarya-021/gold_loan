import re
def valid_name(name): return bool(re.fullmatch(r"[A-Za-z ]+", name))
def valid_mobile(mobile): return bool(re.fullmatch(r"[6-9]\d{9}", mobile))
def valid_email(email): return bool(re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email))
def valid_pan(pan): return bool(re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]", pan))
def valid_aadhaar(aadhaar): return bool(re.fullmatch(r"\d{12}", aadhaar))
def valid_pin(pin): return bool(re.fullmatch(r"\d{4}", pin))

def valid_pin(pin):
    return pin.isdigit() and len(pin) == 4
