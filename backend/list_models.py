import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load .env
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("\nAvailable Gemini Models:\n")

for model in genai.list_models():
    print(f"Model name: {model.name}")
    print(f"  Display name: {model.display_name}")
    print(f"  Supported methods: {model.supported_generation_methods}")
    print("-" * 60)
