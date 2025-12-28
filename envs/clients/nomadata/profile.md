# Nomadata Client Profile

## Identity
- Client code / slug: nomadata
- Display name: Nomadata Labs (Demo Sandbox)
- Internal owner: Aaron LaPorte
- Primary business contact: demo@nomadata.com / +1-555-0101
- Technical contact: platform@nomadata.com
- Time zone / schedule: US/Eastern, daily 5 a.m.
- Priority / SLA: Sandbox (non-prod)

## Environment Variables
- DATABASE_URL: sqlite:///data/demo.sqlite
- EXPORT_ROOT: exports
- REPORT_ROOT: reports
- LOG_LEVEL: DEBUG
- TZ: UTC
- Extra vars: none

## Access Control
- VPN/bastion: not required (local demo DB)
- IP allow-list: n/a
- Credential rotation: refresh demo seed monthly
- Compliance: internal demo data only

## Scheduling & Jobs
- Schedule windows: 5 a.m. daily wrapper (envs/schedules/5am/nomadata.env)
- Job IDs: sample_orders, tech_summary_analysis, tech_risk_snapshot
- Recovery: rerun via dotenv run --dotenv-path envs/clients/nomadata.env python runner.py --only <job>

## Distribution & Notifications
- Delivery: local exports + archive zip
- Email/Slack: not enabled (demo)
- Retention: keep latest outputs, archive zipped snapshots

## Notes
- Seed datasets via scripts/seed_demo_data.py and scripts/seed_demo_tech_risk.py
- Acts as pre-release regression client
