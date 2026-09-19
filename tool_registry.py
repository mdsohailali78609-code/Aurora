from typing import Dict, Any

# E-Commerce Tools
from ecommerce_ops import (
    intercept_abandoned_cart, generate_personal_shopper_bundle, trigger_vip_restock,
    deflect_return_request, handle_shipping_exception, optimize_agentic_seo,
    trigger_post_purchase_upsell, predict_creative_fatigue, adjust_dynamic_pricing,
    run_liquidity_copilot, fight_fraud_chargeback, calculate_autonomous_reorder,
    audit_vendor_accountability
)

# Social Media Tools
from social_agent import (
    publish_video_post, publish_standalone_post, repurpose_content, guide_api_onboarding,
    search_internet, create_campaign_strategy, check_active_campaigns, get_daily_task,
    schedule_post_time, schedule_standalone_post
)

# General / Desktop Tools (Imported from the Omni-Agent module)
from agent import (
    search_web, get_trending_social_ideas, add_contact
)

# Global Registry
TOOL_REGISTRY = {
    # E-Commerce
    "intercept_abandoned_cart": intercept_abandoned_cart,
    "generate_personal_shopper_bundle": generate_personal_shopper_bundle,
    "trigger_vip_restock": trigger_vip_restock,
    "deflect_return_request": deflect_return_request,
    "handle_shipping_exception": handle_shipping_exception,
    "optimize_agentic_seo": optimize_agentic_seo,
    "trigger_post_purchase_upsell": trigger_post_purchase_upsell,
    "predict_creative_fatigue": predict_creative_fatigue,
    "adjust_dynamic_pricing": adjust_dynamic_pricing,
    "run_liquidity_copilot": run_liquidity_copilot,
    "fight_fraud_chargeback": fight_fraud_chargeback,
    "calculate_autonomous_reorder": calculate_autonomous_reorder,
    "audit_vendor_accountability": audit_vendor_accountability,
    
    # Social Media
    "publish_video_post": publish_video_post,
    "publish_standalone_post": publish_standalone_post,
    "repurpose_content": repurpose_content,
    "guide_api_onboarding": guide_api_onboarding,
    "search_internet": search_internet,
    "create_campaign_strategy": create_campaign_strategy,
    "check_active_campaigns": check_active_campaigns,
    "get_daily_task": get_daily_task,
    "schedule_post_time": schedule_post_time,
    "schedule_standalone_post": schedule_standalone_post,
    
    # General / OS
    "search_web": search_web,
    "get_trending_social_ideas": get_trending_social_ideas,
    "add_contact": add_contact
}

def get_tools(tool_ids: list[str]) -> list[Any]:
    """
    Returns a list of actual LangChain tool functions based on string IDs.
    Ignores invalid/unrecognized IDs.
    """
    return [TOOL_REGISTRY[t_id] for t_id in tool_ids if t_id in TOOL_REGISTRY]
