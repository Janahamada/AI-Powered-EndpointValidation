"""
LLM call 2: turn a structured findings list + retrieved policy excerpts
into readable, policy-grounded recommendations. This call never sees the
raw controls data or the blueprint rules directly — only the findings
that the deterministic comparator already produced, so there's nothing
left for the model to get wrong about *whether* something is a gap,
only how to explain and prioritize it.
"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RECOMMENDATION_MODEL, RAG_TOP_K
from llm.ollama_client import call_ollama
from models import ComplianceResult
from rag.retriever import retrieve_policy_context

SYSTEM_PROMPT = """You are a security compliance assistant. You will be \
given a list of control findings for one asset (fields that failed the \
security blueprint) and relevant excerpts from internal policies and \
standards. Write clear, actionable remediation recommendations.

Rules:
- Address every finding provided. Do not invent findings that weren't given to you.
- For each recommendation, cite which policy excerpt it's grounded in, by source filename.
- Order recommendations by severity: critical first, then high, medium, low.
- Be concise and operational — this goes to a security analyst, not an executive summary.
- If the provided policy excerpts don't cover a finding, say so rather than guessing at a policy.
"""


def _build_retrieval_query(compliance_result: ComplianceResult) -> str:
    """Build a semantic query from the findings, not the raw user prompt —
    the user's original message carries no retrievable
    signal. The findings themselves are what we need matching policy for."""
    return " ".join(
        f"{f.description} (field: {f.field})" for f in compliance_result.findings
    )


def generate_recommendations(compliance_result: ComplianceResult) -> str:
    if compliance_result.compliant:
        return "Asset is compliant with the blueprint. No recommendations needed."

    query = _build_retrieval_query(compliance_result)
    retrieved = retrieve_policy_context(query, top_k=RAG_TOP_K)

    findings_block = "\n".join(
        f"- [{f.severity}] {f.field}: expected {f.expected}, actual {f.actual} — {f.description}"
        for f in compliance_result.findings
    )
    policy_block = "\n".join(
        f"[{doc['source']}] {doc['text']}" for doc in retrieved
    ) or "(no matching policy excerpts retrieved)"

    prompt = f"""Findings for asset {compliance_result.hostname}:
{findings_block}

Relevant policy excerpts:
{policy_block}

Write the remediation recommendations now."""

    return call_ollama(
        model=RECOMMENDATION_MODEL,
        system=SYSTEM_PROMPT,
        prompt=prompt,
        json_mode=False,
        temperature=0.3,
    )
