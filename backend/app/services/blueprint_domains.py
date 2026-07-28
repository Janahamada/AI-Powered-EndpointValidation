"""
The 10-domain security control blueprint — reporting copy.

Static reference content used only by the PDF appendix. It deliberately does
not touch the compliance engine: these are catalogue entries, not rules, and
nothing here is ever evaluated against an endpoint.

NOTE: this catalogue is mirrored in the UI at
`frontend/src/features/security-blueprint/blueprint-domains.ts`. The two are
presentation copies of the same fixed reference material — if one is edited,
update the other so the page and the report agree.

`validated_by` names the platform control that already validates the entry,
mapping the catalogue onto what the engine actually checks today.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DomainControl:
    name: str
    validated_by: str | None = None


@dataclass(frozen=True)
class SecurityDomain:
    id: int
    name: str
    objective: str
    controls: tuple[DomainControl, ...]

    @property
    def live_count(self) -> int:
        return sum(1 for c in self.controls if c.validated_by)

    @property
    def coverage(self) -> float:
        return round(self.live_count / len(self.controls) * 100.0, 1) if self.controls else 0.0


SECURITY_DOMAINS: tuple[SecurityDomain, ...] = (
    SecurityDomain(
        1,
        "Identity & Access Management (IAM)",
        "Ensure only authorized users have appropriate access.",
        (
            DomainControl("User provisioning & deprovisioning"),
            DomainControl("Multi-Factor Authentication (MFA)"),
            DomainControl("Password Policy"),
            DomainControl("Privileged Access Management (PAM)"),
            DomainControl("Least Privilege"),
            DomainControl("Periodic Access Review"),
        ),
    ),
    SecurityDomain(
        2,
        "Network Security",
        "Protect network infrastructure and communications.",
        (
            DomainControl("Firewalls"),
            DomainControl("Network Segmentation"),
            DomainControl("VPN Security"),
            DomainControl("IDS/IPS"),
            DomainControl("Secure Network Configuration"),
            DomainControl("Secure Remote Access"),
        ),
    ),
    SecurityDomain(
        3,
        "Endpoint Security",
        "Protect workstations, laptops, and servers.",
        (
            DomainControl("Endpoint Detection & Response (EDR)", "edr"),
            DomainControl("Anti-Malware", "antivirus"),
            DomainControl("Host Firewall"),
            DomainControl("Disk Encryption", "bitlocker"),
            DomainControl("Patch Management"),
            DomainControl("Device Control"),
        ),
    ),
    SecurityDomain(
        4,
        "Server & Operating System Security",
        "Secure operating systems and server configurations.",
        (
            DomainControl("Secure Configuration (Hardening)"),
            DomainControl("Patch Management"),
            DomainControl("Audit Logging"),
            DomainControl("Account Management"),
            DomainControl("File Integrity"),
            DomainControl("Service Configuration"),
        ),
    ),
    SecurityDomain(
        5,
        "Application Security",
        "Protect applications throughout their lifecycle.",
        (
            DomainControl("Secure SDLC"),
            DomainControl("Authentication & Authorization"),
            DomainControl("Input Validation"),
            DomainControl("Secure Session Management"),
            DomainControl("API Security"),
            DomainControl("Vulnerability Management"),
        ),
    ),
    SecurityDomain(
        6,
        "Database Security",
        "Protect sensitive data stored in databases.",
        (
            DomainControl("Database Access Control"),
            DomainControl("Transparent Data Encryption (TDE)"),
            DomainControl("Database Activity Monitoring (DAM)"),
            DomainControl("Auditing"),
            DomainControl("Backup Protection"),
            DomainControl("Database Hardening"),
        ),
    ),
    SecurityDomain(
        7,
        "Data Security",
        "Protect data throughout its lifecycle.",
        (
            DomainControl("Data Classification"),
            DomainControl("Encryption at Rest"),
            DomainControl("Encryption in Transit"),
            DomainControl("Data Loss Prevention (DLP)", "dlp"),
            DomainControl("Key Management"),
            DomainControl("Backup & Recovery"),
        ),
    ),
    SecurityDomain(
        8,
        "Cloud Security",
        "Secure cloud services and cloud-hosted assets.",
        (
            DomainControl("Cloud IAM"),
            DomainControl("Secure Configuration"),
            DomainControl("Storage Security"),
            DomainControl("Logging & Monitoring"),
            DomainControl("CSPM (Cloud Security Posture Management)"),
            DomainControl("Encryption"),
        ),
    ),
    SecurityDomain(
        9,
        "Security Monitoring & Incident Response",
        "Detect, investigate, and respond to security events.",
        (
            DomainControl("SIEM"),
            DomainControl("Log Management"),
            DomainControl("Alert Monitoring"),
            DomainControl("Incident Response Process"),
            DomainControl("Threat Intelligence"),
        ),
    ),
    SecurityDomain(
        10,
        "Governance, Risk & Compliance (GRC)",
        "Ensure cybersecurity is governed and aligned with requirements.",
        (
            DomainControl("Security Policies"),
            DomainControl("Risk Assessment"),
            DomainControl("Compliance Management"),
            DomainControl("Security Awareness"),
            DomainControl("Third-Party Risk Management"),
            DomainControl("Audit Management"),
        ),
    ),
)

#: Display names for the platform controls referenced by `validated_by`.
CONTROL_LABELS = {
    "antivirus": "Antivirus",
    "edr": "EDR",
    "bitlocker": "BitLocker",
    "dlp": "DLP",
}

TOTAL_CONTROLS = sum(len(d.controls) for d in SECURITY_DOMAINS)
LIVE_CONTROLS = sum(d.live_count for d in SECURITY_DOMAINS)
OVERALL_COVERAGE = round(LIVE_CONTROLS / TOTAL_CONTROLS * 100.0, 1)

VALIDATION_STAGES = (
    ("1. Design Effectiveness", "Is the control designed to address the identified risk?"),
    ("2. Implementation", "Has the control been implemented correctly?"),
    ("3. Operating Effectiveness", "Is the control functioning consistently and as intended?"),
    (
        "4. Compliance",
        "Does the control comply with policies, standards and regulatory requirements?",
    ),
)
