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
    extraction = extract_ip_and_intent(user_prompt)

    if extraction.ip is None:
        return {
            "status": "clarification_needed",
            "message": "I couldn't find a valid IP address in your message. "
                       "Could you provide the asset's IP?",
        }

    if extraction.intent == "unknown":
        return {
            "status": "clarification_needed",
            "message": f"I found IP {extraction.ip}, but I'm not sure whether you want "
                       "an existence/control check or a compliance check. Which would you like?",
        }

    # --- Step 2: deterministic DB lookup (no LLM) ---
    asset = get_asset_by_ip(extraction.ip)
    if asset is None:
        return {
            "status": "not_found",
            "ip": extraction.ip,
            "message": f"No asset found in inventory with IP {extraction.ip}.",
        }

    controls = get_controls_by_hostname(asset.hostname)
    if controls is None:
        return {
            "status": "no_controls_data",
            "ip": extraction.ip,
            "hostname": asset.hostname,
            "message": f"Asset {asset.hostname} ({extraction.ip}) exists in inventory, "
                       "but no AV/EDR control evidence is on file for it.",
        }

    # --- Branch A: existence + control-presence check ---
    if extraction.intent == "existence_check":
        return {
            "status": "ok",
            "use_case": "existence_check",
            "ip": extraction.ip,
            "hostname": asset.hostname,
            "business_owner": asset.business_owner,
            "exists": True,
            "controls_present": {
                "av_installed": controls.av_installed,
                "edr_sensor_installed": controls.edr_sensor_installed,
            },
        }

    # --- Branch B: compliance check ---
    # Step 3: deterministic diff against blueprint (no LLM)
    compliance_result = compare_controls_to_blueprint(controls, get_blueprint())

    response = {
        "status": "ok",
        "use_case": "compliance_check",
        "ip": extraction.ip,
        "hostname": asset.hostname,
        "compliant": compliance_result.compliant,
        "findings": [f.model_dump() for f in compliance_result.findings],
    }

    # Step 4: only spend the RAG + second LLM call if there's actually
    # something to recommend against.
    if not compliance_result.compliant:
        response["recommendations"] = generate_recommendations(compliance_result)
    else:
        response["recommendations"] = None

    return response
