/**
 * The 10-domain security control blueprint.
 *
 * Static reference content: this is the enterprise control catalogue the
 * platform is being built out against. Wording is kept verbatim from the
 * blueprint so this page stays the single source of truth for it.
 *
 * `validatedBy` marks the controls this platform already validates end-to-end
 * today; everything else is on the roadmap. Nothing here touches the
 * compliance engine — it is a catalogue, not a rule set.
 */

import {
  Cloud,
  Code2,
  Database,
  FileLock2,
  KeyRound,
  Laptop,
  Network,
  ScrollText,
  Server,
  Siren,
  type LucideIcon,
} from "lucide-react";
import type { ControlType } from "@/types/api";

export interface DomainControl {
  name: string;
  /** Set when this platform already collects and validates evidence for it. */
  validatedBy?: ControlType;
}

export interface SecurityDomain {
  id: number;
  slug: string;
  name: string;
  objective: string;
  icon: LucideIcon;
  accent: AccentKey;
  controls: DomainControl[];
}

export type AccentKey =
  | "indigo"
  | "emerald"
  | "sky"
  | "violet"
  | "orange"
  | "amber"
  | "rose"
  | "cyan"
  | "teal"
  | "blue";

/** Static class strings so Tailwind keeps them in the build. */
export const ACCENTS: Record<AccentKey, { text: string; bg: string; ring: string; bar: string }> = {
  indigo: { text: "text-indigo-600 dark:text-indigo-400", bg: "bg-indigo-500/10", ring: "ring-indigo-500/30", bar: "bg-indigo-500" },
  emerald: { text: "text-emerald-600 dark:text-emerald-400", bg: "bg-emerald-500/10", ring: "ring-emerald-500/30", bar: "bg-emerald-500" },
  sky: { text: "text-sky-600 dark:text-sky-400", bg: "bg-sky-500/10", ring: "ring-sky-500/30", bar: "bg-sky-500" },
  violet: { text: "text-violet-600 dark:text-violet-400", bg: "bg-violet-500/10", ring: "ring-violet-500/30", bar: "bg-violet-500" },
  orange: { text: "text-orange-600 dark:text-orange-400", bg: "bg-orange-500/10", ring: "ring-orange-500/30", bar: "bg-orange-500" },
  amber: { text: "text-amber-600 dark:text-amber-400", bg: "bg-amber-500/10", ring: "ring-amber-500/30", bar: "bg-amber-500" },
  rose: { text: "text-rose-600 dark:text-rose-400", bg: "bg-rose-500/10", ring: "ring-rose-500/30", bar: "bg-rose-500" },
  cyan: { text: "text-cyan-600 dark:text-cyan-400", bg: "bg-cyan-500/10", ring: "ring-cyan-500/30", bar: "bg-cyan-500" },
  teal: { text: "text-teal-600 dark:text-teal-400", bg: "bg-teal-500/10", ring: "ring-teal-500/30", bar: "bg-teal-500" },
  blue: { text: "text-blue-600 dark:text-blue-400", bg: "bg-blue-500/10", ring: "ring-blue-500/30", bar: "bg-blue-500" },
};

export const SECURITY_DOMAINS: SecurityDomain[] = [
  {
    id: 1,
    slug: "iam",
    name: "Identity & Access Management (IAM)",
    objective: "Ensure only authorized users have appropriate access.",
    icon: KeyRound,
    accent: "indigo",
    controls: [
      { name: "User provisioning & deprovisioning" },
      { name: "Multi-Factor Authentication (MFA)" },
      { name: "Password Policy" },
      { name: "Privileged Access Management (PAM)" },
      { name: "Least Privilege" },
      { name: "Periodic Access Review" },
    ],
  },
  {
    id: 2,
    slug: "network",
    name: "Network Security",
    objective: "Protect network infrastructure and communications.",
    icon: Network,
    accent: "emerald",
    controls: [
      { name: "Firewalls" },
      { name: "Network Segmentation" },
      { name: "VPN Security" },
      { name: "IDS/IPS" },
      { name: "Secure Network Configuration" },
      { name: "Secure Remote Access" },
    ],
  },
  {
    id: 3,
    slug: "endpoint",
    name: "Endpoint Security",
    objective: "Protect workstations, laptops, and servers.",
    icon: Laptop,
    accent: "sky",
    controls: [
      { name: "Endpoint Detection & Response (EDR)", validatedBy: "edr" },
      { name: "Anti-Malware", validatedBy: "antivirus" },
      { name: "Host Firewall" },
      { name: "Disk Encryption", validatedBy: "bitlocker" },
      { name: "Patch Management" },
      { name: "Device Control" },
    ],
  },
  {
    id: 4,
    slug: "server-os",
    name: "Server & Operating System Security",
    objective: "Secure operating systems and server configurations.",
    icon: Server,
    accent: "violet",
    controls: [
      { name: "Secure Configuration (Hardening)" },
      { name: "Patch Management" },
      { name: "Audit Logging" },
      { name: "Account Management" },
      { name: "File Integrity" },
      { name: "Service Configuration" },
    ],
  },
  {
    id: 5,
    slug: "application",
    name: "Application Security",
    objective: "Protect applications throughout their lifecycle.",
    icon: Code2,
    accent: "orange",
    controls: [
      { name: "Secure SDLC" },
      { name: "Authentication & Authorization" },
      { name: "Input Validation" },
      { name: "Secure Session Management" },
      { name: "API Security" },
      { name: "Vulnerability Management" },
    ],
  },
  {
    id: 6,
    slug: "database",
    name: "Database Security",
    objective: "Protect sensitive data stored in databases.",
    icon: Database,
    accent: "amber",
    controls: [
      { name: "Database Access Control" },
      { name: "Transparent Data Encryption (TDE)" },
      { name: "Database Activity Monitoring (DAM)" },
      { name: "Auditing" },
      { name: "Backup Protection" },
      { name: "Database Hardening" },
    ],
  },
  {
    id: 7,
    slug: "data",
    name: "Data Security",
    objective: "Protect data throughout its lifecycle.",
    icon: FileLock2,
    accent: "rose",
    controls: [
      { name: "Data Classification" },
      { name: "Encryption at Rest" },
      { name: "Encryption in Transit" },
      { name: "Data Loss Prevention (DLP)", validatedBy: "dlp" },
      { name: "Key Management" },
      { name: "Backup & Recovery" },
    ],
  },
  {
    id: 8,
    slug: "cloud",
    name: "Cloud Security",
    objective: "Secure cloud services and cloud-hosted assets.",
    icon: Cloud,
    accent: "cyan",
    controls: [
      { name: "Cloud IAM" },
      { name: "Secure Configuration" },
      { name: "Storage Security" },
      { name: "Logging & Monitoring" },
      { name: "CSPM (Cloud Security Posture Management)" },
      { name: "Encryption" },
    ],
  },
  {
    id: 9,
    slug: "monitoring",
    name: "Security Monitoring & Incident Response",
    objective: "Detect, investigate, and respond to security events.",
    icon: Siren,
    accent: "teal",
    controls: [
      { name: "SIEM" },
      { name: "Log Management" },
      { name: "Alert Monitoring" },
      { name: "Incident Response Process" },
      { name: "Threat Intelligence" },
    ],
  },
  {
    id: 10,
    slug: "grc",
    name: "Governance, Risk & Compliance (GRC)",
    objective: "Ensure cybersecurity is governed and aligned with requirements.",
    icon: ScrollText,
    accent: "blue",
    controls: [
      { name: "Security Policies" },
      { name: "Risk Assessment" },
      { name: "Compliance Management" },
      { name: "Security Awareness" },
      { name: "Third-Party Risk Management" },
      { name: "Audit Management" },
    ],
  },
];

/** The four questions asked of every control in the blueprint. */
export const VALIDATION_STAGES = [
  {
    step: 1,
    name: "Design Effectiveness",
    question: "Is the control designed to address the identified risk?",
    accent: "sky" as AccentKey,
  },
  {
    step: 2,
    name: "Implementation",
    question: "Has the control been implemented correctly?",
    accent: "emerald" as AccentKey,
  },
  {
    step: 3,
    name: "Operating Effectiveness",
    question: "Is the control functioning consistently and as intended?",
    accent: "violet" as AccentKey,
  },
  {
    step: 4,
    name: "Compliance",
    question: "Does the control comply with policies, standards and regulatory requirements?",
    accent: "orange" as AccentKey,
  },
];

/** NIST-style outcomes the blueprint drives toward. */
export const OUTCOMES = ["Protect", "Detect", "Respond", "Recover"];

export const TOTAL_CONTROLS = SECURITY_DOMAINS.reduce((n, d) => n + d.controls.length, 0);
export const LIVE_CONTROLS = SECURITY_DOMAINS.reduce(
  (n, d) => n + d.controls.filter((c) => c.validatedBy).length,
  0,
);
