"""
Grounded chat query engine.

Answers any in-scope question about the fleet, controls, policies and
blueprints — not just per-IP lookups — while guaranteeing that every answer is
derived from THIS system's own data (database, compliance engine, blueprint
rules, policy/standard documents). Every response carries a `sources` list
showing exactly where the answer came from, so nothing is unattributable.

Routing (deterministic first, LLM only for phrasing/explanation):
  1. message contains an IP            -> endpoint check (compliance/existence)
  2. policy / blueprint / golden-image -> policy lookup (blueprint rules + docs)
  3. "which / list / show"             -> list of matching endpoints
  4. "how many / rate / overall / …"   -> fleet metric (from the compliance engine)
  5. "what is / why / explain"         -> grounded explanation (RAG over policies/CIS)
  6. otherwise                         -> clarification

The facts always come from deterministic queries; the local LLM is used only to
phrase explanation answers, and even then strictly over retrieved excerpts.
"""

import re

from sqlalchemy.orm import Session

from app.config import settings
from app.llm.ollama_client import OllamaUnavailable, call_ollama, is_ollama_up
from app.rag.retriever import retrieve_policy_context
from app.repositories import asset_repo, blueprint_repo, control_repo
from app.schemas.chat import ChatResponse, ChatSource, ChatTableRow
from app.schemas.common import CONTROL_LABELS, ControlType, ValidationStatus
from app.schemas.control import Finding
from app.services import compliance_service as cs
from app.services import validation_service

_IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

_CONTROL_KEYWORDS: dict[str, list[str]] = {
    "bitlocker": ["bitlocker", "encrypt", "encryption", "disk encryption", "at rest"],
    "firewall": ["firewall", "inbound", "profile", "port"],
    "antivirus": ["antivirus", "anti-virus", "malware", "signature", "defender", "tamper", "real-time"],
    "edr": ["edr", "sensor", "endpoint detection", "check-in", "check in", "isolation"],
}

_LIST_KW = ["which ", "list ", "show me", "show all", "name the", "what endpoints",
            "what assets", "top ", "worst", "give me the endpoints"]
_FLEET_KW = ["how many", "number of", "count", "percentage", "percent", " rate", "overall",
             "average", "total", "most ", "fleet", "across", "posture", "how is our",
             "how's our", "are compliant", "are failing", "are passing", "compliance score",
             "how many endpoints"]
_POLICY_KW = ["policy", "blueprint", "golden image", "baseline", "rule", "require",
              "threshold", "standard", "cis", "benchmark", "expected value", "what should",
              "what does the", "config", "criteria"]
_DEFINE_KW = ["what is", "what's", "what are", "explain", "why is", "why does", "why do",
              "how does", "tell me about", "meaning of", "purpose of", "define", "difference between"]


# --------------------------------------------------------------------------- #
# Detection helpers
# --------------------------------------------------------------------------- #
def _find_ip(msg: str) -> str | None:
    m = _IP_RE.search(msg)
    if not m:
        return None
    from app.schemas.control import IP_PATTERN

    return m.group(0) if IP_PATTERN.match(m.group(0)) else None


def _detect_control(msg: str) -> str | None:
    m = msg.lower()
    for control, kws in _CONTROL_KEYWORDS.items():
        if any(k in m for k in kws):
            return control
    return None


def _has(msg: str, kws: list[str]) -> bool:
    m = msg.lower()
    return any(k in m for k in kws)


def _engine_source(n: int) -> ChatSource:
    rules = "21"
    return ChatSource(
        kind="engine",
        label=f"Compliance engine — {n} endpoint(s) evaluated against {rules} blueprint rules",
    )


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def answer(db: Session, message: str) -> ChatResponse:
    msg = message.strip()
    if not msg:
        return _clarify("Ask me about an endpoint, a control, the fleet, or a policy.")

    ip = _find_ip(msg)
    if ip:
        return _handle_endpoint(db, msg, ip)
    if _has(msg, _POLICY_KW):
        return _handle_policy(db, msg)
    if _has(msg, _LIST_KW):
        return _handle_list(db, msg)
    if _has(msg, _FLEET_KW):
        return _handle_fleet_metric(db, msg)
    if _has(msg, _DEFINE_KW):
        return _handle_explanation(db, msg)
    # Last resort: try a grounded explanation; if nothing retrievable, clarify.
    explained = _handle_explanation(db, msg)
    if explained.sources:
        return explained
    return _clarify(
        "I can answer questions about a specific endpoint (by IP), the fleet's "
        "compliance metrics, which endpoints fail a control, or what a policy / "
        "blueprint requires. Could you rephrase along those lines?"
    )


def _clarify(text: str) -> ChatResponse:
    return ChatResponse(status="clarification_needed", answer_type="clarification", message=text)


# --------------------------------------------------------------------------- #
# 1. Endpoint (per-IP) — compliance / existence
# --------------------------------------------------------------------------- #
def _handle_endpoint(db: Session, msg: str, ip: str) -> ChatResponse:
    # Deterministic intent: an existence question ("is it installed / present /
    # in inventory") unless it clearly asks about compliance. Default to the
    # richer compliance answer. No LLM call needed here.
    m = msg.lower()
    existence_words = ["installed", "present", "exist", "inventory", "deployed", "have all", "has all"]
    compliance_words = ["compliant", "comply", "why", "policy", "blueprint", "finding", "fix", "remediat", "posture"]
    if any(w in m for w in existence_words) and not any(w in m for w in compliance_words):
        intent = "existence_check"
    else:
        intent = "compliance_check"

    asset = asset_repo.get_by_ip(db, ip)
    if asset is None:
        return ChatResponse(
            status="not_found",
            answer_type="endpoint",
            ip=ip,
            message=f"No endpoint with IP {ip} exists in the asset inventory.",
            sources=[ChatSource(kind="inventory", label="Asset inventory (assets table)")],
        )

    record = control_repo.get_control_record(db, asset.hostname)
    rules = blueprint_repo.get_all(db)
    controls = validation_service.validate_controls(record, rules)

    sources = [
        ChatSource(kind="inventory", label=f"Asset inventory — {asset.hostname} ({ip})"),
        ChatSource(kind="database", label="Control evidence: antivirus, EDR, firewall, BitLocker tables"),
        ChatSource(kind="engine", label="Compliance engine — validated against 21 blueprint rules"),
    ]

    if intent == "existence_check":
        present = {c.control_type: c.present for c in controls}
        missing = [c for c in controls if not c.present]
        present_labels = [c.label for c in controls if c.present]
        parts = [
            f"{asset.hostname} ({ip}) is in the inventory, owned by {asset.business_owner}.",
            "Controls with evidence: " + (", ".join(present_labels) if present_labels else "none") + ".",
        ]
        missing_findings = [
            Finding(control_type=c.control_type, field=f"{c.control_type}_present",
                    expected=True, actual=False, severity="high",
                    description=f"{c.label} has no evidence on file for this endpoint.")
            for c in missing
        ]
        parts.append("Missing: " + ", ".join(c.label for c in missing) + "." if missing
                     else "All four controls are present.")
        if missing:
            parts.append("Open the endpoint and click 'Generate AI recommendations' for the AI's remediation guidance from your CIS docs.")
        return ChatResponse(
            status="ok", answer_type="endpoint", use_case="existence_check",
            hostname=asset.hostname, ip=ip, message=" ".join(parts),
            findings=missing_findings, sources=sources,
            ai_available=is_ollama_up(), data={"controls_present": present},
        )

    findings = validation_service.all_findings(controls)
    score = validation_service.compliance_score(controls)
    status_value = validation_service.endpoint_status(controls)
    compliant = len(findings) == 0
    parts = [f"{asset.hostname} ({ip}) scores {score}% and is currently {status_value}."]
    if compliant:
        parts.append("It meets every blueprint rule across all four controls.")
    else:
        crit = sum(1 for f in findings if f.severity == "critical")
        high = sum(1 for f in findings if f.severity == "high")
        parts.append(f"{len(findings)} finding(s) — {crit} critical, {high} high. "
                     "Open the endpoint and click 'Generate AI recommendations' for the AI's "
                     "remediation guidance, written from your policy & CIS documents.")
    return ChatResponse(
        status="ok", answer_type="endpoint", use_case="compliance_check",
        hostname=asset.hostname, ip=ip, compliant=compliant, message=" ".join(parts),
        findings=findings, sources=sources,
        ai_available=is_ollama_up(),
        data={"compliance_score": score, "status": status_value},
    )


# --------------------------------------------------------------------------- #
# 2. Fleet metric
# --------------------------------------------------------------------------- #
def _handle_fleet_metric(db: Session, msg: str) -> ChatResponse:
    summary = cs.build_dashboard(db)
    total = summary.total_endpoints
    control = _detect_control(msg)
    m = msg.lower()
    sources = [_engine_source(total)]

    # Critical / high findings counts
    if "critical" in m:
        n = summary.critical_findings
        return _metric_answer(
            f"There are {n} critical finding(s) across the fleet of {total} endpoints.",
            {"critical_findings": n}, sources, control)
    if "high" in m and "finding" in m:
        n = summary.high_risk_findings
        return _metric_answer(
            f"There are {n} high-severity finding(s) across the fleet.",
            {"high_findings": n}, sources, control)

    # Per-control question
    if control:
        stat = next((p for p in summary.per_control if p.control_type == control), None)
        if stat:
            label = CONTROL_LABELS[ControlType(control)]
            failing = stat.fail_count + stat.warning_count + stat.no_data_count
            if any(k in m for k in ["fail", "not ", "non-compliant", "noncompliant", "missing", "without", "unencrypted"]):
                msg_txt = (f"{failing} of {total} endpoints are not fully compliant with {label} "
                           f"({stat.fail_count} FAIL, {stat.warning_count} WARNING, {stat.no_data_count} no-data). "
                           f"{stat.pass_count} pass.")
            elif any(k in m for k in ["pass", "compliant", "meet"]):
                msg_txt = f"{stat.pass_count} of {total} endpoints pass {label} ({stat.compliance_rate}% compliance rate)."
            else:
                msg_txt = (f"{label}: {stat.compliance_rate}% compliance rate — "
                           f"{stat.pass_count} pass, {stat.warning_count} warning, {stat.fail_count} fail"
                           + (f", {stat.no_data_count} no-data." if stat.no_data_count else "."))
            sources.append(ChatSource(kind="blueprint", label=f"{label} blueprint rules"))
            return _metric_answer(msg_txt, stat.model_dump(), sources, control)

    # Overall / general posture
    sb = summary.endpoint_status_breakdown
    msg_txt = (f"The fleet's overall assurance score is {summary.overall_compliance_score}% across "
               f"{total} endpoints — {sb.get('PASS',0)} passing, {sb.get('WARNING',0)} warning, "
               f"{sb.get('FAIL',0)} failing, {sb.get('NO_DATA',0)} no-data. "
               f"{summary.critical_findings} critical and {summary.high_risk_findings} high findings are open.")
    return _metric_answer(msg_txt, {
        "overall_score": summary.overall_compliance_score,
        "status_breakdown": sb,
        "findings_by_severity": summary.findings_by_severity,
    }, sources, None)


def _metric_answer(message: str, data: dict, sources: list[ChatSource], control: str | None) -> ChatResponse:
    return ChatResponse(status="ok", answer_type="fleet_metric", message=message,
                        sources=sources, data=data)


# --------------------------------------------------------------------------- #
# 3. List of endpoints
# --------------------------------------------------------------------------- #
def _handle_list(db: Session, msg: str) -> ChatResponse:
    evaluated = cs.evaluate_all(db)
    control = _detect_control(msg)
    m = msg.lower()
    want_fail = any(k in m for k in ["fail", "not ", "non-compliant", "noncompliant", "missing",
                                     "without", "unencrypted", "worst", "risk", "critical"])

    rows: list[ChatTableRow] = []
    if control:
        label = CONTROL_LABELS[ControlType(control)]
        matched = []
        for ev in evaluated:
            cv = next((c for c in ev.controls if c.control_type == control), None)
            if not cv:
                continue
            if want_fail and cv.status != ValidationStatus.PASS.value:
                matched.append((ev, cv))
            elif not want_fail and cv.status == ValidationStatus.PASS.value:
                matched.append((ev, cv))
        matched.sort(key=lambda t: t[0].score)
        for ev, cv in matched[:50]:
            rows.append(ChatTableRow(hostname=ev.record.hostname, values={
                "ip": ev.asset.ip_address if ev.asset else "—",
                "owner": ev.asset.business_owner if ev.asset else "—",
                f"{control}_status": cv.status,
                "score": ev.score,
            }))
        verb = "are not fully compliant with" if want_fail else "pass"
        message = f"{len(matched)} endpoint(s) {verb} {label}" + (
            f" (showing {len(rows)})." if len(matched) > len(rows) else ".")
        sources = [_engine_source(len(evaluated)), ChatSource(kind="blueprint", label=f"{label} blueprint rules")]
    else:
        # List by overall status (default: failing/worst)
        target = evaluated
        if want_fail:
            target = [e for e in evaluated if e.status in (ValidationStatus.FAIL.value, ValidationStatus.NO_DATA.value)]
        target = sorted(target, key=lambda e: e.score)
        for ev in target[:50]:
            rows.append(ChatTableRow(hostname=ev.record.hostname, values={
                "ip": ev.asset.ip_address if ev.asset else "—",
                "owner": ev.asset.business_owner if ev.asset else "—",
                "status": ev.status,
                "score": ev.score,
                "critical": sum(1 for f in ev.findings if f.severity == "critical"),
            }))
        message = f"{len(target)} endpoint(s) " + ("are failing or at risk" if want_fail else "in the fleet") + (
            f" (showing {len(rows)})." if len(target) > len(rows) else ".")
        sources = [_engine_source(len(evaluated))]

    return ChatResponse(status="ok", answer_type="list", message=message, table=rows, sources=sources)


# --------------------------------------------------------------------------- #
# 4. Policy / blueprint lookup
# --------------------------------------------------------------------------- #
def _handle_policy(db: Session, msg: str) -> ChatResponse:
    control = _detect_control(msg)
    rules = blueprint_repo.get_all(db)
    if control:
        rules = [r for r in rules if r.control_type == control]
        label = CONTROL_LABELS[ControlType(control)]
    else:
        label = "all four controls"

    if not rules:
        return _clarify("I couldn't match that to a control. Try 'what does the blueprint require for BitLocker?'")

    lines = [f"The blueprint requires the following for {label}:"]
    for r in rules:
        op = {"eq": "must equal", "gte": "must be at least", "lte": "must be at most"}.get(r.operator, r.operator)
        lines.append(f"• {r.field} {op} {r.expected} — [{r.severity}] {r.description}")

    sources = [ChatSource(kind="blueprint", label="blueprint_rules (assurance baseline)")]
    if control in ("firewall", "bitlocker"):
        sources.append(ChatSource(kind="blueprint",
                                  label=f"{label} golden-image baseline ({control}_blueprint.csv)"))
    # The written policy doc only covers AV/EDR — cite it only for those.
    if control in ("antivirus", "edr", None):
        sources.append(ChatSource(kind="policy", label="EdrAv-policy.txt (AV/EDR control policies)"))
        retrieved = retrieve_policy_context(msg, collection_key="master_policies", top_k=2)
        for d in retrieved:
            sources.append(ChatSource(kind="policy", label=d["source"]))

    return ChatResponse(status="ok", answer_type="policy", message="\n".join(lines),
                        sources=_dedupe(sources),
                        data={"rules": [r.model_dump() for r in rules]})


# --------------------------------------------------------------------------- #
# 5. Grounded explanation (RAG over policies + CIS, phrased by the LLM)
# --------------------------------------------------------------------------- #
_EXPLAIN_SYSTEM = """You are a security assurance assistant. Answer the user's \
question USING ONLY the provided policy and standard excerpts. Cite the source \
filename for each claim in square brackets, e.g. [EdrAv-policy.txt]. If the \
excerpts do not cover the question, say you don't have that in the available \
policies — do not invent an answer. Be concise."""


def _handle_explanation(db: Session, msg: str) -> ChatResponse:
    # Our own policies first (most operationally relevant), then the CIS standard.
    retrieved = (
        retrieve_policy_context(msg, collection_key="master_policies", top_k=3)
        + retrieve_policy_context(msg, collection_key="standards", top_k=3)
    )
    if not retrieved:
        return ChatResponse(status="ok", answer_type="explanation", sources=[],
                            message="")  # empty -> router falls through to clarify

    sources = _dedupe([ChatSource(kind=("standard" if d["source"].startswith("cis") else "policy"),
                                  label=d["source"]) for d in retrieved])
    excerpts = "\n\n".join(f"[{d['source']}] {d['text']}" for d in retrieved)

    if settings.AI_ENABLED and is_ollama_up():
        try:
            text = call_ollama(
                model=settings.EXPLANATION_MODEL,
                system=_EXPLAIN_SYSTEM,
                prompt=f"Question: {msg}\n\nExcerpts:\n{excerpts}\n\nAnswer:",
                temperature=0.2,
            )
            return ChatResponse(status="ok", answer_type="explanation", message=text.strip(),
                                sources=sources, ai_available=True)
        except OllamaUnavailable:
            pass

    # Deterministic fallback: present the grounding excerpts directly.
    body = "Based on the available policies and standards:\n\n" + "\n\n".join(
        f"[{d['source']}] {d['text']}" for d in retrieved[:3])
    return ChatResponse(status="ok", answer_type="explanation", message=body,
                        sources=sources, ai_available=False)


def _dedupe(sources: list[ChatSource]) -> list[ChatSource]:
    seen: set[tuple[str, str]] = set()
    out: list[ChatSource] = []
    for s in sources:
        key = (s.kind, s.label)
        if key not in seen:
            seen.add(key)
            out.append(s)
    return out
