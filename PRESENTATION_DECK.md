# Cloud Computing FT-III Presentation Deck: SecureVault
**Project Title:** SecureVault — Secure Cloud File Storage & Disaster Recovery System  
**Course Code:** 21CSE362T (Cloud Computing)  
**Student Name:** Rohit M  

---

### Slide 1: Title & Problem Statement
- **Title:** SecureVault: Resilient Cloud File Storage & Version-Controlled Disaster Recovery
- **Context:** Cloud Storage Systems (FT-III Project)
- **Problem Statements:**
  1. *Unauthorized Exposure:* Misconfigured permissions in multi-tenant environments leading to privilege escalation and data leakage.
  2. *Data Loss & Overwrite Vulnerability:* Accidental modification or malicious deletion without point-in-time recovery guarantees.
- **Proposed Solution:** A cloud-native storage gateway implementing Role-Based Access Control (RBAC), immutable SHA-256 integrity verification, automated object versioning, and an immutable audit trail.

---

### Slide 2: Cloud Risks & Course Alignment
- **Relevance to Syllabus:**
  - *Unit 1:* Cloud computing characteristics, service models, security boundaries, and disaster recovery SLA commitments.
  - *Cloud Risks Addressed:* Multi-tenancy leakage, accidental administrative deletion, insider threats, and silent bit-rot / integrity tampering.
  - *Shared Responsibility Model:* SecureVault distinguishes provider responsibilities (storage infrastructure availability) from consumer responsibilities (access control enforcement and object lifecycle management).

---

### Slide 3: Objectives & Technical Requirements
- **Primary Objectives:**
  - Enforce zero-trust client access using Role-Based Access Control (Admin vs. Viewer roles).
  - Provide non-destructive file versioning supporting instantaneous point-in-time recovery.
  - Compute cryptographic fingerprints (SHA-256) at ingestion to detect data tampering.
  - Maintain an immutable audit log recording all transactions (`LOGIN`, `UPLOAD`, `RESTORE`, `DOWNLOAD`).
- **Core Requirements:**
  - Serverless architecture utilizing free-tier cloud resources without upfront capital expense.
  - Near-instant Recovery Point Objective (RPO $\approx$ 0) and minimal Recovery Time Objective (RTO < 5s).

---

### Slide 4: Proposed Cloud Architecture
- **Architecture Diagram:**
  - **Presentation Layer:** Streamlit Community Cloud (Interactive Python PaaS container).
  - **Compute & Logic:** Server-side execution handling cryptographic hashing and authorization gating.
  - **Storage Layer (IaaS/BaaS):** Supabase Storage Engine (Private Object Storage Bucket: `secure-files`).
  - **Metadata & State Engine:** Supabase Managed PostgreSQL Database (`file_versions` & `audit_logs`).
- **Data Flow:**
  - User uploads file $\rightarrow$ Streamlit computes SHA-256 $\rightarrow$ Object stream stored with unique version key $\rightarrow$ PostgreSQL records version metadata $\rightarrow$ Audit event committed.

---

### Slide 5: Service Models & Technology Justification
| Component | Cloud Service Model | Technology Used | Selection Justification |
| :--- | :--- | :--- | :--- |
| **Front-End & Application** | PaaS (Platform as a Service) | Streamlit Cloud | Rapid deployment from Git, zero-server maintenance, automated TLS termination. |
| **Object Store** | IaaS / BaaS | Supabase Storage (S3-compatible) | Private access controls, high durability, independent object lifecycle management. |
| **Relational Database** | DaaS (Database as a Service) | Supabase PostgreSQL | ACID compliance for audit trails, relational integrity constraints for file versions. |

---

### Slide 6: Security, Storage & Recovery Design
- **Cryptographic Integrity:**
  - Every upload computes a SHA-256 hash before committing the object. 
  - Restoring a file recalculates and compares hashes to mathematically guarantee identical payload state.
- **Non-Destructive Versioning:**
  - Overwrites never replace physical cloud objects.
  - A new object is created at `secure-files/{filename}_v{n}`, and pointer flags (`is_current`) are updated atomically in PostgreSQL.
- **Access Control & Auditability:**
  - Admin: Authorized for `UPLOAD`, `RESTORE`, `DELETE`, and `VIEW`.
  - Viewer: Read-only access (`DOWNLOAD`, `VIEW`). Upload/Restore controls are locked.
  - Append-only audit logs capture user identity, role, timestamp, and action parameters.

---

### Slide 7: Live Demonstration & Test Plan Execution
| Test Case | Objective | Action | Expected & Observed Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TC-01: RBAC Enforcement** | Verify privilege isolation | Log in as `viewer` | Upload & Restore controls disabled in UI | **PASS** |
| **TC-02: Cloud Ingestion** | Ingest file into private cloud bucket | Log in as `admin`, upload `sample.txt` | File persisted; SHA-256 registered; Version 1 active | **PASS** |
| **TC-03: Version Tracking** | Confirm non-destructive overwrite | Upload modified `sample.txt` | Version 2 generated; Version 1 preserved; distinct SHA-256 | **PASS** |
| **TC-04: Disaster Recovery** | Restore prior state after modification | Trigger Restore on Version 1 | Version 1 promoted to current; original hash restored | **PASS** |
| **TC-05: Audit Verification** | Confirm traceability | Inspect Audit Log tab | Chronological log of `LOGIN`, `UPLOAD`, `RESTORE` present | **PASS** |

---

### Slide 8: Evaluation Metrics, SLA, Cost & Limitations
- **Empirical Metrics:**
  - Functional Test Pass Rate: **100% (5/5 tests passed)**.
  - Recovery Time Objective (RTO): **< 2 seconds** (instantaneous database pointer switch).
  - Recovery Point Objective (RPO): **0 data loss** (immutable historic versions retained).
- **Cost & SLA Analysis:**
  - Operates within Supabase (Free tier: 1 GB storage, 500 MB DB) & Streamlit Cloud (Free tier: 1 GB RAM).
  - Production scaling requires moving from free shared resources to dedicated compute with contractual 99.9% uptime SLAs.
- **Architectural Limitations:**
  - Current prototype enforces RBAC at the application layer using a server-side service key.
  - Production evolution: Implement native Supabase Auth with Row Level Security (RLS) policies directly on PostgreSQL and Storage buckets.

---

### Slide 9: Conclusion & Viva Readiness
- **Key Takeaways:**
  - Demonstrated that cloud security requires a defense-in-depth approach: access controls, data integrity guarantees, and disaster recovery.
  - Verified that point-in-time recovery can be achieved efficiently using cloud metadata pointers without redundant data duplication.
- **Ready for Examiner Questions (Viva Prep):**
  - *Q: Why SHA-256 over MD5?* $\rightarrow$ Collision resistance against malicious file substitution attacks.
  - *Q: How is disaster recovery handled?* $\rightarrow$ Multi-version object retention with atomic pointer rollback in metadata.
  - *Q: Difference between PaaS and BaaS in this project?* $\rightarrow$ Streamlit hosts the compute application runtime (PaaS); Supabase manages storage and database engines as a service (BaaS).
