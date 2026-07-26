"""
The default assurance baseline (blueprint) for all four controls — the single
canonical source consumed by both the seeder (scripts/seed_blueprint.py) and
the test suite. AV/EDR rules match the original baseline; Firewall/BitLocker
rules are derived from the golden-image reference rows in the *_blueprint.csv
files.

`expected` values are native Python types here; the seeder JSON-encodes them
for storage so bool/int/str round-trip with their real type.
"""

DEFAULT_RULES: list[dict] = [
    # --- Antivirus ---
    dict(control_type="antivirus", field="av_installed", operator="eq", expected=True,
         severity="critical", description="Antivirus must be installed."),
    dict(control_type="antivirus", field="av_version", operator="gte", expected="4.18.24050.7",
         severity="medium", description="Antivirus version must be at least 4.18.24050.7."),
    dict(control_type="antivirus", field="av_realtime_protection", operator="eq", expected=True,
         severity="critical", description="AV real-time protection must be enabled."),
    dict(control_type="antivirus", field="av_tamper_protection", operator="eq", expected=True,
         severity="high", description="AV tamper protection must be enabled."),
    dict(control_type="antivirus", field="av_policy", operator="eq", expected="Standard_Workstation_Policy",
         severity="medium", description="AV policy must be set to 'Standard_Workstation_Policy'."),
    dict(control_type="antivirus", field="av_signature_age_days", operator="lte", expected=7,
         severity="high", description="AV signatures must be updated within 7 days."),
    # --- EDR ---
    dict(control_type="edr", field="edr_sensor_installed", operator="eq", expected=True,
         severity="critical", description="EDR sensor must be installed."),
    dict(control_type="edr", field="edr_sensor_version", operator="gte", expected="6.55.18203",
         severity="medium", description="EDR sensor version must be at least 6.55.18203."),
    dict(control_type="edr", field="edr_protection_status", operator="eq", expected="Healthy",
         severity="critical", description="EDR sensor must report a healthy protection status."),
    dict(control_type="edr", field="edr_isolation_status", operator="eq", expected="Not Isolated",
         severity="high", description="EDR sensor must not be isolated."),
    dict(control_type="edr", field="edr_policy", operator="eq", expected="EDR_Production_v2",
         severity="medium", description="EDR policy must be set to 'EDR_Production_v2'."),
    dict(control_type="edr", field="edr_last_checkin_hours", operator="lte", expected=24,
         severity="medium", description="EDR agent must check in at least every 24 hours."),
#     # --- Firewall (golden image: all profiles Enabled, default inbound Block) ---
#     dict(control_type="firewall", field="fw_domain_profile", operator="eq", expected="Enabled",
#          severity="high", description="Firewall Domain profile must be enabled."),
#     dict(control_type="firewall", field="fw_private_profile", operator="eq", expected="Enabled",
#          severity="high", description="Firewall Private profile must be enabled."),
#     dict(control_type="firewall", field="fw_public_profile", operator="eq", expected="Enabled",
#          severity="high", description="Firewall Public profile must be enabled."),
#     dict(control_type="firewall", field="fw_default_inbound_action", operator="eq", expected="Block",
#          severity="high", description="Firewall default inbound action must be 'Block'."),
    # --- BitLocker (golden image: XtsAes256 / On / 100% / FullyEncrypted / encrypted) ---
    dict(control_type="bitlocker", field="bl_is_encrypted", operator="eq", expected=True,
         severity="critical", description="System volume must be encrypted with BitLocker."),
    dict(control_type="bitlocker", field="bl_protection_status", operator="eq", expected="On",
         severity="high", description="BitLocker protection status must be 'On'."),
    dict(control_type="bitlocker", field="bl_percentage_encrypted", operator="gte", expected=100,
         severity="high", description="BitLocker volume must be 100% encrypted."),
    dict(control_type="bitlocker", field="bl_volume_status", operator="eq", expected="FullyEncrypted",
         severity="high", description="BitLocker volume status must be 'FullyEncrypted'."),
    dict(control_type="bitlocker", field="bl_encryption_method", operator="eq", expected="XtsAes256",
         severity="medium", description="BitLocker must use the XtsAes256 encryption method."),
    # --- DLP (golden image: DLP_Agent=Running) ---
    dict(control_type="dlp", field="dlp_agent_status", operator="eq", expected="Running",
     severity="critical", description="DLP agent must be running."),
    dict(control_type="dlp", field="dlp_data_classification", operator="eq", expected="Restricted",
          severity="high", description="DLP data classification must be set to 'Restricted'."),
    dict(control_type="dlp", field="dlp_channel", operator="eq", expected="Authorized",
          severity="medium", description="DLP communication channel must be 'Authorized'."),
]
