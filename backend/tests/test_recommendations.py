"""Tests for the deterministic, grounded remediation recommendations."""

from app.schemas.control import Finding
from app.services import remediation_service


def _finding(control_type, field, severity, expected, actual, desc):
    return Finding(
        control_type=control_type,
        field=field,
        severity=severity,
        expected=expected,
        actual=actual,
        description=desc,
    )


def test_recommendation_is_grounded_in_blueprint_policy_and_cis():
    findings = [
        _finding("antivirus", "av_installed", "critical", True, False, "Antivirus must be installed."),
    ]
    recs = remediation_service.build_recommendations(findings)
    assert len(recs) == 1
    r = recs[0]
    assert r.title  # an action headline
    assert r.observed == "No" and r.required == "Yes"
    assert "av_installed" in r.blueprint_rule
    assert r.policy_reference  # OUR control/blueprint reference
    assert r.cis is not None and r.cis.safeguard == "10.1"  # accurate CIS mapping
    assert r.steps  # concrete remediation steps
    assert "CRITICAL" in r.why  # severity justification embedded


def test_recommendations_are_severity_ordered():
    findings = [
        _finding("antivirus", "av_policy", "medium", "P", "Q", "AV policy drift."),
        _finding("bitlocker", "bl_is_encrypted", "critical", True, False, "Not encrypted."),
        _finding("antivirus", "av_tamper_protection", "high", True, False, "Tamper off."),
    ]
    recs = remediation_service.build_recommendations(findings)
    assert [r.severity for r in recs] == ["critical", "high", "medium"]


def test_each_control_maps_to_its_cis_safeguard():
    cases = {
        ("antivirus", "av_signature_age_days"): "10.2",
        ("edr", "edr_sensor_installed"): "13.7",
        ("firewall", "fw_default_inbound_action"): "4.5",
        ("bitlocker", "bl_is_encrypted"): "3.6",
    }
    for (ct, field), expected_cis in cases.items():
        rec = remediation_service.build_recommendations(
            [_finding(ct, field, "high", "x", "y", "d")]
        )[0]
        assert rec.cis is not None
        assert rec.cis.safeguard == expected_cis


def test_render_text_and_empty():
    assert "No remediation required" in remediation_service.render_text("H", [])
    recs = remediation_service.build_recommendations(
        [_finding("firewall", "fw_domain_profile", "high", "Enabled", "Disabled", "FW domain off.")]
    )
    text = remediation_service.render_text("HOST-1", recs)
    assert "Recommendation 1" in text
    assert "CIS Safeguard 4.5" in text
    assert "How" not in text or "•" in text  # steps rendered as bullets
