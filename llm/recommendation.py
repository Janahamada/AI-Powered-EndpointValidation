"""
LLM call 2, now with two entry points sharing one core:

- generate_compliance_recommendations(): compliance-check branch.
  Findings come from compliance/comparator.py's blueprint diff.
  RAG queries ONLY the 'master_policies' collection.

- generate_existence_recommendations(): existence-check branch.
  Findings are just "this control isn't installed at all" (no
  configuration/compliance evaluation — that's the compliance branch's
  job). RAG queries ONLY the 'standards' collection (CIS controls).

Neither call ever sees raw controls or blueprint rules directly — only
a findings list that's already been decided deterministically upstream,
so the LLM's job stays "explain and cite," never "decide."
"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RECOMMENDATION_MODEL, RAG_TOP_K
from llm.ollama_client import call_ollama
from models import ComplianceResult, Finding
from rag.retriever import retrieve_policy_context

COMPLIANCE_SYSTEM_PROMPT = """You are a security compliance assistant. You will be \
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

EXISTENCE_SYSTEM_PROMPT = """You are a security compliance assistant. You will be \
given a list of security controls that are completely missing (not installed at all) \
on one asset, and relevant excerpts from the CIS Controls standard. Write clear, \
actionable recommendations for deploying the missing control(s).

Rules:
- This is about a control's EXISTENCE, not its configuration or compliance status —
  do not comment on settings, thresholds, or configuration quality. The control isn't
  there at all; the recommendation is to deploy it.
- Address every missing control provided. Do not invent gaps that weren't given to you.
- For each recommendation, cite which CIS control/safeguard it's grounded in, by
  source filename and the safeguard identifier mentioned in the excerpt if present.
- Be concise and operational — this goes to a security analyst, not an executive summary.
- If the provided excerpts don't cover a missing control, say so rather than guessing.
"""


def _findings_block(findings: list[Finding]) -> str:
    return "\n".join(
        f"- [{f.severity}] {f.field}: expected {f.expected}, actual {f.actual} — {f.description}"
        for f in findings
    )


def _policy_block(retrieved: list[dict]) -> str:
    return "\n".join(f"[{doc['source']}] {doc['text']}" for doc in retrieved) \
        or "(no matching excerpts retrieved)"


def _retrieval_query(findings: list[Finding]) -> str:
    """Build the semantic query from the findings themselves, not the raw
    user prompt — the user's original message ('check 10.1.2.3') carries
    no retrievable signal on its own."""
    return " ".join(f"{f.description} (field: {f.field})" for f in findings)


def generate_compliance_recommendations(compliance_result: ComplianceResult) -> str:
    if compliance_result.compliant:
        return "Asset is compliant with the blueprint. No recommendations needed."

    query = _retrieval_query(compliance_result.findings)
    retrieved = retrieve_policy_context(query, collection_key="master_policies", top_k=RAG_TOP_K)

    prompt = f"""Findings for asset {compliance_result.hostname}:
{_findings_block(compliance_result.findings)}

Relevant policy excerpts:
{_policy_block(retrieved)}

Write the remediation recommendations now."""

    return call_ollama(
        model=RECOMMENDATION_MODEL,
        system=COMPLIANCE_SYSTEM_PROMPT,
        prompt=prompt,
        json_mode=False,
        temperature=0.3,
    )


def generate_existence_recommendations(hostname: str, missing_controls: list[Finding]) -> str:
    if not missing_controls:
        return "All expected controls are present. No recommendations needed."

    query = _retrieval_query(missing_controls)
    retrieved = retrieve_policy_context(query, collection_key="standards", top_k=RAG_TOP_K)

    prompt = f"""Missing controls for asset {hostname}:
{_findings_block(missing_controls)}

Relevant CIS Controls excerpts:
{_policy_block(retrieved)}

Write the deployment recommendations now."""

    return call_ollama(
        model=RECOMMENDATION_MODEL,
        system=EXISTENCE_SYSTEM_PROMPT,
        prompt=prompt,
        json_mode=False,
        temperature=0.3,
    )