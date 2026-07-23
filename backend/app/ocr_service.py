from io import BytesIO

from PIL import Image
import pytesseract

def extract_text_from_image(image_source):
    if isinstance(image_source, (bytes, bytearray)):
        image = Image.open(BytesIO(image_source))
    else:
        image = Image.open(image_source)

    text = pytesseract.image_to_string(image)
    
    return text.strip()