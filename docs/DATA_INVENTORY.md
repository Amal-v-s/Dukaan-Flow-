# DukaanFlow Data Inventory & Privacy Classification

## Overview
This document records every data entity, field classification, storage mechanism, and retention schedule across DukaanFlow.

## Data Inventory Matrix

| Entity | Fields | Sensitivity | Storage | Retention |
|--------|--------|-------------|---------|-----------|
| **User Account** | `id`, `email`, `password_hash`, `full_name`, `role` | Confidentially Sensitive (PII) | `users` collection | Active account duration + 30 days |
| **Business Tenant** | `id`, `name`, `currency`, `timezone`, `safety_buffer_paise` | Business Confidential | `businesses` collection | Active account duration |
| **Customer** | `id`, `name`, `phone`, `notes`, `balances` | PII / Merchant Confidential | `customers` subcollection | Active account duration |
| **Khata Ledger Entry** | `id`, `customer_id`, `entry_type`, `amount_paise`, `effective_date`, `due_date` | Financial Record | `ledger_entries` | 7 years (statutory requirement) |
| **Supplier** | `id`, `name`, `phone`, `category` | Merchant Confidential | `suppliers` subcollection | Active account duration |
| **Supplier Bill** | `id`, `supplier_id`, `amount_paise`, `due_date`, `payments` | Financial Record | `supplier_bills` | 7 years (statutory requirement) |
| **Cash Transaction** | `id`, `type`, `description`, `amount_paise`, `date`, `direction` | Financial Record | `transactions` | 7 years (statutory requirement) |
| **Repayment Plan** | `id`, `customer_id`, `installments`, `status` | Financial Schedule | `repayment_plans` | 7 years (statutory requirement) |
| **Audit Event** | `id`, `business_id`, `actor_id`, `action`, `entity_type`, `timestamp` | Compliance Log | `audit_events` | 1 year minimum (immutable) |
| **Temporary CSV Import** | Staged rows, column mappings | Ephemeral | `import_batches` | 24 hours (auto-purged) |

## Data Residency & Sovereignty
- **Primary Database:** Google Cloud Firestore (Multi-region or Regional: `asia-south1`, Mumbai, India).
- **Backups:** Google Cloud Storage (Bucket Location: `asia-south1`, encrypted at rest via Google-managed encryption keys).
- **Processing:** Google Cloud Run container instances executing exclusively in `asia-south1`.
