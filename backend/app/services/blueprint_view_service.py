"""
Blueprint view service: assembles the human-readable "what we validate against"
picture from the same sources the engine actually uses — the `blueprint_rules`
table, the remediation knowledge base (for CIS + policy references), the
golden-image reference config, and the internal AV/EDR policy document.
"""

import re
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.repositories import blueprint_repo
from app.schemas.blueprint import (
    BlueprintRuleView,
    BlueprintView,
    ControlBlueprint,
    PolicyDoc,
)
from app.schemas.common import CONTROL_LABELS, ControlType
from app.schemas.recommendation import CisReference
from app.services.remediation_kb import KB, cis_for

_OP_LABEL = {"eq": "must equal", "gte": "must be at least", "lte": "must be at most"}
_CONTROL_ORDER = ["antivirus", "edr", "firewall", "bitlocker"]

# The golden-image reference rows the firewall/bitlocker rules are derived from.
_GOLDEN_IMAGES = {
    "firewall": {
        "reference": "GOLDEN-IMAGE-FW (firewall_blueprint.csv)",
        "Domain Profile": "Enabled",
        "Private Profile": "Enabled",
        "Public Profile": "Enabled",
        "Default Inbound Action": "Block",
    },
    "bitlocker": {
        "reference": "GOLDEN-IMAGE-ENC (bitlocker_blueprint.csv)",
        "Encryption Method": "XtsAes256",
        "Protection Status": "On",
        "Percentage Encrypted": "100",
        "Volume Status": "FullyEncrypted",
        "Encrypted": "True",
    },
}


def _cis_for_field(field: str) -> CisReference | None:
    entry = KB.get(field)
    tup = cis_for(entry.get("cis")) if entry else None
    return CisReference(safeguard=tup[0], title=tup[1], function=tup[2]) if tup else None


def _policy_ref(field: str) -> str:
    entry = KB.get(field)
    return entry["policy"] if entry else ""


def build_blueprint_view(db: Session) -> BlueprintView:
    rules = blueprint_repo.get_all(db)
    by_control: dict[str, list] = {}
    for r in rules:
        by_control.setdefault(r.control_type, []).append(r)

    controls: list[ControlBlueprint] = []
    for ct in _CONTROL_ORDER:
        views = [
            BlueprintRuleView(
                field=r.field,
                operator=r.operator,
                operator_label=_OP_LABEL.get(r.operator, r.operator),
                expected=r.expected,
                severity=r.severity,
                description=r.description,
                cis=_cis_for_field(r.field),
                policy_reference=_policy_ref(r.field),
            )
            for r in by_control.get(ct, [])
        ]
        controls.append(
            ControlBlueprint(
                control_type=ct,
                label=CONTROL_LABELS[ControlType(ct)],
                rule_count=len(views),
                golden_image=_GOLDEN_IMAGES.get(ct),
                rules=views,
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


_POLICY_HEAD = re.compile(r"^Policy\s+([A-Z]+-\d+):\s*(.+)$")


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
        head = _POLICY_HEAD.match(lines[0].strip())
        if head:
            entries.append(
                PolicyDoc(
                    id=head.group(1),
                    title=head.group(2).strip(),
                    text=" ".join(l.strip() for l in lines[1:]).strip(),
                )
            )
    return entries
