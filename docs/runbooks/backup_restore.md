# Runbook: Backup & Disaster Recovery Architecture

## Service Level Objectives
- **Recovery Point Objective (RPO):** 24 hours (Automated nightly exports via Cloud Scheduler).
- **Recovery Time Objective (RTO):** 2 hours (Automated import into fresh Firestore instance).

## Backup Strategy
1. **Automated Daily Export:**
   - Cloud Scheduler triggers `infra/backup-firestore.sh` at 02:00 IST every night.
   - Files are stored in a Cloud Storage bucket located in `asia-south1`.
   - Lifecycle policy automatically transitions backups to Coldline after 30 days and deletes after 90 days.

2. **Immutable Audit Trail:**
   - Financial audit records in the `audit_events` collection are append-only.
   - Deletions are disallowed by Firestore security rules.

## Disaster Recovery Procedure
1. Verify target project state (typically staging or a freshly provisioned production project).
2. Execute restore command:
   ```bash
   ./infra/restore-firestore.sh gs://dukaanflow-production-backups/firestore/LATEST_TIMESTAMP dukaanflow-production
   ```
3. Run post-restore sanity checks:
   ```bash
   pytest tests/test_pilot_e2e.py
   ```
4. Verify tenant balances match expected checksums.
