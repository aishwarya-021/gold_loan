import base64
from groq import Groq
from PIL import Image
import io

# ----------------------------
# GROQ CONFIG
# ----------------------------
GROQ_API_KEY = "Your key"  # <-- put your key here
client = Groq(api_key=GROQ_API_KEY)

VISION_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"


def is_image(file_bytes):
    try:
        Image.open(io.BytesIO(file_bytes))
        return True
    except:
        return False


def extract_identity_from_image(file_bytes):
    """
    Uses Groq Vision model to extract KYC fields from image.
    Returns structured dict (SAFE for CSV).
    """

    if not is_image(file_bytes):
        return None, "Uploaded file is not an image"

    base64_image = base64.b64encode(file_bytes).decode("utf-8")

    prompt = """
    You are a professional KYC document analysis expert.

    Extract identity information from the document.

    OUTPUT FORMAT (STRICT):
    Name:
    DOB_or_Age:
    Aadhaar_Number:
    PAN_Number:
    Confidence_Level:

    RULES:
    - If not visible, write "Not Found"
    - Do NOT guess
    - No explanations
    """

    response = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        },
                    },
                ],
            }
        ],
        temperature=0.0
    )

    raw_text = response.choices[0].message.content

    extracted = {
        "name": "",
        "dob": "",
        "aadhaar_last4": ""
    }

    for line in raw_text.split("\n"):
        if line.lower().startswith("name"):
            extracted["name"] = line.split(":", 1)[1].strip()
        elif "dob" in line.lower() or "age" in line.lower():
            extracted["dob"] = line.split(":", 1)[1].strip()
        elif "aadhaar" in line.lower():
            aadhaar = line.split(":", 1)[1].strip().replace(" ", "")
            extracted["aadhaar_last4"] = aadhaar[-4:] if aadhaar.isdigit() else ""

    return extracted, None
