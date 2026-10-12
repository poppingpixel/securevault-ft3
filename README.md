# SecureVault — Cloud Computing FT-III

## What it demonstrates
- Cloud-hosted Streamlit application
- Supabase managed PostgreSQL metadata and audit logs
- Private Supabase Storage bucket for files
- Versioned uploads, restore workflow, SHA-256 fingerprints
- Admin/viewer demonstration roles and audit trail

> Educational prototype only. Demo roles are app-level checks, not production identity management. Do not upload sensitive files.

## 1. Create cloud accounts
1. Create/sign in to GitHub.
2. Create/sign in to Supabase and create a project.
3. Create/sign in to Streamlit Community Cloud.

## 2. Configure Supabase
1. In Storage, create a bucket named `secure-files` and ensure it is **private**.
2. Open SQL Editor and run all SQL from `supabase_setup.sql`.
3. Open Project Settings / API (or Connect) and copy the project URL and service-role key. Keep the service-role key secret.

## 3. Upload code to GitHub
Create a repository named `securevault-ft3`. Upload:
- `app.py`
- `requirements.txt`
- `supabase_setup.sql`
- `README.md`

Do not upload keys or passwords.

## 4. Deploy
1. Open https://share.streamlit.io/
2. Choose Create app → select the GitHub repository → main branch → `app.py`.
3. Before or after first launch, open app settings / Secrets and paste the TOML below, replacing placeholders.
4. Restart/redeploy the app.

```toml
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "YOUR_SERVICE_ROLE_KEY"

[demo_users.admin]
password = "CHANGE_THIS_ADMIN_PASSWORD"
role = "admin"

[demo_users.viewer]
password = "CHANGE_THIS_VIEWER_PASSWORD"
role = "viewer"
```

Use unique demo passwords and do not reuse your personal passwords.

## 5. Demo test plan
1. Sign in as `viewer`; confirm upload and restore are disabled.
2. Sign in as `admin`; upload a harmless text file named `sample.txt`.
3. Upload a changed version with the same filename.
4. Open Recovery and restore the first version.
5. Download the current file and verify its contents.
6. Open Audit log and show UPLOAD, RESTORE, and DOWNLOAD entries.
7. Capture screenshots and record actual observations. Do not invent performance numbers.

## Evaluation metrics to report
- Functional test pass rate = passed tests / total tests × 100%
- Upload/download time = measured seconds for each test file size
- Recovery correctness = whether restored content matches selected version
- Integrity check = compare SHA-256 fingerprints
- Cost discussion = use the current free-tier limits and state that usage beyond included quotas may incur charges; do not claim production cost from a classroom test.

## Architecture
Browser → Streamlit Community Cloud → Supabase PostgreSQL (metadata/audit)  
Streamlit server → Supabase private object storage (file versions)

## Important technical limitation
The Streamlit app uses the Supabase service-role key server-side and performs demo role checks in the app. This is acceptable only for a controlled classroom prototype. A production system should use per-user Supabase Auth and Row Level Security policies and enforce authorization at the storage/database layer.
