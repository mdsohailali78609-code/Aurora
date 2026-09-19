import os
from langchain_google_genai import ChatGoogleGenerativeAI
os.environ["GOOGLE_API_KEY"] = "AQ.Ab8RN6KTK73UufbJrKVNckqfVisJhpk4p6eHIaZ18WX7_dVqcQ"
try:
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest")
    print("Trying gemini-1.5-flash-latest...")
    print(llm.invoke("Hi").content)
except Exception as e:
    print(f"Error flash-latest: {e}")

try:
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest")
    print("Trying gemini-1.5-pro-latest...")
    print(llm.invoke("Hi").content)
except Exception as e:
    print(f"Error pro-latest: {e}")

try:
    llm = ChatGoogleGenerativeAI(model="gemini-pro")
    print("Trying gemini-pro...")
    print(llm.invoke("Hi").content)
except Exception as e:
    print(f"Error gemini-pro: {e}")
