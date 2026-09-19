import requests

url = "http://localhost:8000/api/contact"
payload = {
    "firstName": "Test",
    "lastName": "User",
    "email": "test@test.com",
    "companyName": "Test Inc",
    "idea": "A simple chatbot"
}

try:
    res = requests.post(url, json=payload)
    print(res.status_code)
    print(res.text)
except Exception as e:
    print(f"Error: {e}")
