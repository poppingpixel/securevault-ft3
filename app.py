import os
import hashlib
from datetime import datetime, timezone

import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="SecureVault | Cloud Case Study", page_icon="🔐", layout="wide")

st.title("🔐 SecureVault")
st.caption("Cloud Security & Data Recovery — FT-III case study prototype")

st.info(
    "Demonstrates private cloud object storage, file-version recovery, role-based app permissions, "
    "and an audit log. This is an educational prototype, not a production security product."
)

def get_supabase() -> Client:
    url = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL", ""))
    key = st.secrets.get("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""))
    if not url or not key:
        st.error("Cloud backend is not configured yet. Add SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY to Streamlit Secrets.")
        st.stop()
    return create_client(url, key)

supabase = get_supabase()

# Prototype authentication is an application-level demo gate. The service key stays server-side
# in Streamlit Secrets; never expose it in GitHub or browser-side code.
def verify_demo_credentials(username, password):
    users = st.secrets.get("demo_users", {})
    if username not in users:
        return None
    entry = users[username]
    if isinstance(entry, dict) and entry.get("password") == password:
        return entry.get("role", "viewer")
    return None

if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.role = None

with st.sidebar:
    st.header("Demo sign-in")
    st.caption("Use accounts configured in Streamlit Secrets.")
    if st.session_state.user:
        st.success(f"Signed in: {st.session_state.user} ({st.session_state.role})")
        if st.button("Sign out"):
            st.session_state.user = None
            st.session_state.role = None
            st.rerun()
    else:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Sign in", type="primary"):
            role = verify_demo_credentials(username, password)
            if role:
                st.session_state.user = username
                st.session_state.role = role
                st.rerun()
            else:
                st.error("Invalid demo credentials.")

if not st.session_state.user:
    st.warning("Sign in using one of the demo accounts configured by the project owner.")
    st.stop()

user = st.session_state.user
role = st.session_state.role

def log_event(action, filename="", details=""):
    supabase.table("audit_logs").insert({
        "username": user,
        "role": role,
        "action": action,
        "filename": filename,
        "details": details,
        "created_at": datetime.now(timezone.utc).isoformat()
    }).execute()

def safe_name(name):
    # Keep object names predictable and avoid path traversal.
    cleaned = "".join(ch for ch in name if ch.isalnum() or ch in "._- ")
    return cleaned.strip().replace(" ", "_")[:100] or "uploaded_file"

def file_hash(data):
    return hashlib.sha256(data).hexdigest()

def list_versions(filename):
    return (supabase.table("file_versions")
            .select("*").eq("filename", filename)
            .order("version", desc=True).execute().data)

tabs = st.tabs(["📁 Files", "♻️ Recovery", "🧾 Audit log", "ℹ️ Architecture"])

with tabs[0]:
    st.subheader("Private cloud file storage")
    if role == "admin":
        uploaded = st.file_uploader("Upload a file (new upload creates a new version)", key="upload")
        if uploaded is not None and st.button("Upload to private cloud storage", type="primary"):
            filename = safe_name(uploaded.name)
            data = uploaded.getvalue()
            current = list_versions(filename)
            next_version = (max([int(x["version"]) for x in current]) + 1) if current else 1
            object_path = f"{filename}/v{next_version}_{file_hash(data)[:12]}"
            # Bucket must be private. App's server-side key is held in Streamlit Secrets.
            supabase.storage.from_("secure-files").upload(
                path=object_path,
                file=data,
                file_options={"content-type": uploaded.type or "application/octet-stream", "upsert": "false"}
            )
            supabase.table("file_versions").insert({
                "filename": filename,
                "version": next_version,
                "object_path": object_path,
                "sha256": file_hash(data),
                "size_bytes": len(data),
                "uploaded_by": user,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_current": True
            }).execute()
            # Mark previous versions as not current.
            supabase.table("file_versions").update({"is_current": False}).eq("filename", filename).neq("version", next_version).execute()
            log_event("UPLOAD", filename, f"Created version {next_version}; SHA-256 {file_hash(data)}")
            st.success(f"Uploaded {filename}, version {next_version}.")
            st.rerun()
    else:
        st.caption("Viewer access: uploads are disabled.")

    rows = (supabase.table("file_versions").select("*").eq("is_current", True)
            .order("filename").execute().data)
    if rows:
        for row in rows:
            c1, c2, c3, c4 = st.columns([3, 1, 1, 2])
            c1.write(f"**{row['filename']}**")
            c2.write(f"v{row['version']}")
            c3.write(f"{row['size_bytes']} bytes")
            c4.write(row["created_at"][:19].replace("T", " "))
            if role in ("admin", "viewer"):
                if st.button("Download", key=f"download_{row['id']}"):
                    result = supabase.storage.from_("secure-files").download(row["object_path"])
                    log_event("DOWNLOAD", row["filename"], f"Downloaded version {row['version']}")
                    st.download_button(
                        "Save downloaded file",
                        data=result,
                        file_name=row["filename"],
                        key=f"save_{row['id']}"
                    )
    else:
        st.write("No files yet. Sign in as admin and upload a small test file.")

with tabs[1]:
    st.subheader("Recover an earlier version")
    filenames = sorted({x["filename"] for x in (supabase.table("file_versions").select("filename").execute().data or [])})
    if role != "admin":
        st.warning("Only admins can restore versions.")
    elif filenames:
        chosen = st.selectbox("Choose a file", filenames)
        versions = list_versions(chosen)
        if versions:
            labels = {f"Version {x['version']} · {x['created_at'][:19]} · {x['size_bytes']} bytes": x for x in versions}
            label = st.selectbox("Select the version to recover", list(labels.keys()))
            selected = labels[label]
            st.code(f"SHA-256: {selected['sha256']}")
            if st.button("Restore selected version as current", type="primary"):
                supabase.table("file_versions").update({"is_current": False}).eq("filename", chosen).execute()
                supabase.table("file_versions").update({"is_current": True}).eq("id", selected["id"]).execute()
                log_event("RESTORE", chosen, f"Restored version {selected['version']} as current")
                st.success(f"Version {selected['version']} is now marked current. The original versions remain stored.")
                st.rerun()
    else:
        st.write("Upload a file first to create versions.")

with tabs[2]:
    st.subheader("Audit trail")
    if role == "admin":
        logs = (supabase.table("audit_logs").select("*").order("created_at", desc=True).limit(100).execute().data)
    else:
        logs = (supabase.table("audit_logs").select("*").eq("username", user)
                .order("created_at", desc=True).limit(50).execute().data)
    if logs:
        st.dataframe(logs, use_container_width=True, hide_index=True)
    else:
        st.write("No audit events recorded yet.")

with tabs[3]:
    st.subheader("System architecture")
    st.markdown("""
    **User browser** → **Streamlit Community Cloud (application layer)** → **Supabase PostgreSQL (metadata + audit logs)**  
    **Application layer** → **Supabase private Storage bucket (file objects and historical versions)**

    - **Service model:** PaaS for app hosting; managed database and object storage are consumed as cloud services.
    - **Security controls:** private bucket, server-side secret, role-gated application actions, audit logging, and SHA-256 integrity fingerprints.
    - **Recovery control:** every upload is stored as a separate version; restoring changes the current-version pointer without deleting prior versions.
    - **Limitations:** demo role checks are application-level and are not a substitute for production-grade identity management. Do not upload sensitive or personal files.
    """)
    st.caption("For a classroom demonstration only. Do not use this prototype to store confidential data.")
