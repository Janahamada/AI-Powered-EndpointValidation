"""
Remediation knowledge base — the deterministic, curated grounding for every
recommendation.

Each entry is keyed by the blueprint field it remediates and is anchored in OUR
own controls and blueprints:
  - `policy`  : the internal control policy / golden-image baseline that the
                rule enforces (AV-0x / EDR-0x from the EDR/AV policy; the
                Firewall Policy-FW-01 golden image; the BitLocker encryption
                baseline). This is the primary reference.
  - `cis`     : a CIS Safeguard cited as a SUPPORTING external standard, mapped
                accurately (not fuzzy-matched). Optional.
  - `action`  : the remediation headline.
  - `why`     : control-specific rationale (severity justification is added
                generically by the service).
  - `steps`   : concrete, operational remediation steps.

There is intentionally no LLM here: a recommendation can never cite a control
number or policy that isn't in this table.
"""

# CIS Safeguards actually present in policies/standards/cis_controls_v8_1_2.md.
_CIS = {
    "10.1": ("10.1", "Deploy and Maintain Anti-Malware Software", "Devices / Detect"),
    "10.2": ("10.2", "Configure Automatic Anti-Malware Signature Updates", "Devices / Protect"),
    "10.6": ("10.6", "Centrally Manage Anti-Malware Software", "Devices / Protect"),
    "10.7": ("10.7", "Use Behavior-Based Anti-Malware Software", "Devices / Detect"),
    "13.2": ("13.2", "Deploy a Host-Based Intrusion Detection Solution", "Devices / Detect"),
    "13.7": ("13.7", "Deploy a Host-Based Intrusion Prevention Solution", "Devices / Protect"),
    "4.5": ("4.5", "Implement and Manage a Firewall on End-User Devices", "Devices / Protect"),
    "4.4": ("4.4", "Implement and Manage a Firewall on Servers", "Devices / Protect"),
    "3.6": ("3.6", "Encrypt Data on End-User Devices", "Data / Protect"),
    "3.11": ("3.11", "Encrypt Sensitive Data at Rest", "Data / Protect"),
}

# field -> remediation entry
KB: dict[str, dict] = {
    # ---------------------------- Antivirus ----------------------------
    "av_installed": {
        "action": "Deploy the managed antivirus agent on this endpoint",
        "policy": "Antivirus blueprint — antivirus must be installed",
        "cis": "10.1",
        "why": "With no antivirus agent present the endpoint has no malware "
        "prevention or detection at all, so malicious files can execute unimpeded.",
        "steps": [
            "Push the approved antivirus package to the endpoint via the management console.",
            "Confirm the agent registers and reports an 'Installed' status.",
            "Verify real-time protection and the standard workstation policy are applied.",
        ],
    },
    "av_realtime_protection": {
        "action": "Enable antivirus real-time protection",
        "policy": "Antivirus blueprint — real-time protection must be enabled",
        "cis": "10.7",
        "why": "Real-time (behaviour-based) scanning is the primary preventive layer; "
        "with it off, threats are only caught on a scheduled scan — long after execution.",
        "steps": [
            "Re-enable real-time protection in the endpoint's antivirus policy.",
            "Confirm no local override or exclusion is disabling it.",
            "Validate the change reflects in the console within one heartbeat.",
        ],
    },
    "av_tamper_protection": {
        "action": "Enable antivirus tamper protection",
        "policy": "Policy AV-03 (Tamper Protection) — must remain enabled",
        "cis": "10.6",
        "why": "Tamper protection stops malware (and unauthorized users) from disabling "
        "the agent; without it, an attacker can silently neutralise antivirus before acting.",
        "steps": [
            "Turn on tamper protection in the managed antivirus policy.",
            "Ensure only the security team can modify agent settings.",
            "Treat any disablement outside an approved maintenance window as a critical violation.",
        ],
    },
    "av_signature_age_days": {
        "action": "Update antivirus signatures to within the 7-day threshold",
        "policy": "Policy AV-01 (Signature Freshness) — updated within 7 days",
        "cis": "10.2",
        "why": "Stale signatures miss recently-published malware. The blueprint requires "
        "signatures no older than 7 days; beyond that the endpoint is blind to new threats.",
        "steps": [
            "Trigger a manual signature update on the endpoint.",
            "Confirm automatic signature updates are enabled and reaching the endpoint.",
            "Remediate within one business day of detection per Policy AV-01.",
        ],
    },
    "av_version": {
        "action": "Upgrade the antivirus agent to an approved supported version",
        "policy": "Policy AV-04 (Agent Version) — approved vendor-supported version",
        "cis": "10.1",
        "why": "Unsupported or end-of-life agent versions miss engine fixes and new "
        "detection capabilities, weakening protection over time.",
        "steps": [
            "Schedule an upgrade to the approved minimum agent version or later.",
            "Validate the upgrade completes and the agent still reports healthy.",
            "Remediate within 5 business days of detection per Policy AV-04.",
        ],
    },
    "av_policy": {
        "action": "Apply the approved standard antivirus policy",
        "policy": "Policy AV-05 (Agent Policy) — approved standard workstation policy",
        "cis": "10.6",
        "why": "A non-standard policy can silently weaken protection or disable required "
        "controls; centrally-managed configuration keeps every endpoint at the approved baseline.",
        "steps": [
            "Reassign the endpoint to the approved standard workstation policy.",
            "Investigate why it drifted (manual change, wrong group, stale assignment).",
            "Remediate within one business day per Policy AV-05.",
        ],
    },
    # ------------------------------- EDR -------------------------------
    "edr_sensor_installed": {
        "action": "Deploy the EDR sensor on this endpoint",
        "policy": "EDR blueprint — EDR sensor must be installed",
        "cis": "13.7",
        "why": "Without an EDR sensor there is no host-based intrusion detection/response "
        "telemetry — threats that evade antivirus go completely unseen.",
        "steps": [
            "Deploy the approved EDR sensor package to the endpoint.",
            "Confirm the sensor registers with the management console and reports healthy.",
            "Apply the approved EDR production configuration baseline.",
        ],
    },
    "edr_protection_status": {
        "action": "Investigate and restore EDR sensor health",
        "policy": "Policy EDR-03 (Sensor Health Status) — must report Healthy",
        "cis": "13.2",
        "why": "An 'Unhealthy' sensor is running but not functioning correctly (driver "
        "failure, corrupted config); it provides none of the protection an 'installed' "
        "status implies.",
        "steps": [
            "Investigate the sensor within one business day per Policy EDR-03.",
            "Restart the sensor service and check for driver/configuration errors.",
            "Confirm the sensor returns to a Healthy status in the console.",
        ],
    },
    "edr_isolation_status": {
        "action": "Confirm and clear unexpected network isolation",
        "policy": "EDR blueprint — sensor must not be isolated (Not Isolated)",
        "cis": "13.7",
        "why": "An isolated sensor is cut off from the network, usually as active "
        "containment. If the isolation is not part of an approved incident response, "
        "the endpoint is offline and unprotected in normal operations.",
        "steps": [
            "Verify whether the isolation is an intentional incident-response action.",
            "If not, release the endpoint from isolation in the console.",
            "Document any legitimate containment against the related incident.",
        ],
    },
    "edr_last_checkin_hours": {
        "action": "Restore EDR agent check-in to within 24 hours",
        "policy": "Policy EDR-02 (Agent Check-In Frequency) — at least every 24h",
        "cis": "13.7",
        "why": "An agent that misses its check-in window may be powered off, network-"
        "blocked, or compromised; stale telemetry means real-time detection is not working.",
        "steps": [
            "Check the endpoint's connectivity to the EDR management console.",
            "Restart the sensor service and force a check-in.",
            "If it misses two consecutive windows and stays unresponsive, isolate it per Policy EDR-02.",
        ],
    },
    "edr_sensor_version": {
        "action": "Upgrade the EDR sensor to an approved supported version",
        "policy": "Policy EDR-04 (Sensor Version) — within vendor support lifecycle",
        "cis": "13.7",
        "why": "Outdated sensor versions lack current detections and fixes, reducing "
        "the endpoint's detection and response coverage.",
        "steps": [
            "Schedule an upgrade to the approved minimum sensor version or later.",
            "Confirm the sensor reports healthy after upgrade.",
            "Remediate within 5 business days of detection per Policy EDR-04.",
        ],
    },
    "edr_policy": {
        "action": "Apply the approved EDR configuration baseline",
        "policy": "Policy EDR-05 (Sensor Configuration Baseline) — approved baseline",
        "cis": "13.7",
        "why": "A non-standard EDR configuration can weaken protection, disable telemetry, "
        "or prevent proper detection, undermining the whole control.",
        "steps": [
            "Reassign the endpoint to the approved EDR production baseline.",
            "Investigate the cause of the deviation.",
            "Correct within one business day per Policy EDR-05.",
        ],
    },
    # ----------------------------- Firewall ----------------------------
    "fw_domain_profile": {
        "action": "Enable the host firewall Domain profile",
        "policy": "Firewall golden image (Policy-FW-01) — Domain profile Enabled",
        "cis": "4.5",
        "why": "A disabled Domain-profile firewall exposes the endpoint on the corporate "
        "network to unsolicited inbound connections and lateral movement.",
        "steps": [
            "Enable the Domain profile via Group Policy or the host firewall configuration.",
            "Confirm the default-deny inbound posture is retained.",
            "Validate the endpoint matches the Policy-FW-01 golden image.",
        ],
    },
    "fw_private_profile": {
        "action": "Enable the host firewall Private profile",
        "policy": "Firewall golden image (Policy-FW-01) — Private profile Enabled",
        "cis": "4.5",
        "why": "A disabled Private-profile firewall leaves the endpoint exposed on "
        "trusted/home networks, a common path for inbound attacks.",
        "steps": [
            "Enable the Private profile in the host firewall configuration.",
            "Confirm the default-deny inbound posture is retained.",
            "Validate against the Policy-FW-01 golden image.",
        ],
    },
    "fw_public_profile": {
        "action": "Enable the host firewall Public profile",
        "policy": "Firewall golden image (Policy-FW-01) — Public profile Enabled",
        "cis": "4.5",
        "why": "The Public profile applies on untrusted networks; disabling it exposes the "
        "endpoint directly to hostile networks (cafés, airports, hotels).",
        "steps": [
            "Enable the Public profile in the host firewall configuration.",
            "Ensure the default-deny inbound rule remains in force.",
            "Validate against the Policy-FW-01 golden image.",
        ],
    },
    "fw_default_inbound_action": {
        "action": "Set the firewall default inbound action to Block",
        "policy": "Firewall golden image (Policy-FW-01) — default inbound Block",
        "cis": "4.5",
        "why": "A default-allow inbound posture permits any service not explicitly denied; "
        "the required default-deny (Block) drops all inbound traffic except what is allowed.",
        "steps": [
            "Set the default inbound action to Block across all firewall profiles.",
            "Review allowed inbound rules and remove anything unnecessary.",
            "Validate against the Policy-FW-01 golden image.",
        ],
    },
    # ---------------------------- BitLocker ----------------------------
    "bl_is_encrypted": {
        "action": "Enable BitLocker full-disk encryption on the system volume",
        "policy": "BitLocker golden image — system volume must be encrypted",
        "cis": "3.6",
        "why": "An unencrypted volume exposes all data at rest: a lost or stolen device "
        "gives an attacker full access to its contents.",
        "steps": [
            "Enable BitLocker on the system volume and escrow the recovery key.",
            "Use the XtsAes256 method and confirm protection turns On.",
            "Let encryption complete to 100% (FullyEncrypted).",
        ],
    },
    "bl_protection_status": {
        "action": "Turn BitLocker protection On",
        "policy": "BitLocker golden image — protection status must be On",
        "cis": "3.6",
        "why": "'Protection Off' (suspended) means the volume key is exposed and the data "
        "is effectively unprotected even if the disk shows as encrypted.",
        "steps": [
            "Resume BitLocker protection (e.g. `manage-bde -protectors -enable`).",
            "Confirm the protection status reports On.",
            "Investigate why protection was suspended.",
        ],
    },
    "bl_percentage_encrypted": {
        "action": "Complete BitLocker encryption to 100%",
        "policy": "BitLocker golden image — volume must be 100% encrypted",
        "cis": "3.6",
        "why": "A partially-encrypted volume still exposes the unencrypted portion of the "
        "disk to offline data recovery.",
        "steps": [
            "Allow the encryption process to run to completion.",
            "Confirm the volume reaches 100% / FullyEncrypted.",
            "Investigate stalls (power policy, disk errors, interrupted encryption).",
        ],
    },
    "bl_volume_status": {
        "action": "Bring the BitLocker volume to a FullyEncrypted state",
        "policy": "BitLocker golden image — volume status FullyEncrypted",
        "cis": "3.6",
        "why": "Any status other than FullyEncrypted (Unencrypted / EncryptionInProgress) "
        "means data at rest is not fully protected.",
        "steps": [
            "Complete or restart BitLocker encryption on the volume.",
            "Confirm the volume status reports FullyEncrypted.",
            "Verify the recovery key is safely escrowed.",
        ],
    },
    "bl_encryption_method": {
        "action": "Re-encrypt the volume using the XtsAes256 method",
        "policy": "BitLocker golden image — XtsAes256 encryption method",
        "cis": "3.6",
        "why": "Weaker or legacy encryption methods do not meet the approved cryptographic "
        "baseline; XtsAes256 is the required standard for data-at-rest protection.",
        "steps": [
            "Decrypt and re-encrypt the volume using the XtsAes256 method.",
            "Confirm the reported encryption method is XtsAes256.",
            "Update the device's encryption policy to enforce XtsAes256 going forward.",
        ],
    },
}

# Presence gaps raised by the existence-check flow reuse the install entries.
KB["av_present"] = KB["av_installed"]
KB["edr_present"] = KB["edr_sensor_installed"]
KB["fw_present"] = {
    "action": "Collect firewall telemetry / deploy host firewall management",
    "policy": "Firewall golden image (Policy-FW-01)",
    "cis": "4.5",
    "why": "No firewall evidence is on file, so the endpoint's inbound exposure cannot be "
    "assured against the Policy-FW-01 golden image.",
    "steps": [
        "Confirm the host firewall is present and centrally managed.",
        "Onboard the endpoint to firewall telemetry collection.",
        "Validate configuration against the Policy-FW-01 golden image.",
    ],
}
KB["bl_present"] = {
    "action": "Collect BitLocker telemetry / deploy disk encryption management",
    "policy": "BitLocker golden image",
    "cis": "3.6",
    "why": "No BitLocker evidence is on file, so data-at-rest protection cannot be assured "
    "against the encryption baseline.",
    "steps": [
        "Confirm BitLocker is deployed and managed on the endpoint.",
        "Onboard the endpoint to encryption telemetry collection.",
        "Validate against the BitLocker encryption baseline.",
    ],
}


def cis_for(key: str | None):
    return _CIS.get(key) if key else None
