import { Shield, ShieldAlert, Flame, Lock } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { ControlType, Severity, ValidationStatus } from "@/types/api";

interface StatusMeta {
  label: string;
  /** Tailwind classes for a solid badge. */
  badge: string;
  /** Bare text color class. */
  text: string;
  /** Fill color for charts (CSS var reference). */
  color: string;
  dot: string;
}

export const STATUS_META: Record<ValidationStatus, StatusMeta> = {
  PASS: {
    label: "Pass",
    badge: "bg-pass/15 text-pass border border-pass/30",
    text: "text-pass",
    color: "hsl(var(--pass))",
    dot: "bg-pass",
  },
  WARNING: {
    label: "Warning",
    badge: "bg-warning/15 text-warning border border-warning/30",
    text: "text-warning",
    color: "hsl(var(--warning))",
    dot: "bg-warning",
  },
  FAIL: {
    label: "Fail",
    badge: "bg-fail/15 text-fail border border-fail/30",
    text: "text-fail",
    color: "hsl(var(--fail))",
    dot: "bg-fail",
  },
  NO_DATA: {
    label: "No Data",
    badge: "bg-nodata/15 text-nodata border border-nodata/30",
    text: "text-nodata",
    color: "hsl(var(--nodata))",
    dot: "bg-nodata",
  },
};

interface SeverityMeta {
  label: string;
  badge: string;
  color: string;
}

export const SEVERITY_META: Record<Severity, SeverityMeta> = {
  critical: { label: "Critical", badge: "bg-critical/15 text-critical border border-critical/30", color: "hsl(var(--critical))" },
  high: { label: "High", badge: "bg-high/15 text-high border border-high/30", color: "hsl(var(--high))" },
  medium: { label: "Medium", badge: "bg-medium/15 text-medium border border-medium/30", color: "hsl(var(--medium))" },
  low: { label: "Low", badge: "bg-low/15 text-low border border-low/30", color: "hsl(var(--low))" },
};

export const CONTROL_META: Record<ControlType, { label: string; short: string; icon: LucideIcon }> = {
  antivirus: { label: "Antivirus", short: "AV", icon: Shield },
  edr: { label: "Endpoint Detection & Response", short: "EDR", icon: ShieldAlert },
  firewall: { label: "Firewall", short: "FW", icon: Flame },
  bitlocker: { label: "BitLocker Encryption", short: "BitLocker", icon: Lock },
};

export const CONTROL_ORDER: ControlType[] = ["antivirus", "edr", "firewall", "bitlocker"];
export const SEVERITY_ORDER: Severity[] = ["critical", "high", "medium", "low"];

/** Human labels for the sometimes-cryptic evidence field names. */
export const FIELD_LABELS: Record<string, string> = {
  av_installed: "Installed",
  av_version: "Version",
  av_engine_version: "Engine Version",
  av_signature_version: "Signature Version",
  av_realtime_protection: "Real-Time Protection",
  av_tamper_protection: "Tamper Protection",
  av_policy: "Policy",
  av_signature_age_days: "Signature Age (days)",
  av_last_heartbeat_hours: "Last Heartbeat (hours)",
  edr_sensor_installed: "Sensor Installed",
  edr_sensor_version: "Sensor Version",
  edr_protection_status: "Protection Status",
  edr_isolation_status: "Isolation Status",
  edr_policy: "Policy",
  edr_last_checkin_hours: "Last Check-in (hours)",
  edr_detection_count: "Detection Count",
  fw_domain_profile: "Domain Profile",
  fw_private_profile: "Private Profile",
  fw_public_profile: "Public Profile",
  fw_default_inbound_action: "Default Inbound Action",
  bl_encryption_method: "Encryption Method",
  bl_protection_status: "Protection Status",
  bl_percentage_encrypted: "Percentage Encrypted",
  bl_volume_status: "Volume Status",
  bl_is_encrypted: "Encrypted",
  bl_compliance_state: "Compliance State",
};

export function fieldLabel(field: string): string {
  return FIELD_LABELS[field] ?? field.replace(/_/g, " ");
}

/** Evidence fields to display per control on the endpoint-detail view. */
export const EVIDENCE_FIELDS: Record<ControlType, string[]> = {
  antivirus: [
    "av_installed",
    "av_version",
    "av_realtime_protection",
    "av_tamper_protection",
    "av_policy",
    "av_signature_age_days",
  ],
  edr: [
    "edr_sensor_installed",
    "edr_sensor_version",
    "edr_protection_status",
    "edr_isolation_status",
    "edr_policy",
    "edr_last_checkin_hours",
    "edr_detection_count",
  ],
  firewall: [
    "fw_domain_profile",
    "fw_private_profile",
    "fw_public_profile",
    "fw_default_inbound_action",
  ],
  bitlocker: [
    "bl_is_encrypted",
    "bl_protection_status",
    "bl_percentage_encrypted",
    "bl_volume_status",
    "bl_encryption_method",
  ],
};

/** Presents an evidence value for display (booleans, nulls, numbers). */
export function formatEvidenceValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value);
}
