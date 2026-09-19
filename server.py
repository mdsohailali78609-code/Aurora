import os
import json
import logging
import traceback
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configure logging for the FastAPI Server
logger = logging.getLogger("aurora_server")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)

# Load environment variables (includes API Keys)
load_dotenv()

# Import the Master Omni-Agent and specific tools
from social_agent import publish_standalone_post
from agent import agent as omni_agent, config as omni_config

# Import Auth & DB 
import database
import auth
from sqlalchemy.orm import Session
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm

# Initialize Database
database.Base.metadata.create_all(bind=database.engine)

# Initialize FastAPI App
app = FastAPI(
    title="Aurora Omni-Agent Server",
    description="Central backend for routing frontend commands to the Python Agent ecosystem.",
    version="2.0.0"
)

# Initialize Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure Cross-Origin Resource Sharing (CORS)
# (Using wildcard for local testing. Lock down to specific domains for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# Data Models
# ==========================================

class PostRequest(BaseModel):
    """Schema for a direct social media post request."""
    content: str
    platform: str

class ChatRequest(BaseModel):
    """Schema for a message sent to the Omni-Agent."""
    prompt: str
    session_id: str = "default_session"

class ContactRequest(BaseModel):
    """Schema for lead capture form submissions."""
    firstName: str
    lastName: str = ""
    email: str
    companyName: str
    idea: str = ""

class UserCreate(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class DeployRequest(BaseModel):
    agent_type: str

class IntegrationRequest(BaseModel):
    deployment_id: int
    platform: str
    api_key: str

class CustomAgentConfig(BaseModel):
    client_id: str
    agent_id: str
    name: str
    system_prompt: str
    tools: list[str]

# ==========================================
# API Endpoints

# ==========================================

@app.post("/api/auth/register", response_model=Token)
def register_user(user: UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(database.User).filter(database.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = database.User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token = auth.create_access_token(data={"sub": new_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/auth/login", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(database.User).filter(database.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/deploy")
@limiter.limit("5/minute")
def deploy_agent(req: DeployRequest, request: Request, current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    """Creates a new AgentDeployment for the logged-in user."""
    deployment = database.AgentDeployment(user_id=current_user.id, agent_type=req.agent_type, status="active")
    db.add(deployment)
    db.commit()
    db.refresh(deployment)
    return {"status": "success", "deployment_id": deployment.id}

@app.post("/api/integrations")
@limiter.limit("10/minute")
def save_integration(req: IntegrationRequest, request: Request, current_user: database.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    """Securely saves API keys to the database for a specific deployment."""
    # Verify deployment belongs to user
    deployment = db.query(database.AgentDeployment).filter(
        database.AgentDeployment.id == req.deployment_id,
        database.AgentDeployment.user_id == current_user.id
    ).first()
    
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
        
    integration = database.IntegrationKey(
        deployment_id=deployment.id,
        platform=req.platform,
        api_key_encrypted=req.api_key  # Should be encrypted in production
    )
    db.add(integration)
    db.commit()
    db.refresh(integration)
    return {"status": "success", "integration_id": integration.id}

@app.post("/api/agent/social/post")
@limiter.limit("10/minute")
def create_social_post(req: PostRequest, request: Request, current_user: database.User = Depends(auth.get_current_user)):
    """
    Directly triggers the standalone social media publishing tool.
    
    Args:
        req (PostRequest): The content and platform for the post.
        
    Returns:
        dict: The result of the publishing action.
    """
    logger.info(f"Received API Request: Standalone Post to {req.platform}")
    try:
        # Trigger the Python Tool directly from the Web API
        result = publish_standalone_post.invoke({
            "content": req.content,
            "platform": req.platform
        })
        logger.info(f"Post successful: {result}")
        return {"status": "success", "message": result}
    except Exception as e:
        logger.error(f"Failed to publish standalone post: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def send_lead_notification(lead_data: dict, assessment: str):
    """Sends an email notification to the founder when a lead is captured."""
    sender_email = os.getenv("SMTP_EMAIL")
    sender_password = os.getenv("SMTP_PASSWORD")
    target_email = "mdsohailali78609@gmail.com"
    
    if not sender_email or not sender_password:
        logger.warning("SMTP_EMAIL or SMTP_PASSWORD not set in .env. Lead saved locally but email not sent.")
        return
        
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = target_email
        msg['Subject'] = f"🚀 New AI Agent Lead: {lead_data['companyName']}"

        body = f"""
New Lead Captured!

Name: {lead_data['firstName']} {lead_data['lastName']}
Email: {lead_data['email']}
Company: {lead_data['companyName']}

Idea/Workflow: 
{lead_data['idea']}

AI Assessment: {assessment}
        """
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # Connect to Gmail SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        logger.info("Lead notification emailed successfully to founder.")
    except Exception as e:
        logger.error(f"Failed to send lead email: {e}")


@app.post("/api/contact")
@limiter.limit("50/minute")
def submit_contact(req: ContactRequest, request: Request):
    """
    Captures leads from the frontend Discuss Project form.
    """
    logger.info(f"Received Lead: {req.firstName} {req.lastName} - {req.email} ({req.companyName})")
    try:
        with open("../leads.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(req.model_dump()) + "\n")
            
        # Use LLM to evaluate the idea
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash")
        
        prompt = f"""
        Evaluate the following AI agent idea. 
        If it is a basic workflow (simple scripts, straightforward API calls, existing templates, basic chatbots), output EXACTLY: SIMPLE
        If it requires complex reasoning, multiple agents, RAG, custom databases, or intricate integrations, output EXACTLY: COMPLEX
        Respond ONLY with SIMPLE or COMPLEX.
        
        Idea: {req.idea}
        """
        
        response = llm.invoke(prompt)
        content_val = response.content
        
        if isinstance(content_val, list):
            text_parts = []
            for item in content_val:
                if isinstance(item, dict):
                    text_parts.append(str(item.get("text", item.get("TEXT", ""))))
                else:
                    text_parts.append(str(item))
            assessment = " ".join(text_parts).strip().upper()
        else:
            assessment = str(content_val).strip().upper()
            
        logger.info(f"LLM Assessment: {assessment}")
        
        # Notify the founder
        send_lead_notification(req.model_dump(), assessment)
        
        # Format proposal variables
        return {
            "status": "success",
            "complexity": "Enterprise Build" if "COMPLEX" in assessment else "Standard Build",
            "delivery": "1-2 weeks" if "COMPLEX" in assessment else "3-5 days",
            "whatsapp": "7294938525"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Failed to process lead proposal: {e}")
        raise HTTPException(status_code=500, detail="Failed to process proposal.")

@app.post("/api/agent/chat")
@limiter.limit("15/minute")
def chat_with_agent(req: ChatRequest, request: Request, current_user: database.User = Depends(auth.get_current_user)):
    """
    Main entry point for the Omni-Agent. Routes the user's prompt through the 
    LangGraph State Machine to determine the correct tools to execute.
    
    Args:
        req (ChatRequest): The user's input prompt and session ID.
        
    Returns:
        dict: The final reasoning/answer generated by the Omni-Agent.
    """
    logger.info(f"Received Chat Request from session '{req.session_id}': '{req.prompt}'")
    try:
        # Define session-specific configuration
        local_config = {"configurable": {"thread_id": req.session_id}, "recursion_limit": 10}
        
        # Invoke the full autonomous Omni-Agent
        response = omni_agent.invoke({"messages": [("user", req.prompt)]}, config=local_config)
        
        # The agent's final answer is the content of the last message
        final_message = response["messages"][-1]
        final_answer = final_message.content if hasattr(final_message, 'content') else str(final_message)
        
        logger.info("Omni-Agent successfully processed the request.")
        return {"status": "success", "message": final_answer}
    except Exception as e:
        logger.error("Omni-Agent encountered a fatal error during graph execution.")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="The AI Agent encountered an internal error. Check server logs.")

@app.post("/api/custom/{client_id}/chat")
@limiter.limit("15/minute")
def chat_with_custom_agent(client_id: str, req: ChatRequest, request: Request):
    """
    Dynamic endpoint for a client's specific Custom Agent.
    """
    logger.info(f"Custom Agent '{client_id}' received prompt: '{req.prompt}' (session: {req.session_id})")
    try:
        from custom_agent_factory import create_custom_agent
        agent_data = create_custom_agent(client_id)
        agent_executor = agent_data["executor"]
        system_prompt = agent_data["system_prompt"]
        
        # Configure thread for memory
        local_config = {"configurable": {"thread_id": f"{client_id}_{req.session_id}"}, "recursion_limit": 10}
        
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=req.prompt)]
        
        response = agent_executor.invoke({"messages": messages}, config=local_config)
        
        final_message = response["messages"][-1]
        final_answer = final_message.content if hasattr(final_message, 'content') else str(final_message)
        
        return {"status": "success", "message": final_answer}
    except Exception as e:
        logger.error(f"Custom Agent Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/agents")
def create_custom_agent_config(req: CustomAgentConfig, request: Request):
    """Admin endpoint to deploy a custom agent to the configuration JSON."""
    try:
        agents_data = {}
        if os.path.exists("custom_agents.json"):
            with open("custom_agents.json", "r", encoding="utf-8") as f:
                agents_data = json.load(f)
                
        agents_data[req.client_id] = {
            "agent_id": req.agent_id,
            "name": req.name,
            "system_prompt": req.system_prompt,
            "tools": req.tools
        }
        
        with open("custom_agents.json", "w", encoding="utf-8") as f:
            json.dump(agents_data, f, indent=4)
            
        # Invalidate cache if it exists in the factory
        try:
            from custom_agent_factory import _AGENT_CACHE
            if req.client_id in _AGENT_CACHE:
                del _AGENT_CACHE[req.client_id]
        except Exception:
            pass
            
        return {"status": "success", "message": "Agent successfully deployed!"}
    except Exception as e:
        logger.error(f"Failed to deploy custom agent: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/api/custom/{client_id}/details")
def get_custom_agent_details(client_id: str, request: Request):
    """Retrieves custom agent details for the client portal."""
    try:
        if not os.path.exists("custom_agents.json"):
            raise HTTPException(status_code=404, detail="Agent database not found")
            
        with open("custom_agents.json", "r", encoding="utf-8") as f:
            agents_data = json.load(f)
            
        if client_id not in agents_data:
            raise HTTPException(status_code=404, detail="Agent not found for this client")
            
        agent_info = agents_data[client_id]
        return {
            "status": "success",
            "name": agent_info.get("name", "Custom Agent"),
            "agent_id": agent_info.get("agent_id", client_id)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching agent details: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# ==========================================
# Static Files & Server Start

# ==========================================

# Serve the Web Dashboard (Frontend) from the root URL
app.mount("/", StaticFiles(directory="AuroraDashboard", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting Aurora Omni-Agent Server on http://0.0.0.0:{port}")
    uvicorn.run("server:app", host="0.0.0.0", port=port)
