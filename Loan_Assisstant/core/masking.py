def mask_pan(pan): return "XXXXXX" + pan[-4:]
def mask_mobile(mobile): return "XXXXXX" + mobile[-4:]

def mask_dob(dob):
    y, m, d = dob.split("-")
    return f"{d} {m} XXXX"