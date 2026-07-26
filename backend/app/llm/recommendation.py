"""
RAG-grounded remediation recommendations (the original AI behaviour).

The model does NOT invent recommendations from general knowledge: it is handed
excerpts that were semantically retrieved from YOUR own documents, and asked to
write remediation guidance that cites them. This is the purpose of the RAG
layer — "look in the policy/standard docs and answer from them."

Two collections, one per use case (as in the original design):
  - compliance findings  -> RAG over 'master_policies' (your AV/EDR policy)
  - existence gaps        -> RAG over 'standards' (CIS Controls)

Graceful degradation: if Ollama or Chroma is unavailable, a deterministic
summary built from the same findings is returned instead (source="fallback"),
so the feature never errors.
"""

from app.config import SEVERITY_ORDER, settings
from app.llm.ollama_client import OllamaUnavailable, call_ollama, is_ollama_up
from app.rag.retriever import retrieve_policy_context
from app.schemas.control import Finding

COMPLIANCE_SYSTEM_PROMPT = """You are a security compliance assistant. You will be \
given a list of control findings for one asset (fields that failed the security \
blueprint) and relevant excerpts from internal policies and standards. Write \
clear, actionable remediation recommendations.

Rules:
- Address every finding provided. Do not invent findings that weren't given to you.
- For each recommendation, cite which policy excerpt it's grounded in, by source filename.
- Order recommendations by severity: critical first, then high, medium, low.
- Keep each recommendation to ONE short sentence plus its citation — be brief.
- If the provided excerpts don't cover a finding, say so rather than guessing.
- Where relevant, reference the applicable master policy.
"""

EXISTENCE_SYSTEM_PROMPT = """You are a security compliance assistant. You will be \
given a list of security controls that are completely missing (not installed at \
all) on one asset, and relevant excerpts from the CIS Controls standard. Write \
clear, actionable recommendations for deploying the missing control(s).

Rules:
- This is about a control's EXISTENCE, not its configuration — the control isn't
  there at all; the recommendation is to deploy it.
- Address every missing control provided. Do not invent gaps.
- Cite which CIS control/safeguard each recommendation is grounded in, by source filename.
- Be concise and operational.
"""


def _findings_block(findings: list[Finding]) -> str:
    return "\n".join(
        f"- [{f.severity}] {f.control_type}.{f.field}: "
        f"expected {f.expected}, actual {f.actual} — {f.description}"
        for f in findings
    )


def _policy_block(retrieved: list[dict]) -> str:
    return (
        "\n".join(f"[{d['source']}] {d['text']}" for d in retrieved)
        or "(no matching excerpts retrieved)"
    )


def _retrieval_query(findings: list[Finding]) -> str:
    """Build the semantic query from the findings themselves — the retrievable
    signal is in the descriptions, not in the raw user prompt."""
    return " ".join(f"{f.description} (field: {f.field})" for f in findings)


def _deterministic_fallback(hostname: str, findings: list[Finding]) -> str:
    ordered = sorted(findings, key=lambda f: SEVERITY_ORDER.get(f.severity, 99))
    lines = [
        f"Deterministic remediation for {hostname} — the AI narrative layer is "
        f"offline, so this is generated directly from the validated findings:\n"
    ]
    for f in ordered:
        lines.append(
            f"• [{f.severity.upper()}] {f.control_type.title()}: {f.description} "
            f"(observed {f.actual}, required {f.expected})."
        )
    return "\n".join(lines)


def generate_recommendations(
    hostname: str,
    findings: list[Finding],
    collection_key: str = "master_policies",
) -> tuple[str, str]:
    """
    Returns (recommendation_text, source) where source is "llm" (RAG-grounded
    model output), "fallback" (deterministic, AI offline), or "none".
    """
    if not findings:
        return (
            f"{hostname} is compliant with the blueprint. No recommendations needed.",
            "none",
        )

    if not settings.AI_ENABLED or not is_ollama_up():
        return _deterministic_fallback(hostname, findings), "fallback"

    system = (
        EXISTENCE_SYSTEM_PROMPT
        if collection_key == "standards"
        else COMPLIANCE_SYSTEM_PROMPT
    )
    # 1) RETRIEVE: pull the most relevant excerpts from the chosen doc collection.
    query = _retrieval_query(findings)
    retrieved = retrieve_policy_context(query, collection_key=collection_key)

    # 2) GENERATE: the model writes recommendations grounded in those excerpts.
    prompt = f"""Findings for asset {hostname}:
{_findings_block(findings)}

Relevant policy/standard excerpts:
{_policy_block(retrieved)}

Write the remediation recommendations now."""

    try:
        text = call_ollama(
            model=settings.RECOMMENDATION_MODEL,
            system=system,
            prompt=prompt,
            temperature=0.3,
        )
        return text.strip(), "llm"
    except OllamaUnavailable:
        return _deterministic_fallback(hostname, findings), "fallback"
