import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv()
load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=True)
load_dotenv(dotenv_path=PROJECT_ROOT / ".env.txt", override=True)

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError("Missing GOOGLE_API_KEY in environment variables.")

client = genai.Client(api_key=api_key)
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Hello",
)

print(response.text)
