"""
Blueprint view service: assembles the human-readable "what we validate against"
picture from the blueprint_rules table and the golden-image reference config.

The CIS Safeguard and policy reference for each rule are INFERRED by the AI —
there is no pre-written field→standard mapping file. For each rule we:
  1. RETRIEVE candidate CIS Safeguards by semantically searching the CIS
     document (RAG), and
  2. let the LLM CHOOSE the single best-fitting safeguard from those candidates
     (one batched call for all rules).
The safeguard identifiers and titles always come from the retrieved document
text, so the model can only pick among real safeguards — it can't invent one.

Because the blueprint rules are static, the inferred mapping is cached in
process after the first build, so the Blueprint page loads quickly thereafter.
If the AI/RAG layer is offline, it falls back to the nearest retrieved safeguard
(or nothing), and the rules (the real baseline) always render regardless.
"""

import json
import re
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.llm.ollama_client import OllamaUnavailable, call_ollama, is_ollama_up
from app.rag.retriever import retrieve_policy_context
from app.repositories import blueprint_repo
from app.schemas.blueprint import (
    BlueprintRuleView,
    BlueprintView,
    ControlBlueprint,
    PolicyDoc,
)
from app.schemas.common import CONTROL_LABELS, ControlType
from app.schemas.recommendation import CisReference

_OP_LABEL = {"eq": "must equal", "gte": "must be at least", "lte": "must be at most"}
_CONTROL_ORDER = ["antivirus", "edr", "firewall", "bitlocker"]

# Parses the heading of a retrieved CIS chunk, e.g.
#   "CIS Safeguard 10.2 (Devices / Protect): Configure Automatic ... Updates"
_CIS_HEAD = re.compile(r"CIS Safeguard\s+(\d+(?:\.\d+)?)\s*\(([^)]+)\):\s*([^\n]+)")
# Parses the heading of a retrieved policy chunk, e.g. "Policy AV-01: Signature Freshness"
_POLICY_HEAD = re.compile(r"Policy\s+([A-Z]+-\d+):\s*([^\n]+)")

# Firewall/BitLocker are enforced by golden-image baselines (no policy prose doc).
_GOLDEN_POLICY = {
    "firewall": "Firewall golden-image baseline (Policy-FW-01)",
    "bitlocker": "BitLocker golden-image baseline",
}

_GOLDEN_IMAGES = {
    "firewall": {
        "reference": "GOLDEN-IMAGE-FW (firewall_blueprint.csv)",
        "Domain Profile": "Enabled", "Private Profile": "Enabled",
        "Public Profile": "Enabled", "Default Inbound Action": "Block",
    },
    "bitlocker": {
        "reference": "GOLDEN-IMAGE-ENC (bitlocker_blueprint.csv)",
        "Encryption Method": "XtsAes256", "Protection Status": "On",
        "Percentage Encrypted": "100", "Volume Status": "FullyEncrypted", "Encrypted": "True",
    },
}

# Cache of the AI-inferred mapping: field -> (CisReference|None, policy_ref).
_MAP_CACHE: dict[str, tuple[CisReference | None, str]] = {}

_CIS_CHOOSE_SYSTEM = (
    "You map an internal security rule to the single best-fitting CIS Safeguard, "
    "choosing ONLY from the candidate safeguards listed for each rule. Return ONLY "
    "a JSON object mapping each rule id to the chosen safeguard number (a string). "
    "Never invent a safeguard number that is not in that rule's candidates."
)


_POLICY_LABEL = {
    "antivirus": "Antivirus control policy (EdrAv-policy.txt)",
    "edr": "EDR control policy (EdrAv-policy.txt)",
    "firewall": "Firewall golden-image baseline (Policy-FW-01)",
    "bitlocker": "BitLocker golden-image baseline",
}


def _cis_candidates(description: str) -> dict[str, CisReference]:
    """Per-rule RAG search over the CIS doc → this rule's own candidate
    safeguards (details taken straight from the retrieved text)."""
    out: dict[str, CisReference] = {}
    for h in retrieve_policy_context(description, collection_key="standards", top_k=4):
        m = _CIS_HEAD.search(h["text"])
        if m and m.group(1) not in out:
            out[m.group(1)] = CisReference(
                safeguard=m.group(1), function=m.group(2).strip(), title=m.group(3).strip()
            )
    return out


def _llm_choose(rules, cand_by_field: dict[str, dict]) -> dict[str, str]:
    """One bounded LLM call: for each rule, pick the best safeguard from that
    rule's OWN candidate list. Returns field -> safeguard number ({} on failure)."""
    lines = []
    for r in rules:
        cands = cand_by_field.get(r.field, {})
        if not cands:
            continue
        opts = "; ".join(f"{sid}={ref.title}" for sid, ref in cands.items())
        lines.append(f'- {r.field} | "{r.description}" | candidates: {opts}')
    if not lines:
        return {}
    prompt = (
        "For each rule choose the single best-fitting CIS Safeguard from that "
        "rule's own candidate list.\n\n" + "\n".join(lines)
        + '\n\nReturn JSON mapping each rule id to the chosen safeguard number, '
        'e.g. {"av_installed": "10.1"}.'
    )
    try:
        raw = call_ollama(
            model=settings.EXPLANATION_MODEL, system=_CIS_CHOOSE_SYSTEM,
            prompt=prompt, json_mode=True, temperature=0.0, timeout=80,
        )
        parsed = json.loads(raw)
        return {k: str(v) for k, v in parsed.items()} if isinstance(parsed, dict) else {}
    except (OllamaUnavailable, json.JSONDecodeError, TypeError, ValueError):
        return {}


# Whether to add an LLM "choose the best candidate" pass on top of the RAG
# nearest-match. Off by default: on this corpus it lowered accuracy (the model
# picks from semantically-retrieved candidates that are often the wrong
# safeguard) and added ~70s. Flip on to experiment.
_USE_LLM_REFINEMENT = False


def _ensure_cache(rules) -> None:
    """Populate the inferred-mapping cache in one pass from per-rule RAG search;
    cached afterwards so the page is instant."""
    if all(r.field in _MAP_CACHE for r in rules):
        return

    cand_by_field = {r.field: _cis_candidates(r.description) for r in rules}
    chosen = (
        _llm_choose(rules, cand_by_field)
        if _USE_LLM_REFINEMENT and is_ollama_up()
        else {}
    )

    for r in rules:
        cands = cand_by_field[r.field]
        cis: CisReference | None = None
        pick = chosen.get(r.field)
        if pick and pick in cands:
            cis = cands[pick]
        elif cands:
            cis = next(iter(cands.values()))  # nearest retrieved safeguard
        _MAP_CACHE[r.field] = (cis, _POLICY_LABEL.get(r.control_type, ""))


def build_blueprint_view(db: Session) -> BlueprintView:
    rules = blueprint_repo.get_all(db)
    _ensure_cache(rules)

    by_control: dict[str, list] = {}
    for r in rules:
        by_control.setdefault(r.control_type, []).append(r)

    controls: list[ControlBlueprint] = []
    for ct in _CONTROL_ORDER:
        views = []
        for r in by_control.get(ct, []):
            cis, policy = _MAP_CACHE.get(r.field, (None, ""))
            views.append(
                BlueprintRuleView(
                    field=r.field, operator=r.operator,
                    operator_label=_OP_LABEL.get(r.operator, r.operator),
                    expected=r.expected, severity=r.severity, description=r.description,
                    cis=cis, policy_reference=policy,
                )
            )
        controls.append(
            ControlBlueprint(
                control_type=ct, label=CONTROL_LABELS[ControlType(ct)],
                rule_count=len(views), golden_image=_GOLDEN_IMAGES.get(ct), rules=views,
            )
        )

    return BlueprintView(
        total_rules=len(rules),
        controls=controls,
        policies=_parse_policies(),
        standard_name="CIS Critical Security Controls v8.1.2",
        standard_controls=18,
        standard_safeguards=153,
    )


_POLICY_LINE = re.compile(r"^Policy\s+([A-Z]+-\d+):\s*(.+)$")


def _parse_policies() -> list[PolicyDoc]:
    """Parse the internal AV/EDR policy document into structured entries."""
    path = Path(settings.POLICIES_ROOT) / "master_policies" / "EdrAv-policy.txt"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    entries: list[PolicyDoc] = []
    for block in re.split(r"\n\s*\n", text):
        lines = block.strip().splitlines()
        if not lines:
            continue
        head = _POLICY_LINE.match(lines[0].strip())
        if head:
            entries.append(
                PolicyDoc(id=head.group(1), title=head.group(2).strip(),
                          text=" ".join(l.strip() for l in lines[1:]).strip())
            )
    return entries
