import json
import os
from pydantic import BaseModel

class ContactRequest(BaseModel):
    firstName: str
    lastName: str = ""
    email: str
    companyName: str
    idea: str = ""

req = ContactRequest(firstName="A", email="b@c.com", companyName="D", idea="test")
try:
    with open("leads.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(req.model_dump()) + "\n")
        
    os.environ["GOOGLE_API_KEY"] = "AQ.Ab8RN6KTK73UufbJrKVNckqfVisJhpk4p6eHIaZ18WX7_dVqcQ"
    from langchain_google_genai import ChatGoogleGenerativeAI
    llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash")
    prompt = f"Evaluate idea: {req.idea}"
    response = llm.invoke(prompt)
    print("TYPE:", type(response.content))
    print("CONTENT:", response.content)
    assessment = str(response.content).strip().upper()
    print("SUCCESS:", assessment)
except Exception as e:
    import traceback
    traceback.print_exc()
