"""
Remediation service.

Recommendations are generated entirely by the AI via RAG — the model searches
your policy/CIS documents, retrieves the relevant excerpts, and writes the
remediation guidance citing them (see app/llm/recommendation.py). There is no
pre-written recommendation content here.

The *findings* (what is wrong) are always deterministic — computed by the rules
engine from your database — and are passed in here as the grounding the AI writes
against. So the AI never decides compliance; it only explains how to fix what the
engine already found.
"""

from app.config import SEVERITY_ORDER
from app.schemas.control import Finding

# Cap how many findings are sent to the model per request so generation stays
# within the timeout on larger models (the most severe are kept).
_MAX_FINDINGS_FOR_LLM = 6


def ai_recommendations(
    hostname: str,
    findings: list[Finding],
    collection_key: str | None = None,
) -> tuple[str | None, bool]:
    """RAG-grounded remediation recommendations. The model reads excerpts
    retrieved from your documents and writes recommendations citing them.

    Returns (recommendation_text, ai_available). Text is always returned when
    there are findings (LLM output when Ollama is up, else a deterministic
    fallback built from the findings); ai_available is True only when it came
    from the model.

    Collection follows the original split: whole-control gaps are graded against
    the CIS 'standards' collection, configuration findings against your
    'master_policies'."""
    if not findings:
        return None, False

    from app.llm.recommendation import generate_recommendations

    only_presence_gaps = all(f.field.endswith("_present") for f in findings)
    collection = collection_key or ("standards" if only_presence_gaps else "master_policies")
    capped = sorted(findings, key=lambda f: SEVERITY_ORDER.get(f.severity, 99))[
        :_MAX_FINDINGS_FOR_LLM
    ]
    text, source = generate_recommendations(hostname, capped, collection_key=collection)
    return text, source == "llm"
