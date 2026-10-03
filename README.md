# 🛡️ AEGIS — Agentic AI-Powered Security Monitoring & Risk Identification

> An intelligent security monitoring system that detects suspicious data-access behavior, investigates security alerts using specialized AI agents and contextual knowledge, and automates security reporting and response workflows.

---

## 📌 Overview

**AEGIS** is an Agentic AI-powered security monitoring and risk-identification system designed to identify suspicious data-access activity and assist security teams in investigating and responding to potential security risks.

Modern organizations generate large volumes of access activity across users, datasets, devices, locations, and sessions. Most events are legitimate, but a small percentage may indicate suspicious behavior such as:

- Excessive or bulk data access
- Access during unusual hours
- Repeated failed access attempts
- Access from unfamiliar locations
- Access from unfamiliar devices

AEGIS combines **machine learning, behavioral detection, Retrieval-Augmented Generation (RAG), specialized AI agents, PostgreSQL, Streamlit, and n8n automation** into a single security workflow.

The system follows the overall lifecycle:

```text
Access Data
     ↓
Feature Engineering
     ↓
Anomaly Detection
     ↓
Security Alerts
     ↓
RAG Knowledge Retrieval
     ↓
AI Investigation
     ↓
Risk Assessment
     ↓
PostgreSQL
     ↓
n8n Automation
     ↓
Excel + Email Reporting
