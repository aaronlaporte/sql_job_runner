# Nomadata Connection Checklist

## Client Metadata
- Client name: Nomadata Labs (Demo Sandbox)
- Primary contact: demo@nomadata.com / +1-555-0101
- Escalation: platform@nomadata.com
- Schedule window: 5 a.m. ET

## Database Connectivity
- Engine: SQLite via SQLAlchemy (`sqlite:///data/demo.sqlite`)
- Host/cluster: local file `data/demo.sqlite`
- Port: n/a
- Database/catalog: demo.sqlite
- Schemas: default (tables `orders`, `technology_risk_assessments`, etc.)
- Auth: none (file-based)
- Username/password: n/a
- Extra params: ensure `data/` writable
- Network: local filesystem
- Test SQL: `SELECT COUNT(*) FROM orders;`

## Output Requirements
- Formats: CSV + Markdown summaries
- Destinations: `EXPORT_ROOT=exports`, `REPORT_ROOT=reports`
- Retention: keep recent files, archive zipped snapshot to `exports/archive/tech_risk_snapshot.zip`
- SFTP: not required
- Cloud buckets: not required (plugins present but disabled)

## Notifications & Integrations
- Email recipients: none
- SMTP: not configured
- Slack webhook: not configured
- Other: `data_quality_snapshot` JSON for comparisons

## Job Configuration
- SQL templates: `sample_orders.sql`, `tech_summary_analysis.sql`, `tech_risk_snapshot.sql`
- Parameters: default date windows in YAMLs
- Validation: JSON validation enabled
- Post-process: markdown summary, combos, archive zip, data-quality snapshot (cloud/email/slack disabled)

## Access & Compliance
- Data classification: internal demo only
- Supporting docs: repository README + seed scripts
- Audit requirements: none
- Credential review: refresh demo DB monthly

### Notes
- Enable cloud/email/slack plugins only when real endpoints exist
- Keep `envs/clients/nomadata.env` as the default test client
