# MASTER PROMPT FOR CLAUDE AGENT

This document defines the complete implementation requirements for the AI-Powered Endpoint Assurance Validation project.

## Goal
Build a production-ready web application using:
- React + Vite + TypeScript + Tailwind + shadcn/ui
- FastAPI + SQLAlchemy + Pydantic
- SQLite
- JWT Authentication
- ReportLab + OpenPyXL

## Core Modules
1. Login
2. Dashboard
3. Endpoints
4. Endpoint Details
5. AI Chat
6. Reports

## Validation Controls
- Antivirus
- EDR
- Firewall
- BitLocker

Each control returns PASS / WARNING / FAIL.

## Databases
1. Asset Inventory
2. Endpoint Security
3. Compliance
Unified using endpoint_id.

## AI Requirements
- Search SQLite first.
- Never hallucinate.
- Explain findings.
- Explain recommendations.
- Reference CIS controls where applicable.
- Explain severity and compliance score.

## Development Phases
1. Read and understand the entire repository.
2. Backend foundation.
3. Frontend foundation.
4. Dashboard.
5. Endpoint pages.
6. Validation engine.
7. Compliance engine.
8. AI chat.
9. Reports.
10. Testing and verification.

## Testing
Do not declare the project complete until all APIs, UI, database integration, AI responses, reports, authentication, routing, and validation rules are tested and verified.

## Engineering Standards
Use SOLID, DRY, KISS, Clean Architecture, reusable components, service layer, repository pattern, proper logging, validation, and production-ready code.