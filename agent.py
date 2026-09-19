import os
import json
import logging
import webbrowser
import urllib.parse
from typing import Dict, Any

from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver

# Import Omni-Agent Tools from other modules
from social_agent import publish_video_post, publish_standalone_post, repurpose_content, guide_api_onboarding
from ecommerce_ops import (
    intercept_abandoned_cart, generate_personal_shopper_bundle, trigger_vip_restock,
    deflect_return_request, handle_shipping_exception, optimize_agentic_seo,
    trigger_post_purchase_upsell, predict_creative_fatigue, adjust_dynamic_pricing,
    run_liquidity_copilot, fight_fraud_chargeback, calculate_autonomous_reorder,
    audit_vendor_accountability
)

# Configure logging for the central Omni-Agent module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)

# 1. Environment Configuration
os.environ["GOOGLE_API_KEY"] = "AQ.Ab8RN6KTK73UufbJrKVNckqfVisJhpk4p6eHIaZ18WX7_dVqcQ"

# Initialize memory for the agent (Database Persistence)
conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
checkpointer = SqliteSaver(conn)
CONTACTS_FILE = "contacts.json"


# ==========================================
# 2. Local OS & Utility Tools
# ==========================================

@tool
def search_web(query: str) -> str:
    """
    Searches the internet for products, news, or general information.
    
    Args:
        query (str): The search intent.
        
    Returns:
        str: Mock search results (to be replaced by live API in Phase 2).
    """
    logger.info(f"Searching Google for: '{query}'...")
    if "shirt" in query.lower():
        return "Found 3 trending black shirts on Myntra and Zara for ₹1500 each."
    return f"Search results for {query}: Information found successfully."

@tool
def get_trending_social_ideas(platform: str, niche: str) -> str:
    """
    Finds viral video ideas and the best time to post on social media.
    
    Args:
        platform (str): Target social platform.
        niche (str): Content niche.
        
    Returns:
        str: Generated trends and times.
    """
    logger.info(f"Analyzing trends for {platform} in the {niche} niche...")
    return f"Trending {platform} Idea: 'Day in the life of an AI dev'. Best time to post: 6:00 PM IST."

def load_contacts() -> Dict[str, Any]:
    """Helper function to load the local address book."""
    if os.path.exists(CONTACTS_FILE):
        with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_contacts(contacts: Dict[str, Any]) -> None:
    """Helper function to persist the local address book."""
    with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
        json.dump(contacts, f, indent=4)

@tool
def add_contact(name: str, platform: str, handle: str) -> str:
    """
    Permanently saves a person's contact information (username or phone number) into the address book.
    
    Args:
        name (str): Person's name.
        platform (str): Communication platform (e.g., 'WhatsApp').
        handle (str): Phone number or username.
        
    Returns:
        str: Status of the save operation.
    """
    logger.info(f"Saving contact '{name}' for {platform}...")
    contacts = load_contacts()
    
    key_name = name.lower().strip()
    if key_name not in contacts:
        contacts[key_name] = {}
        
    contacts[key_name][platform.lower()] = handle
    save_contacts(contacts)
    
    return f"Successfully saved {name}'s {platform} contact as {handle}."

@tool
def send_message(app: str, contact_name: str, message: str) -> str:
    """
    Sends a text message to someone on WhatsApp or Telegram, looking up their contact info automatically.
    
    Args:
        app (str): The app to use (whatsapp, telegram).
        contact_name (str): The name of the recipient in the address book.
        message (str): The message text.
        
    Returns:
        str: Status of the message dispatch.
    """
    logger.info(f"Preparing to send message to {contact_name} on {app}:\n'{message}'")
    
    contacts = load_contacts()
    key_name = contact_name.lower().strip()
    platform_key = app.lower().strip()
    
    handle = contacts.get(key_name, {}).get(platform_key, "")
    
    if handle:
        logger.info(f"Found '{contact_name}' in Address Book -> {handle}")
    else:
        logger.warning(f"'{contact_name}' not found for {app}. Opening general share menu.")
    
    print("\n" + "="*50)
    approval = input(f"[SECURITY GATEWAY] Do you approve opening {app} to message {contact_name}? (y/n): ")
    
    if approval.lower() == 'y':
        if "whatsapp" in app.lower():
            if handle:
                url = f"whatsapp://send?phone={urllib.parse.quote_plus(handle)}&text={urllib.parse.quote_plus(message)}"
                fallback = f"https://wa.me/{urllib.parse.quote_plus(handle)}?text={urllib.parse.quote_plus(message)}"
            else:
                url = f"whatsapp://send?text={urllib.parse.quote_plus(message)}"
                fallback = f"https://wa.me/?text={urllib.parse.quote_plus(message)}"
            try:
                os.startfile(url) if hasattr(os, 'startfile') else webbrowser.open(url)
            except Exception:
                webbrowser.open(fallback)
                
        elif "telegram" in app.lower():
            if handle:
                clean_handle = handle.replace("@", "").replace(" ", "").replace("+", "")
                if clean_handle.isdigit():
                    url = f"tg://resolve?phone={urllib.parse.quote_plus(clean_handle)}&text={urllib.parse.quote_plus(message)}"
                    fallback = f"https://t.me/+{urllib.parse.quote_plus(clean_handle)}?text={urllib.parse.quote_plus(message)}"
                else:
                    url = f"tg://resolve?domain={urllib.parse.quote_plus(clean_handle)}&text={urllib.parse.quote_plus(message)}"
                    fallback = f"https://t.me/{urllib.parse.quote_plus(clean_handle)}?text={urllib.parse.quote_plus(message)}"
            else:
                url = f"tg://msg?text={urllib.parse.quote_plus(message)}"
                fallback = f"https://t.me/share/url?url={urllib.parse.quote_plus(message)}"
            try:
                os.startfile(url) if hasattr(os, 'startfile') else webbrowser.open(url)
            except Exception:
                webbrowser.open(fallback)
        else:
            logger.warning(f"App '{app}' not fully supported yet.")
            return f"Simulated sending message via {app}."
            
        logger.info(f"Message dispatched via OS intent.")
        return f"Success: Opened {app} with the message prepared for {contact_name}."
    else:
        logger.info("Message aborted by user.")
        return "Action denied by user."

@tool
def show_on_screen(search_term: str) -> str:
    """
    Opens a web browser to visually show search results for products. DO NOT use this for ordering.
    
    Args:
        search_term (str): The product to search for visually.
    """
    logger.info(f"Opening web browser to show results for: '{search_term}'...")
    url = f"https://www.google.com/search?q={urllib.parse.quote_plus(search_term)}&tbm=shop"
    webbrowser.open(url)
    return f"I have successfully opened a web browser on your screen showing results for {search_term}."

@tool
def order_product(product_name: str) -> str:
    """
    Initializes a mock purchase sequence when a user explicitly asks to 'order', 'buy', or 'purchase'.
    
    Args:
        product_name (str): The product to purchase.
    """
    logger.info(f"Initializing purchase sequence for: '{product_name}'...")
    
    amazon_url = f"https://www.amazon.com/s?k={urllib.parse.quote_plus(product_name)}"
    webbrowser.open(amazon_url)
    
    print("\n=======================================")
    print(f"🛍️  MOCK CHECKOUT: {product_name.upper()}")
    print("=======================================")
    approval = input("Press 'Y' to confirm placing this order (or 'N' to cancel): ")
    
    if approval.lower() == 'y':
        logger.info(f"Order placed for {product_name}.")
        return f"The order for {product_name} was successfully placed."
    else:
        logger.info("Order aborted.")
        return f"The user canceled the order for {product_name}."


# ==========================================
# 3. Brain & Routing Setup (The Omni-Agent)
# ==========================================

# Group all imported department tools together
tools = [
    search_web, get_trending_social_ideas, send_message, show_on_screen, order_product, add_contact,
    publish_video_post, publish_standalone_post, repurpose_content, guide_api_onboarding,
    intercept_abandoned_cart, generate_personal_shopper_bundle, trigger_vip_restock,
    deflect_return_request, handle_shipping_exception, optimize_agentic_seo,
    trigger_post_purchase_upsell, predict_creative_fatigue, adjust_dynamic_pricing,
    run_liquidity_copilot, fight_fraud_chargeback, calculate_autonomous_reorder,
    audit_vendor_accountability
]

# Initialize the core Language Model
llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash")

# Wire the Brain and Hands together automatically using LangGraph
# Note: This 'agent' variable is imported directly by server.py to handle web API requests.
agent = create_react_agent(llm, tools, checkpointer=checkpointer)
config = {"configurable": {"thread_id": "user_session_6"}, "recursion_limit": 10}


# ==========================================
# 4. CLI Execution Mode
# ==========================================

def start_interactive_cli():
    """Runs the agent interactively in the terminal."""
    print("\n🤖 OMNI-AGENT is online! (Type 'quit' to exit)")
    print("Try asking: 'Find me some black shirts' OR 'Send a WhatsApp to Mom' OR 'Post a tweet via Ayrshare'")

    import langchain
    langchain.debug = False # Turn off verbose debugging for cleaner CLI

    while True:
        try:
            user_input = input("\nYou: ")
            
            if user_input.lower() == 'quit':
                logger.info("Shutting down CLI.")
                break
                
            if user_input.lower() == 'clear':
                os.system('cls' if os.name == 'nt' else 'clear')
                continue
                
            if user_input.lower() == 'save':
                current_state = agent.get_state(config)
                with open("chat_log.txt", "w", encoding="utf-8") as f:
                    f.write("--- Chat History ---\n\n")
                    for msg in current_state.values.get("messages", []):
                        role = msg.type.capitalize()
                        content = msg.content if hasattr(msg, 'content') else str(msg)
                        if content:
                            f.write(f"{role}: {content}\n\n")
                print("✨ Conversation history saved to 'chat_log.txt'!")
                continue
                
            # Pass input into the graph
            result = agent.invoke({"messages": [("user", user_input)]}, config=config)
            
            # Clean output
            final_message = result['messages'][-1]
            clean_text = final_message.content if hasattr(final_message, 'content') else str(final_message)
            
            print(f"\nAI Agent:\n{clean_text}")
            
        except KeyboardInterrupt:
            logger.info("Interrupted by user. Shutting down.")
            break
        except Exception as e:
            logger.error(f"Error during agent invocation: {e}")

if __name__ == "__main__":
    start_interactive_cli()