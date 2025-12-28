# Client Onboarding Form (SQL Access)

Use this checklist to gather every credential or configuration needed before wiring a client into the job runner. Store the completed form securely; copy only the fields required into `envs/clients/<client>.env`.

## Client Metadata
- **Client name:**  
- **Primary contact (name/email/phone):**  
- **Escalation contact:**  
- **Time zone / preferred schedule window:**  

## Database Connectivity
- **Engine/driver (e.g., PostgreSQL, SQL Server, Snowflake):**  
- **Hostname / cluster:**  
- **Port:**  
- **Database / catalog:**  
- **Schema(s) to read from:**  
- **Authentication model:** password / key pair / IAM / Kerberos (specify)  
- **Username / service account:**  
- **Password / secret / certificate path:**  
- **Additional connection params (SSL mode, warehouse, role, etc.):**  
- **Network requirements:** VPN, bastion host, static IP allow-list, TLS certificates  
- **Test SQL to verify permissions:**  

## Output Requirements
- **Export format(s):** CSV / Parquet / Excel  
- **Destination directories:** `EXPORT_ROOT` = …, `REPORT_ROOT` = …  
- **Retention policy / archival needs (zip, S3, etc.):**  
- **SFTP details (if applicable):** host, port, username, path, SSH key / password  
- **Cloud buckets (S3/GCS/Azure) and credentials:**  

## Notifications & Integrations
- **Email recipients for reports:**  
- **SMTP settings (host, port, TLS, username, password):**  
- **Slack / Teams webhook URLs or channels:**  
- **Other integrations (PagerDuty, ServiceNow, etc.):**  

## Job Configuration
- **Initial SQL templates needed:**  
- **Parameter defaults (dates, filters):**  
- **Validation rules / thresholds:**  
- **Post-process steps required (load to DB, archive, uploads, alerts):**  

## Access Control & Compliance
- **Data classification:** internal / confidential / regulated (PII, PCI, HIPAA)  
- **Supporting documentation (ERD, data dictionary, SLA):**  
- **Audit requirements (logging, approval chains):**  
- **Expiration / review cadence for credentials:**  

### Notes / Outstanding Tasks
-  
