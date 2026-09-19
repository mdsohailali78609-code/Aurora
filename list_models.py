import os
import requests
api_key = "AQ.Ab8RN6KTK73UufbJrKVNckqfVisJhpk4p6eHIaZ18WX7_dVqcQ"
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
response = requests.get(url)
for model in response.json().get("models", []):
    print(model["name"])
