# Operational SLA & Incident Response Timelines
Category: Operations
Author: Site Reliability Engineering (SRE)
Published: 2025-03-15

## 1. Service Level Objectives (SLO)
Production services maintain a target availability SLO of 99.9% uptime. System response latency for P99 API requests must remain under 200 milliseconds during peak traffic conditions.

## 2. SLA Incident Response Timeline & Resolution Thresholds
- **Priority 1 (Critical Outage):** Initial response within 15 minutes; Resolution target within 4 hours.
- **Priority 2 (High Impact):** Initial response within 1 hour; Resolution target within 24 hours.
- **Priority 3 (Medium Impact):** Initial response within 4 hours; Resolution target within 72 hours.
- **Priority 4 (Low Impact):** Initial response within 24 hours; Resolution target within 168 hours (7 days).

## 3. Post-Incident Root Cause Analysis (RCA)
A mandatory blameless Post-Mortem RCA document must be published within 48 hours for all P1 and P2 production incidents.
