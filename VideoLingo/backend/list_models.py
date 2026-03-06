import os
import requests
from dotenv import load_dotenv

load_dotenv()

def list_models():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY is not set.")
        return

    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print("Available Gemini Models:")
            print("-" * 50)
            for model in models:
                name = model.get("name")
                display_name = model.get("displayName")
                version = model.get("version")
                # Filter out older models to focus on the strongest ones requested
                if "gemini" in name:
                    print(f"Name: {name}")
                    print(f"Display Name: {display_name}")
                    print(f"Version: {version}")
                    print("-" * 50)
        else:
            print(f"Error fetching models: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    list_models()
