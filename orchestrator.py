"""
Orchestrator: the only place that knows about the full flow. Everything
else (extraction, DB, comparator, RAG, recommendations) is a plain
function this file calls in order.
"""

from db.database import get_asset_by_ip, get_controls_by_hostname
from db.blueprint import get_blueprint
from compliance.comparator import compare_controls_to_blueprint
from llm.extraction import extract_ip_and_intent
from llm.recommendation import generate_recommendations


def handle_user_message(user_prompt: str) -> dict:
    # --- Step 1: LLM call — extract IP + intent from free text ---
    

    # --- Step 2: deterministic DB lookup (no LLM) ---
   


    # --- Branch A: existence + control-presence check ---
    

    # --- Branch B: compliance check ---
    # Step 3: deterministic diff against blueprint (no LLM)
    
    # Step 4: only spend the RAG + second LLM call if there's actually
    
    # something to recommend against
    return response