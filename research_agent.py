import json
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_google_genai import ChatGoogleGenerativeAI

@tool
def run_fact_check_audit(script_text: str) -> str:
    """Runs a highly rigorous fact-check on a given script, searches the internet for verification of each claim, and outputs a Credibility Report. Use this immediately when a user asks to fact-check or verify a script."""
    print("\n[FACT CHECKER] Initializing credibility scan...")
    
    llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash")
    
    # Step 1: Extract claims
    print("[FACT CHECKER] Extracting factual claims...")
    extract_prompt = f"""Extract all factual claims, statistics, and verifiable statements from the following script. Output a valid JSON list of strings ONLY. No markdown, no formatting. Just the raw array.
Script: {script_text}
Output format: ["claim 1", "claim 2"]"""
    
    res = llm.invoke([("system", extract_prompt)]).content
    if res.startswith("```json"): res = res.replace("```json\n", "").replace("\n```", "")
    res = res.strip()
    
    try:
        claims = json.loads(res)
    except:
        return f"Failed to parse claims from the script. Raw output: {res}"
        
    if not claims:
        return "No verifiable factual claims found in this script."
        
    # Step 2: Verify each claim
    search = DuckDuckGoSearchRun()
    report = "\n🔍 CREDIBILITY COPILOT: FACT-CHECK REPORT\n"
    report += "="*45 + "\n"
    citations = []
    
    for i, claim in enumerate(claims):
        print(f"[FACT CHECKER] Verifying claim: {claim[:40]}...")
        try:
            search_results = search.invoke(claim)
        except Exception as e:
            search_results = "Search failed."
            
        verify_prompt = f"""You are an elite Fact-Checker. Compare the Claim to the Search Results. 
Claim: {claim}
Search Results: {search_results}

Determine if the claim is VERIFIED or UNVERIFIED based purely on the search results. If verified, provide a 1-sentence explanation and a citation source (e.g., domain name). If unverified or missing context, explain why.
Output JSON ONLY. No markdown tags. Format:
{{
    "status": "VERIFIED" or "UNVERIFIED",
    "explanation": "short explanation",
    "citation": "source link or domain if available, else None"
}}"""
        v_res = llm.invoke([("system", verify_prompt)]).content
        if v_res.startswith("```json"): v_res = v_res.replace("```json\n", "").replace("\n```", "")
        v_res = v_res.strip()
        
        try:
            v_data = json.loads(v_res)
            status = v_data.get("status", "UNVERIFIED")
            if status == "VERIFIED":
                report += f"🟢 VERIFIED: {claim}\n   Reason: {v_data.get('explanation')}\n\n"
                cit = v_data.get('citation')
                if cit and cit != "None": citations.append(f"[{i+1}] {cit}")
            else:
                report += f"🔴 UNVERIFIED: {claim}\n   Reason: {v_data.get('explanation')}\n   [ACTION REQUIRED: Verify manually or remove from script]\n\n"
        except:
            report += f"🔴 UNVERIFIED: {claim}\n   Reason: Analysis failed on this specific claim.\n\n"

    report += "📚 SHOW NOTES CITATIONS:\n"
    if citations:
        for cit in citations:
            report += f"{cit}\n"
    else:
        report += "No citations generated.\n"
        
    print("[FACT CHECKER] Scan complete!")
    return report
