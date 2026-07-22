"""
Orchestrator: the only place that knows about the full flow.

- existence_check: DB existence/control-presence check (unchanged), PLUS
  now a RAG + LLM call against the 'standards' (CIS) collection if any
  control is missing entirely — scoped to "does it exist," not compliance.
- compliance_check: unchanged behavior, RAG + LLM call scoped to the
  'master_policies' collection.
"""

from models import Finding
from db.database import get_asset_by_ip, get_controls_by_hostname
from db.blueprint import get_blueprint
from compliance.comparator import compare_controls_to_blueprint
from llm.extraction import extract_ip_and_intent
from llm.recommendation import generate_compliance_recommendations, generate_existence_recommendations


def _missing_control_findings(controls) -> list[Finding]:
    """Existence-check is only about presence/absence — not configuration —
    so this only ever produces at most two findings (AV, EDR), independent
    of the full blueprint used by the compliance branch."""
    findings = []
    if not controls.av_installed:
        findings.append(Finding(
            field="av_installed", expected=True, actual=False,
            severity="critical", description="Antivirus is not installed on this asset.",
        ))
    if not controls.edr_sensor_installed:
        findings.append(Finding(
            field="edr_sensor_installed", expected=True, actual=False,
            severity="critical", description="EDR sensor is not installed on this asset.",
        ))
    return findings


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
        missing = _missing_control_findings(controls)

        response = {
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

        # Only spend the RAG + LLM call if a control is actually missing.
        if missing:
            response["recommendations"] = generate_existence_recommendations(asset.hostname, missing)
        else:
            response["recommendations"] = None

        return response

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
        response["recommendations"] = generate_compliance_recommendations(compliance_result)
    else:
        response["recommendations"] = None

    return response