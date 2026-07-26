"""Unit tests for the deterministic validation engine (no DB, no network)."""

import json

import pytest

from app.schemas.control import BlueprintRuleOut, ControlRecord
from app.schemas.common import ValidationStatus
from app.services import chat_service, validation_service
from app.validators.controls import AntivirusValidator, BitlockerValidator


def _rules() -> list[BlueprintRuleOut]:
    from app.services.blueprint_defaults import DEFAULT_RULES

    return [
        BlueprintRuleOut(
            control_type=r["control_type"],
            field=r["field"],
            operator=r["operator"],
            expected=r["expected"],
            severity=r["severity"],
            description=r["description"],
        )
        for r in DEFAULT_RULES
    ]


def _fully_compliant_record() -> ControlRecord:
    return ControlRecord(
        hostname="TEST-OK",
        av_present=True, av_installed=True, av_version="4.18.24050.7",
        av_realtime_protection=True, av_tamper_protection=True,
        av_policy="Standard_Workstation_Policy", av_signature_age_days=1,
        edr_present=True, edr_sensor_installed=True, edr_sensor_version="6.55.18203",
        edr_protection_status="Healthy", edr_isolation_status="Not Isolated",
        edr_policy="EDR_Production_v2", edr_last_checkin_hours=2, edr_detection_count=0,
        fw_present=True, fw_domain_profile="Enabled", fw_private_profile="Enabled",
        fw_public_profile="Enabled", fw_default_inbound_action="Block",
        bl_present=True, bl_encryption_method="XtsAes256", bl_protection_status="On",
        bl_percentage_encrypted=100, bl_volume_status="FullyEncrypted",
        bl_is_encrypted=True, bl_compliance_state="compliant",
    )


def test_fully_compliant_endpoint_passes_all_controls():
    controls = validation_service.validate_controls(_fully_compliant_record(), _rules())
    assert all(c.status == ValidationStatus.PASS.value for c in controls)
    assert validation_service.compliance_score(controls) == 100.0
    assert validation_service.endpoint_status(controls) == ValidationStatus.PASS.value
    assert validation_service.all_findings(controls) == []


def test_critical_finding_fails_control_and_endpoint():
    rec = _fully_compliant_record()
    rec.av_realtime_protection = False  # critical rule
    controls = validation_service.validate_controls(rec, _rules())
    av = next(c for c in controls if c.control_type == "antivirus")
    assert av.status == ValidationStatus.FAIL.value
    assert validation_service.endpoint_status(controls) == ValidationStatus.FAIL.value


def test_medium_finding_only_warns():
    rec = _fully_compliant_record()
    rec.av_policy = "Wrong_Policy"  # medium rule
    controls = validation_service.validate_controls(rec, _rules())
    av = next(c for c in controls if c.control_type == "antivirus")
    assert av.status == ValidationStatus.WARNING.value


def test_missing_control_row_is_no_data():
    rec = _fully_compliant_record()
    rec.bl_present = False
    controls = validation_service.validate_controls(rec, _rules())
    bl = next(c for c in controls if c.control_type == "bitlocker")
    assert bl.status == ValidationStatus.NO_DATA.value
    assert bl.present is False
    assert bl.score == 0.0


def test_existence_field_mapping_uses_installed_flags_for_av_and_edr():
    rec = _fully_compliant_record()
    rec.av_present = True
    rec.av_installed = False
    rec.edr_present = True
    rec.edr_sensor_installed = False

    assert chat_service._control_exists_for_existence_check(rec, "antivirus") is False
    assert chat_service._control_exists_for_existence_check(rec, "edr") is False
    assert chat_service._control_exists_for_existence_check(rec, "firewall") is True
    assert chat_service._control_exists_for_existence_check(rec, "bitlocker") is True


def test_score_is_fraction_of_passing_fields():
    rec = _fully_compliant_record()
    rec.av_policy = "Wrong_Policy"  # 1 of 6 AV rules fails
    controls = validation_service.validate_controls(rec, _rules())
    av = next(c for c in controls if c.control_type == "antivirus")
    assert av.passed_fields == av.total_fields - 1
    assert av.score == pytest.approx(round((av.total_fields - 1) / av.total_fields * 100, 1))


def test_bitlocker_unencrypted_is_critical_fail():
    rec = _fully_compliant_record()
    rec.bl_is_encrypted = False  # critical
    rec.bl_protection_status = "Off"
    rec.bl_percentage_encrypted = 0
    rec.bl_volume_status = "Unencrypted"
    controls = validation_service.validate_controls(rec, _rules())
    bl = next(c for c in controls if c.control_type == "bitlocker")
    assert bl.status == ValidationStatus.FAIL.value
    assert any(f.severity == "critical" for f in bl.findings)
