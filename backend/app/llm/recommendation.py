"""
RAG-grounded remediation recommendations.

Gemini generation is used only for text generation. All embeddings are handled
locally and retrieval is performed over Chroma collections. The model receives
retrieved policy excerpts and a strict prompt template that ensures explicit
recommendation output.
"""

from app.config import SEVERITY_ORDER, settings
from app.llm.gemini_client import call_gemini, is_gemini_enabled
from app.rag.retriever import retrieve_policy_context
from app.schemas.control import Finding

COMPLIANCE_SYSTEM_PROMPT = """You are a security compliance assistant. You will be \
given a list of control findings for one asset and relevant excerpts from internal \
policy documents. Write remediation recommendations using the exact template \
provided in the prompt.

Rules:
- Do not invent findings or new policy structure.
- Do not determine severity; the findings are already grouped by severity.
- Use the provided policy metadata exactly: Policy, Source, and Text.
- Write one recommendation per finding, in the template format.
- If a finding is not covered by the provided excerpts, say so clearly under that finding.
- Do not add extra sections, summaries, or bullet lists beyond the template.
"""

EXISTENCE_SYSTEM_PROMPT = """You are a security compliance assistant. You will be \
given a list of missing security controls for one asset and relevant excerpts from \
the CIS Controls standard. Write remediation recommendations using the exact \
template provided in the prompt.

Rules:
- This is about a control's EXISTENCE, not its configuration.
- Do not invent gaps or new findings.
- Use the provided policy metadata exactly: Policy, Source, and Text.
- Write one recommendation per finding, in the template format.
- If a finding is not covered by the provided excerpts, say so clearly under that finding.
- Do not add extra sections, summaries, or bullet lists beyond the template.
"""


def _findings_by_severity_block(findings: list[Finding]) -> str:
    groups: dict[str, list[str]] = {
        "critical": [],
        "high": [],
        "medium": [],
        "low": [],
    }
    for f in findings:
        severity = f.severity.lower()
        if severity not in groups:
            severity = "low"
        groups[severity].append(f.description)

    lines = []
    for severity in ("critical", "high", "medium", "low"):
        if groups[severity]:
            lines.append(f"{severity.title()} Findings")
            lines.extend(f"- {desc}" for desc in groups[severity])
            lines.append("")

    return "\n".join(lines).strip()


def _policy_block(retrieved: list[dict]) -> str:
    if not retrieved:
        return "(no matching excerpts retrieved)"

    blocks = []
    for d in retrieved:
        blocks.append(
            f"Policy: {d.get('policy', 'unknown')}\n"
            f"Source: {d.get('source', 'unknown')}\n"
            f"Text:\n{d.get('text', '').strip()}\n"
            "---------------------"
        )

    return "\n".join(blocks)


def _retrieval_query(finding: Finding) -> str:
    return f"{finding.description} (field: {finding.field})"


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
    print("AI enabled:", is_gemini_enabled())
    print("Calling Gemini...")
    if not findings:
        return (
            f"{hostname} is compliant with the blueprint. No recommendations needed.",
            "none",
        )

    if not is_gemini_enabled():
        return _deterministic_fallback(hostname, findings), "fallback"

    system = (
        EXISTENCE_SYSTEM_PROMPT
        if collection_key == "standards"
        else COMPLIANCE_SYSTEM_PROMPT
    )

    retrieved = []
    seen_texts = set()
    per_find_top_k = max(settings.RAG_TOP_K, 5)
    for f in findings:
        q = _retrieval_query(f)
        try:
            pieces = retrieve_policy_context(q, collection_key=collection_key, top_k=per_find_top_k)
        except Exception:
            pieces = []
        for d in pieces:
            text = d.get("text", "")
            if text and text not in seen_texts:
                retrieved.append(d)
                seen_texts.add(text)

    prompt = f"""Findings for asset {hostname}:
{_findings_by_severity_block(findings)}

Relevant policy/standard excerpts:
{_policy_block(retrieved)}

Instruction:
- For each finding above, write exactly one recommendation.
- Use the following output format for every finding:

Finding: <finding description>
Severity: <severity>
Policy: <policy identifier or standard 'no matching excerpt found'>
Source: <source filename>
Recommendation: <one short, actionable sentence. If the excerpt matches, end with the source filename in parentheses.>

Do not add any other sections, summaries, or bullet lists.
"""

    try:
        text = call_gemini(
            model=settings.GEMINI_MODEL,
            system=system,
            prompt=prompt,
            temperature=0.3,
        )
        print("Gemini succeeded")
        return text.strip(), "llm"
    except Exception as e:
        print("Falling back:", e)
        print("Gemini exception:", repr(e))
        raise
