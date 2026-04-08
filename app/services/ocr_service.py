import easyocr
import os


reader = easyocr.Reader(['ar', 'en'])

def extract_text_from_image(image_path: str) -> str:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at: {image_path}")

  
    results = reader.readtext(image_path)

    extracted_lines = [res[1] for res in results]

    full_text = " ".join(extracted_lines)
    return full_text.strip()