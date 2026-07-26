"""
Remediation service: turns deterministic findings into structured, grounded
`Recommendation` objects using the remediation knowledge base.

Grounding order per recommendation:
  1. the blueprint rule that failed (required vs observed),
  2. OUR control policy / golden-image baseline (primary reference),
  3. a CIS Safeguard (supporting reference).

An optional LLM narrative summary can be layered on top when Ollama is
available — but it never replaces or overrides the structured, cited cards.
"""

from app.config import SEVERITY_ORDER, settings
from app.schemas.control import Finding
from app.schemas.recommendation import CisReference, Recommendation
from app.services.remediation_kb import KB, cis_for

_SEVERITY_JUSTIFICATION = {
    "critical": "Rated CRITICAL: this removes a primary preventive or detective "
    "control, leaving the endpoint directly exposed — remediate immediately.",
    "high": "Rated HIGH: a required protection is disabled or a defense-in-depth "
    "layer is missing, materially raising risk — remediate within one business day.",
    "medium": "Rated MEDIUM: the control is present but has drifted from the "
    "approved baseline, reducing assurance — remediate within the standard SLA.",
    "low": "Rated LOW: a minor deviation from the baseline — remediate during "
    "routine maintenance.",
}


def _fmt(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def _generic_entry(finding: Finding) -> dict:
    return {
        "action": f"Remediate {finding.field}",
        "policy": f"{finding.control_type.title()} blueprint",
        "cis": None,
        "why": finding.description,
        "steps": [f"Bring '{finding.field}' to the required value ({_fmt(finding.expected)})."],
    }


def build_recommendations(findings: list[Finding]) -> list[Recommendation]:
    """Deterministic, severity-ordered structured recommendations."""
    ordered = sorted(findings, key=lambda f: SEVERITY_ORDER.get(f.severity, 99))
    recs: list[Recommendation] = []
    for f in ordered:
        entry = KB.get(f.field) or _generic_entry(f)
        cis_tuple = cis_for(entry.get("cis"))
        cis = (
            CisReference(safeguard=cis_tuple[0], title=cis_tuple[1], function=cis_tuple[2])
            if cis_tuple
            else None
        )
        justification = _SEVERITY_JUSTIFICATION.get(f.severity, "")
        recs.append(
            Recommendation(
                control_type=f.control_type,
                field=f.field,
                severity=f.severity,
                title=entry["action"],
                finding=f.description,
                observed=_fmt(f.actual),
                required=_fmt(f.expected),
                why=f"{entry['why']} {justification}".strip(),
                blueprint_rule=f"Required: {f.field} = {_fmt(f.expected)} "
                f"(observed {_fmt(f.actual)}).",
                policy_reference=entry["policy"],
                cis=cis,
                steps=list(entry["steps"]),
            )
        )
    return recs


def render_text(hostname: str, recs: list[Recommendation]) -> str:
    """Plain-text rendering used by the PDF report and any text-only surface."""
    if not recs:
        return f"{hostname} meets every blueprint rule. No remediation required."
    lines: list[str] = []
    for i, r in enumerate(recs, start=1):
        cis = f" | CIS Safeguard {r.cis.safeguard} ({r.cis.function}): {r.cis.title}" if r.cis else ""
        lines.append(f"Recommendation {i} [{r.severity.upper()}] — {r.title}")
        lines.append(f"  Finding: {r.finding} (observed {r.observed}, required {r.required})")
        lines.append(f"  Reference: {r.policy_reference}{cis}")
        lines.append(f"  Why: {r.why}")
        for step in r.steps:
            lines.append(f"    • {step}")
        lines.append("")
    return "\n".join(lines).strip()


_SUMMARY_SYSTEM = """You are a security assurance analyst. In 2-4 sentences, write \
an executive summary of this endpoint's most important security gaps and what to \
prioritise first. Be specific but concise. Do NOT list every finding or write \
step-by-step instructions — the detailed remediation is provided separately."""


def ai_summary(hostname: str, findings: list[Finding]) -> tuple[str | None, bool]:
    """Optional, concise LLM executive summary on top of the structured cards.
    Fetched on demand (never blocks a page load). Returns (summary_text,
    ai_available); only returns text when it genuinely came from the LLM.

    Uses a deliberately short prompt/response so generation stays responsive —
    the exhaustive detail already lives in the deterministic recommendation
    cards, so the summary only needs to give the priorities."""
    from app.llm.ollama_client import OllamaUnavailable, call_ollama, is_ollama_up

    if not findings or not settings.AI_ENABLED or not is_ollama_up():
        return None, False

    capped = sorted(findings, key=lambda f: SEVERITY_ORDER.get(f.severity, 99))[:8]
    block = "\n".join(
        f"- [{f.severity}] {f.control_type}.{f.field}: {f.description}" for f in capped
    )
    extra = f" (+{len(findings) - len(capped)} more)" if len(findings) > len(capped) else ""
    prompt = f"Endpoint {hostname} failed these blueprint checks{extra}:\n{block}\n\nExecutive summary:"
    try:
        text = call_ollama(
            model=settings.SUMMARY_MODEL,
            system=_SUMMARY_SYSTEM,
            prompt=prompt,
            temperature=0.3,
        )
        return text.strip(), True
    except OllamaUnavailable:
        return None, False
