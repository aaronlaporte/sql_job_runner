# Client Profile Template

Use this template when creating a new client entry inside your internal system. Once the fields are populated, copy only the required values into `envs/clients/<client>.env`.

## Identity
- Client code / slug:
- Display name:
- Internal owner (sales / CS lead):
- Primary business contact:
- Technical contact:
- Time zone / preferred schedule window:
- Priority / SLA tier:

## Environment Variables
- `DATABASE_URL`:
- `EXPORT_ROOT`:
- `REPORT_ROOT`:
- `LOG_LEVEL`:
- `TZ`:
- Additional env vars (API keys, bucket names, feature flags):

## Access Control
- VPN / bastion instructions:
- IP allow-list for our runner:
- Credential expiration / rotation cadence:
- Compliance classification (PII / PCI / HIPAA / internal):

## Scheduling & Jobs
- Target schedule windows (e.g., 5 a.m. daily, Mondays 8 a.m.):
- Job IDs assigned to each schedule:
- Expected rerun / recovery procedure:

## Distribution & Notifications
- Delivery channels needed (SFTP, S3, email, Slack, downstream DB):
- Email recipients:
- Slack/Teams channels or webhooks:
- Retention / archival policy:

## Notes
- Outstanding tasks / blockers:
- Links to supporting docs (ERDs, data dictionaries, runbooks):
