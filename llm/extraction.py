"""
LLM call 1: turn free-text into {ip, intent}. This is the only place in
the pipeline where an LLM reads the raw user prompt — everything after
this point operates on validated, structured data.
"""

import json
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import EXTRACTION_MODEL
from llm.ollama_client import call_ollama
from models import ExtractionResult

SYSTEM_PROMPT = """You are an intent and entity extraction engine for an \
endpoint security tool. Given a user message, extract:

1. "ip": the IPv4 address mentioned in the message, or null if none is present.
2. "intent": one of exactly these three values:
   - "existence_check": the user only wants to know if the asset exists \
and whether AV/EDR controls are present/applied.
   - "compliance_check": the user wants to know if the asset's controls \
are compliant against the security blueprint/standard and wants findings \
and recommendations.
   - "unknown": the message doesn't clearly map to either use case, or no \
IP is present.
3. "confidence": "high" if both the IP and intent are unambiguous, "low" otherwise.

Respond with ONLY a JSON object with exactly these three keys: ip, intent, confidence.
No prose, no markdown, no explanation.

Examples:
User: "is 10.4.5.6 in our inventory and does it have AV installed?"
{"ip": "10.4.5.6", "intent": "existence_check", "confidence": "high"}

User: "check compliance for 192.168.1.20 against our EDR policy and give me recommendations"
{"ip": "192.168.1.20", "intent": "compliance_check", "confidence": "high"}

User: "what's up with security these days"
{"ip": null, "intent": "unknown", "confidence": "low"}
"""


def extract_ip_and_intent(user_prompt: str) -> ExtractionResult:
    raw = call_ollama(
        model=EXTRACTION_MODEL,
        system=SYSTEM_PROMPT,
        prompt=user_prompt,
        json_mode=True,
        temperature=0.0,  # deterministic extraction, not creative
    )

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # Model didn't return valid JSON despite json_mode — fail safe,
        # don't guess.
        return ExtractionResult(ip=None, intent="unknown", confidence="low")

    # ExtractionResult's field_validator strips any IP that isn't a
    # well-formed IPv4 address, so a hallucinated or malformed value
    # becomes None here rather than reaching the DB layer.
    return ExtractionResult(**parsed)
