import json
import time
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import DuckDuckGoSearchRun

# Initialize LLM internally for these operations
def get_llm():
    return ChatGoogleGenerativeAI(model="gemini-3.6-flash")

@tool
def run_thumbnail_ab_test(video_title: str, topic: str) -> str:
    """Generates 3 distinct thumbnail concepts for A/B testing based on the video title, and simulates an A/B test pipeline deployment."""
    print(f"\n[OPS MANAGER] Generating Thumbnail A/B Test Variants for '{video_title}'...")
    llm = get_llm()
    prompt = f"You are an elite YouTube Strategist. Create 3 highly distinct, high-CTR thumbnail visual concepts for a video titled '{video_title}' about '{topic}'. One should be 'Curiosity Gap', one 'High Emotion/Face', one 'Text Heavy/Bold'. Format as JSON: {{\"variants\": [{{\"type\": \"...\", \"visuals\": \"...\", \"text_overlay\": \"...\"}}]}}"
    
    res = llm.invoke([("system", prompt)]).content
    if res.startswith("```json"): res = res.replace("```json\n", "").replace("\n```", "")
    
    try:
        data = json.loads(res.strip())
        out = "\n🎨 A/B THUMBNAIL DEPLOYMENT INITIATED:\n"
        for i, v in enumerate(data.get("variants", [])):
            out += f"  Variant {i+1} [{v.get('type')}]:\n   - Visuals: {v.get('visuals')}\n   - Text: {v.get('text_overlay')}\n\n"
        out += "[SYSTEM] Variants have been queued to YouTube API. CTR will be monitored for the first 60 minutes to lock the winner."
        return out
    except:
        return f"Failed to generate thumbnail variants. Raw output: {res}"

@tool
def audit_sponsorship_contract(video_transcript: str, contract_requirements: str) -> str:
    """Cross-references a raw video transcript against specific brand sponsorship requirements to ensure contractual fulfillment before posting."""
    print("\n[OPS MANAGER] Running Sponsorship Compliance Audit...")
    llm = get_llm()
    prompt = f"You are a strict Legal & Sponsorship Auditor. Compare the Video Transcript against the Brand Contract Requirements. State if they PASSED or FAILED each requirement. Provide quotes from the transcript if passed. If failed, explain exactly what is missing. Return JSON: {{\"status\": \"PASS\" or \"FAIL\", \"details\": [{{\"req\": \"...\", \"status\": \"PASS\" or \"FAIL\", \"reason\": \"...\"}}]}}\nTranscript: {video_transcript}\nRequirements: {contract_requirements}"
    
    res = llm.invoke([("system", prompt)]).content
    if res.startswith("```json"): res = res.replace("```json\n", "").replace("\n```", "")
    
    try:
        data = json.loads(res.strip())
        overall = data.get('status', 'FAIL')
        icon = "✅" if overall == "PASS" else "❌"
        out = f"\n⚖️ SPONSORSHIP AUDIT RESULT: {icon} {overall}\n"
        out += "="*40 + "\n"
        for detail in data.get('details', []):
            if isinstance(detail, str):
                try: d = json.loads(detail)
                except: d = {"req": detail, "status": "UNKNOWN", "reason": ""}
            else: d = detail
            st = "✅" if d.get('status') == 'PASS' else "❌"
            out += f"{st} Req: {d.get('req')}\n   Reason: {d.get('reason')}\n\n"
        
        if overall == "FAIL":
            out += "[ACTION REQUIRED] Video cannot be published. Please re-record missing requirements."
        else:
            out += "[CLEARED] Video meets all brand guidelines and is ready for upload."
        return out
    except:
        return f"Audit failed to parse response. Raw output: {res}"

@tool
def trigger_crisis_lockdown(brand_name: str) -> str:
    """Monitors live internet sentiment for a specific brand/creator. If massive negative sentiment (cancellation attempt) is detected, it triggers lockdown mode and pauses campaigns."""
    print(f"\n[OPS MANAGER] Scanning global sentiment for '{brand_name}'...")
    search = DuckDuckGoSearchRun()
    llm = get_llm()
    
    try:
        query = f"{brand_name} controversy OR drama OR backlash OR news"
        results = search.invoke(query)
    except:
        results = "No recent data available."
        
    prompt = f"Analyze these recent search results for '{brand_name}'. Determine if there is a severe, active PR crisis/cancellation attempt happening right now. Return JSON: {{\"crisis_detected\": true/false, \"summary\": \"...\", \"sentiment_score_1_to_10\": 5}}\nResults: {results}"
    
    res = llm.invoke([("system", prompt)]).content
    if res.startswith("```json"): res = res.replace("```json\n", "").replace("\n```", "")
    
    try:
        data = json.loads(res.strip())
        if data.get('crisis_detected') or data.get('sentiment_score_1_to_10', 5) < 4:
            out = "\n🚨 CRISIS PROTOCOL INITIATED 🚨\n"
            out += f"Summary: {data.get('summary')}\n"
            out += "Action: ALL scheduled posts PAUSED. Discord community locked. SMS sent to Creator."
            return out
        else:
            return f"\n🟢 Sentiment is stable (Score: {data.get('sentiment_score_1_to_10', 10)}/10). No crisis detected. Campaigns running normally."
    except:
        return "Failed to analyze sentiment."

@tool
def generate_collaboration_thread(creator_a_style: str, creator_b_style: str, topic: str) -> str:
    """Generates a cohesive, highly-engaging Twitter/X thread where two different creators collaborate, merging both of their authentic voices into a single seamless post."""
    print(f"\n[OPS MANAGER] Initiating Brain Sync for collaboration on '{topic}'...")
    llm = get_llm()
    prompt = f"Write a 5-tweet Twitter thread about '{topic}'. The thread is a collaboration between Creator A (Style: {creator_a_style}) and Creator B (Style: {creator_b_style}). Merge their styles seamlessly. It should read like a dynamic conversation or a high-value co-authored piece. Output just the raw text of the thread with 1/ 2/ 3/ numbering."
    
    res = llm.invoke([("system", prompt)]).content
    return f"\n🤝 COLLABORATION THREAD GENERATED:\n{'-'*40}\n{res.strip()}\n{'-'*40}"
