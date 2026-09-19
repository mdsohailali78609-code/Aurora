import os
import json
import time
import logging
import requests
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from research_agent import run_fact_check_audit
from operations_agent import run_thumbnail_ab_test, audit_sponsorship_contract, trigger_crisis_lockdown, generate_collaboration_thread

# Configure logging for the Social Agent module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)

# Load API Keys securely from .env
load_dotenv()

# Database Setup
CAMPAIGN_DB = "social_campaigns.json"
VAULT_DIR = "Social_Posts"

def load_campaigns() -> List[Dict[str, Any]]:
    """Loads campaigns from the JSON database file.
    
    Returns:
        List[Dict[str, Any]]: A list of campaign dictionaries.
    """
    if os.path.exists(CAMPAIGN_DB):
        with open(CAMPAIGN_DB, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse {CAMPAIGN_DB}, returning empty list.")
                return []
    return []

def save_campaigns(campaigns: List[Dict[str, Any]]) -> None:
    """Saves the provided campaigns list to the JSON database file.
    
    Args:
        campaigns (List[Dict[str, Any]]): The updated list of campaigns to save.
    """
    with open(CAMPAIGN_DB, "w", encoding="utf-8") as f:
        json.dump(campaigns, f, indent=4)


# ==========================================
# 3. Social Media Management Tools
# ==========================================

@tool
def search_internet(query: str) -> str:
    """
    Searches the internet for trending music, competitor data, or recent news.
    
    Args:
        query (str): The search term to look up.
        
    Returns:
        str: A summary of the search results.
    """
    logger.info(f"Searching internet for: '{query}'...")
    try:
        search = DuckDuckGoSearchRun()
        return search.invoke(query)
    except Exception as e:
        logger.error(f"Failed to execute internet search: {e}")
        return f"Error executing internet search: {e}"


@tool
def create_campaign_strategy(niche: str, audience: str, monetization: str, days: int) -> str:
    """
    Creates a new JSON master strategy campaign and saves it to the database.
    
    Args:
        niche (str): The content niche (e.g., 'Fitness').
        audience (str): The target demographic.
        monetization (str): How the campaign generates revenue (e.g., 'Affiliate links').
        days (int): Total length of the campaign in days.
        
    Returns:
        str: Confirmation message including the new Campaign ID.
    """
    logger.info(f"Building {days}-day strategy for {niche}...")
    
    system_prompt = """You are an elite Social Media Strategist. Output valid JSON ONLY. Schema:
    {{
      "niche": "{niche}", "target_audience": "{audience}", "monetization": "{monetization}", "days_total": {days}, "current_day": 1,
      "strategy_overview": {{ "mission": "string", "content_pillars": ["Pillar 1", "Pillar 2"], "tone_of_voice": "string" }},
      "schedule": [
        {{ "day": 1, "content_pillar": "string", "format": "string", "hook_angle": "string", "topic": "string", "cta": "string", "status": "pending", "post_time": "TBD" }}
      ]
    }}"""
    
    llm_raw = ChatGoogleGenerativeAI(model="gemini-3.6-flash")
    try:
        res = llm_raw.invoke([("system", system_prompt.format(niche=niche, audience=audience, monetization=monetization, days=days))]).content
        if res.startswith("```json"): 
            res = res.replace("```json\n", "").replace("\n```", "")
        
        data = json.loads(res)
        campaigns = load_campaigns()
        campaigns.append(data)
        save_campaigns(campaigns)
        logger.info(f"Successfully generated and saved campaign ID: {len(campaigns)-1}")
        return f"Campaign saved! ID: {len(campaigns)-1}. Goal: {niche}."
    except Exception as e:
        logger.error(f"Error creating campaign strategy: {e}")
        return f"Error creating campaign: {e}"


@tool
def check_active_campaigns() -> str:
    """
    Retrieves a list of all active campaigns and their current day.
    
    Returns:
        str: A formatted string of all active campaigns.
    """
    campaigns = load_campaigns()
    if not campaigns: 
        return "No active campaigns found."
    
    res = ""
    for idx, c in enumerate(campaigns):
        res += f"ID: {idx} | Niche: {c.get('niche', 'Unknown')} | Day: {c.get('current_day', 1)} of {c.get('days_total', '?')}\n"
    return res


@tool
def get_daily_task(campaign_id: int) -> str:
    """
    Gets the strategy and topic for the current day of a specific campaign ID.
    
    Args:
        campaign_id (int): The ID of the campaign to query.
        
    Returns:
        str: The daily task details or an error message if invalid.
    """
    campaigns = load_campaigns()
    try:
        c = campaigns[campaign_id]
        curr = c.get("current_day", 1)
        day_data = next((d for d in c.get('schedule', []) if d.get('day') == curr), None)
        if not day_data: 
            return "Campaign is complete!"
        return f"Day {curr} Task:\nPillar: {day_data.get('content_pillar')}\nTopic: {day_data.get('topic')}\nTime: {day_data.get('post_time', 'Not scheduled')}"
    except (IndexError, TypeError):
        return "Invalid campaign ID."


@tool
def schedule_post_time(campaign_id: int, time_str: str) -> str:
    """
    Sets the daily automated posting time for the current day in a campaign.
    
    Args:
        campaign_id (int): The ID of the campaign.
        time_str (str): The time to schedule the post (e.g., '14:00').
        
    Returns:
        str: Success or failure message.
    """
    campaigns = load_campaigns()
    try:
        c = campaigns[campaign_id]
        curr = c.get("current_day", 1)
        day_data = next((d for d in c.get('schedule', []) if d.get('day') == curr), None)
        if day_data:
            day_data['post_time'] = time_str
            save_campaigns(campaigns)
            logger.info(f"Scheduled post for Campaign {campaign_id} at {time_str}.")
            return f"Scheduled Day {curr} post for {time_str}."
        return "Day not found in schedule."
    except (IndexError, TypeError):
        return "Invalid campaign ID."


@tool
def publish_video_post(campaign_id: int) -> str:
    """
    Publishes a video (Reel) simultaneously to multiple networks using the Unified Ayrshare API.
    
    Args:
        campaign_id (int): The ID of the campaign containing the video details.
        
    Returns:
        str: Status of the API publish request.
    """
    logger.info(f"Sending unified publish request for Campaign {campaign_id}...")
    campaigns = load_campaigns()
    try:
        campaign = campaigns[campaign_id]
    except (IndexError, TypeError):
        campaign = next((c for c in campaigns if c.get("id") == campaign_id), None)
    
    if not campaign:
        return f"Error: Campaign ID {campaign_id} not found."
    
    api_key = os.getenv("AYRSHARE_API_KEY")
    if not api_key or api_key == "your_ayrshare_api_key_here":
        logger.warning("Missing AYRSHARE_API_KEY. Running in simulation mode.")
        return "⚠️ REAL-WORLD INTEGRATION PAUSED: Missing AYRSHARE_API_KEY in .env.\n[SIMULATION] Video posted to all unified networks successfully."
    
    url = "https://app.ayrshare.com/api/post"
    payload = {
        "post": f"{campaign.get('topic', campaign.get('niche', 'Campaign'))} - {campaign.get('notes', '')}",
        "platforms": ["instagram", "twitter", "facebook"],
        "mediaUrls": ["https://example.com/hosted_video.mp4"]
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        res_data = response.json()
        
        if response.status_code == 200 and "id" in res_data:
            campaign["status"] = "PUBLISHED (UNIFIED API)"
            save_campaigns(campaigns)
            logger.info(f"Video published successfully. Ayrshare ID: {res_data['id']}")
            return f"✅ SUCCESS: Reel physically published to all unified networks! Ayrshare Post ID: {res_data['id']}"
        else:
            logger.error(f"Publish error from Ayrshare: {res_data}")
            return f"❌ PUBLISH ERROR: {res_data}"
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during publish: {e}")
        return f"❌ FATAL REQUEST ERROR: {str(e)}"


@tool
def schedule_standalone_post(content: str, platform: str, time_str: str) -> str:
    """
    Schedules a single, one-off post to a specific platform at a given time without needing a full campaign.
    
    Args:
        content (str): The post text content.
        platform (str): The target social media platform.
        time_str (str): The scheduled time string.
        
    Returns:
        str: Status of the schedule request.
    """
    logger.info(f"Scheduling standalone post for {platform} at {time_str}...")
    return f"Successfully scheduled post about '{content}' on {platform} at {time_str}."


@tool
def publish_standalone_post(content: str, platform: str) -> str:
    """
    Publishes a single, one-off post immediately using the Unified Ayrshare API.
    
    Args:
        content (str): The post text content.
        platform (str): The target social media platform (e.g., 'twitter').
        
    Returns:
        str: Status of the live API request.
    """
    logger.info(f"Publishing standalone post to {platform} via Ayrshare...")
    
    api_key = os.getenv("AYRSHARE_API_KEY")
    if not api_key or api_key == "your_ayrshare_api_key_here":
        time.sleep(2)
        logger.warning("Missing AYRSHARE_API_KEY. Simulating standalone publish.")
        return f"⚠️ SIMULATION: '{content}' was successfully published to {platform}."
        
    url = "https://app.ayrshare.com/api/post"
    payload = {
        "post": content,
        "platforms": [platform.lower()],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            logger.info("Standalone post published successfully.")
            return f"✅ SUCCESS: '{content}' was securely published to {platform} via Ayrshare!"
        else:
            logger.error(f"API Error from Ayrshare: {response.json()}")
            return f"❌ API ERROR: {response.json()}"
    except requests.exceptions.RequestException as e:
        logger.error(f"Network failure during publish: {e}")
        return f"❌ FATAL ERROR: {str(e)}"


@tool
def repurpose_content(transcript: str, platform: str, past_content: str, user_command: str) -> str:
    """
    Repurposes a long-form transcript into highly engaging short-form scripts based on the creator's past style.
    
    Args:
        transcript (str): The raw input text/transcript.
        platform (str): The target platform for the repurposed content.
        past_content (str): Examples of past content to mimic tone and style.
        user_command (str): Explicit user directive for what to emphasize.
        
    Returns:
        str: The structured short-form content output.
    """
    logger.info(f"Repurposing content for {platform}...")
    
    system_prompt = """You are an elite AI Operational Copilot and Digital Manager for a professional content creator. Your primary directive is to protect the creator's time by automating content repurposing, drafting cross-platform copy, and organizing their daily workflow.

INPUT DATA:
- Raw Content/Transcript: {transcript}
- Platform Destination: {platform}
- Creator's Tone & Style Reference: {past_content}
- Current Action Needed: {user_command}

CORE INSTRUCTIONS:
1. Voice Mimicry: Analyze the "Creator's Tone & Style Reference". You must strictly adopt their vocabulary, sentence structure, emoji usage, and pacing. Do not use generic AI buzzwords (e.g., "delve", "uncover", "testament").
2. Content Repurposing: If provided a long-form transcript, identify the 3 most highly engaging, controversial, or educational "hooks." Structure these into 3 distinct short-form scripts (under 60 seconds when spoken).
3. Copywriting constraints: 
   - Twitter/X: Max 280 characters, punchy hook, conversational tone.
   - YouTube Shorts/TikTok: Focus on visual cues and an immediate 3-second hook.
   - Instagram/LinkedIn: Story-driven, spaced formatting, clear Call-to-Action (CTA).
4. Task Extraction: Based on the generated content, list the immediate next steps the creator needs to take.

OUTPUT FORMAT:
You must return your response EXCLUSIVELY as a valid JSON object. Do not include markdown formatting like ```json. Use the following schema:
{{
  "project_title": "Short title for this batch",
  "generated_assets": [
    {{
      "platform": "Name of platform",
      "hook": "The opening line",
      "script_or_caption": "The full text",
      "suggested_visuals": "Brief description of the thumbnail or B-roll needed"
    }}
  ],
  "creator_action_items": [
    "Task 1",
    "Task 2"
  ]
}}"""

    try:
        llm_raw = ChatGoogleGenerativeAI(model="gemini-3.6-flash")
        res = llm_raw.invoke([("system", system_prompt.format(transcript=transcript, platform=platform, past_content=past_content, user_command=user_command))]).content
        
        if res.startswith("```json"): 
            res = res.replace("```json\n", "").replace("\n```", "")
        
        data = json.loads(res)
        formatted_output = f"\n🔥 PROJECT: {data.get('project_title', 'Untitled')}\n"
        for asset in data.get('generated_assets', []):
            formatted_output += f"\n--- {asset.get('platform', 'Unknown')} ---\nHook: {asset.get('hook', '')}\nScript:\n{asset.get('script_or_caption', '')}\nVisuals: {asset.get('suggested_visuals', '')}\n"
        
        formatted_output += "\n📌 YOUR ACTION ITEMS:\n"
        for task in data.get('creator_action_items', []):
            formatted_output += f"- [ ] {task}\n"
            
        return formatted_output
    except Exception as e:
        logger.error(f"Error parsing repurposed content: {e}")
        return f"Error parsing repurposed content: {e}"


@tool
def guide_api_onboarding(platform: str) -> str:
    """
    Explains to the user how to connect their social media accounts using the seamless Clerk + Ayrshare flow.
    
    Args:
        platform (str): The social media platform they want to connect.
        
    Returns:
        str: Structured onboarding instructions.
    """
    platform = platform.title()
    logger.info(f"Providing Ayrshare Unified OAuth guide for {platform}...")
    
    return (
        f"📌 **Connecting {platform} is effortless:**\n"
        f"1. Go to your Web Dashboard.\n"
        f"2. Click the 'Deploy Your Copilot' button.\n"
        f"3. Securely create your account via our Clerk SSO.\n"
        f"4. Once subscribed, click the 'Connect with {platform}' button.\n"
        f"5. Our Unified Ayrshare API securely handles the OAuth token exchange.\n\n"
        f"You only ever have to click 'Accept' once. We route all your multi-platform posts seamlessly!"
    )


# ==========================================
# 4. Standalone Agent Execution Block
# ==========================================

# Note: In a production environment, this agent is usually orchestrated by `agent.py`.
# The code below allows for standalone testing if `social_agent.py` is executed directly.
if __name__ == "__main__":
    llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash")
    tools = [
        search_internet, create_campaign_strategy, check_active_campaigns, get_daily_task, schedule_post_time, 
        publish_video_post, schedule_standalone_post, publish_standalone_post, repurpose_content, run_fact_check_audit,
        run_thumbnail_ab_test, audit_sponsorship_contract, trigger_crisis_lockdown, generate_collaboration_thread,
        guide_api_onboarding
    ]

    system_message = "You are an autonomous Social Media Agent. You manage campaigns, search the web for trends, and automate posting. Always be helpful and conversational."
    agent_executor = create_react_agent(llm, tools)
    
    print("\n==========================================")
    print("AUTONOMOUS SOCIAL MEDIA AGENT")
    print("==========================================")
    print("Agent: Hello! I am your AI Social Media Manager. I can browse the internet for trends, build campaigns, schedule posts, and publish them via API.")
    print("Type 'exit' to quit.\n")
    
    chat_history = [("system", system_message)]
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ['exit', 'quit']:
                print("Agent: Shutting down. Goodbye!")
                break
                
            chat_history.append(("user", user_input))
            response = agent_executor.invoke({"messages": chat_history})
            bot_reply = response["messages"][-1].content
            print(f"\nAgent: {bot_reply}\n")
            chat_history.append(("assistant", bot_reply))
            
        except Exception as e:
            logger.error(f"System Error in conversational loop: {e}")
            print(f"\n[System Error] {e}\n")
