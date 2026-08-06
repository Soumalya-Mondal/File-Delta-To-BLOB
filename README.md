# File-Delta-To-BLOB 🔁☁️

[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Azure](https://img.shields.io/badge/Azure-Blob%20Storage-0089D6?logo=microsoft-azure&logoColor=white)](https://azure.microsoft.com/en-us/services/storage/blobs/)
[![uv](https://img.shields.io/badge/uv-package%20manager-8A2BE2)](https://github.com/astral-sh/uv)
[![Status](https://img.shields.io/badge/status-WIP-yellow.svg)](./README.md)

> **Intelligent file-delta detection and selective Azure Blob Storage synchronization for codebases.**

`File-Delta-To-BLOB` is a Python-based CLI tool that monitors a local source directory (e.g., an analytics engine or any codebase), computes cryptographic file hashes, maintains a persistent state database, and **only uploads files that actually changed**—Added, Modified, or Deleted—to Azure Blob Storage. It minimizes network I/O, reduces storage costs, and guarantees integrity through end-to-end MD5 verification.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [A) Rebase Files Details](#a-rebase-files-details)
  - [B) Upload Files Delta](#b-upload-files-delta)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Database Schema](#database-schema)
- [Known Limitations](#known-limitations)
- [Roadmap & TODOs](#roadmap--todos)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

Modern development workflows often require syncing large codebases across distributed environments. Uploading entire repositories on every change is inefficient. This tool solves that by:

1. **Hashing every file** using MD5 (via 4 MB chunked reads for memory efficiency).
2. **Persisting hashes** in a local SQLite database and a portable JSON snapshot.
3. **Comparing current state** against the last known state to detect *deltas*.
4. **Uploading only the delta** (added/modified files) to Azure Blob Storage.
5. **Verifying integrity** at every step using blob-level content MD5 checks.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Delta Detection** | Identifies Added, Modified, and Deleted files by comparing MD5 hashes against historical state. |
| **Selective Upload** | Only changed files are uploaded to Azure Blob—saving bandwidth and time. |
| **Integrity Verification** | Every upload/download is validated using MD5 checksums. |
| **SQLite Ledger** | Local `AnalysisFileHash.db` maintains full audit history (status, timestamps, sizes). |
| **JSON Snapshot** | `FileHashDetails.json` acts as a lightweight, portable state snapshot synced to Blob. |
| **Smart Exclusions** | Automatically ignores `node_modules`, `__pycache__`, `.git`, `.venv`, lock files, and dotenv files. |
| **Two Operation Modes** | **Rebase** for clean slate initialization; **Upload** for incremental updates. |
| **Step-Level Observability** | Every operation returns a structured dict (`status`, `script_name`, `step`, `message`) for precise error tracing. |

---

## Architecture

```
┌──────────────────────┐
│   Source Codebase    │
│ (Analytics Engine)   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   File-Delta-To-BLOB │
│  ┌────────────────┐  │
│  │  MD5 Hashing   │  │
│  │  + Filtering   │  │
│  └────────────────┘  │
│           │          │
│           ▼          │
│  ┌────────────────┐  │
│  │ SQLite Database│  │  ← analysis_file_hash table
│  │FileHashDetails │  │
│  │     .json      │  │  ← portable snapshot
│  └────────────────┘  │
│           │          │
│           ▼          │
│  ┌────────────────┐  │
│  │  Delta Engine  │  │  ← Detect Added / Modified / Deleted
│  └────────────────┘  │
│           │          │
│           ▼          │
│  ┌────────────────┐  │
│  │ FilesDeltaStore│  │  ← staging folder for uploads
│  └────────────────┘  │
└──────────┬───────────┘
           │ Azure Blob Storage API
           ▼
┌──────────────────────┐
│    Azure Blob        │
│   FilesDeltaStore/   │
│  FileHashDetails.json│
└──────────────────────┘
```

---

## Prerequisites

- **Python** `>= 3.12`
- **Azure Blob Storage Account** with a container ready
- **Connection String** for your Azure Storage Account
- (Recommended) **[uv](https://github.com/astral-sh/uv)** for fast Python project management

---

## Installation

### Using `uv` (recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/File-Delta-To-BLOB.git
cd File-Delta-To-BLOB

# Create virtual environment and install dependencies
uv sync
```

### Using `pip`

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e "."
```

---

## Configuration

Create a `.env` file in the project root (or modify the existing one):

```dotenv
BLOB_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=your_account;AccountKey=your_key;EndpointSuffix=core.windows.net"
BLOB_CONTAINER_NAME="your-container-name"
```

> ⚠️ **Security Note:** Never commit your `.env` file or real connection strings to version control. The included `.gitignore` already excludes `.env` and all runtime artifacts (`database/`, `FilesDeltaStore/`, `FileHashDetails.json`).

### Important: Source Folder Path

The source directory to be scanned is currently **hardcoded** in `main.py`:

```python
analysis_engine_folder_path = Path('/home/soumalya/Desktop/Office-Work/Analytics-Engine')
```

You **must** change this to point to your own target directory before running the tool.

---

## Usage

Run the main entrypoint:

```bash
python main.py
```

You will be presented with an interactive menu:

```text
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
[A] -> Rebase Files Details
[B] -> Upload Files Delta
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Please Enter Your Choice:
```

### A) Rebase Files Details

**Purpose:** Initialize or fully reset the synchronization state.

**What it does:**
1. Deletes any existing local SQLite database and JSON snapshot.
2. Clears **all** files from the Azure Blob container.
3. Recursively scans the source codebase, skipping noise folders and files:
   - **Excluded folders:** `node_modules`, `__pycache__`, `.git`, `.venv`
   - **Excluded files:** `package-lock.json`, `.gitattributes`, `.gitignore`, `.python-version`, `.env`, `uv.lock`
4. Calculates MD5 hashes for every file using efficient 4 MB chunked reads.
5. Stores results in a new SQLite database (`database/AnalysisFileHash.db`).
6. Exports hashes to `FileHashDetails.json`.
7. Uploads the JSON snapshot to Azure Blob for remote state sharing.

**When to use:**
- First-time setup.
- After major repository restructuring.
- When you want a completely clean synchronization baseline.

### B) Upload Files Delta

**Purpose:** Incrementally synchronize only the files that changed since the last run.

**What it does:**
1. Validates that the local environment, database, and JSON snapshot are present.
2. Downloads the remote `FileHashDetails.json` from Azure Blob and verifies it matches the local snapshot byte-for-byte.
3. Scans the source codebase again and calculates fresh hashes.
4. **Detects deltas:**
   - **Added** — new files not in the previous snapshot.
   - **Modified** — files whose MD5 hash changed.
   - **Deleted** — files present in the snapshot but missing locally.
5. Stages added/modified files into the `FilesDeltaStore/` folder.
6. Upserts all changes into the SQLite database using `INSERT OR REPLACE`.
7. Updates the JSON snapshot with new states.
8. Uploads the delta files and the updated JSON snapshot to Azure Blob.

**When to use:**
- Daily development workflows after code changes.
- CI/CD pipelines that need to publish only artifacts that changed.

---

## Project Structure

```text
File-Delta-To-BLOB/
├── main.py                              # CLI entry point (interactive menu)
├── pyproject.toml                       # Project metadata & dependencies
├── .env                                 # Azure credentials (not committed)
├── .gitignore
├── .python-version                      # Pin to Python 3.12
├── README.md
├── uv.lock                              # uv lockfile for reproducible installs
│
├── database/                            # Runtime-generated SQLite DB
│   └── AnalysisFileHash.db
├── FilesDeltaStore/                     # Staging folder for delta uploads
│   └── ...
├── FileHashDetails.json                 # Portable hash snapshot (runtime-generated)
│
└── supportscript/                       # Modular operation scripts
    ├── rebasefilesdetails.py            # Full rebase: scan, hash, create DB/JSON, upload
    ├── uploadfilesdelta.py              # Incremental upload orchestrator
    ├── filedetailscompare.py            # Download remote JSON and validate against local
    ├── localfiledetailsupdate.py        # Detect Added/Modified/Deleted; stage files; update DB/JSON
    ├── localfileprocess.py              # (WIP stub — currently unimplemented)
    └── blobfilesoperation.py            # Unified Azure Blob operations: upload, download, clear
```



---

## How It Works

### State Machine

Each tracked file can be in one of four states:

| State | Meaning |
|-------|---------|
| `Original` | File existed during the last Rebase and has not changed. |
| `Added` | New file detected after the last Rebase/Upload. |
| `Modified` | File exists but its MD5 hash differs from the recorded hash. |
| `Deleted` | File existed in the snapshot but is no longer present locally. |

### Hash Comparison Flow

```
Last Known State (DB/JSON)     Current File System
        │                              │
        ▼                              ▼
   file_path: hash              file_path: hash
        │                              │
        └──────────┬───────────────────┘
                   │
            ┌──────┴──────┐
            │   Compare   │
            └──────┬──────┘
                   │
     ┌─────────────┼─────────────┐
     ▼             ▼             ▼
   Not Found    Different     Identical
     │             │             │
     ▼             ▼             ▼
   Deleted      Modified      Original
   (DB update)  (Stage +      (Skip)
                Upload +
                DB update)
```

### Integrity Guarantees

- **Upload:** The `Content-MD5` header is set on every blob. After upload, the tool queries blob properties and ensures the remote MD5 matches the local MD5.
- **Download:** After downloading from Blob, the tool re-computes the local MD5 and compares it to the blob's recorded `Content-MD5`.

### Blob Path Conventions

| File Type | Blob Path |
|-----------|-----------|
| Delta files (added/modified) | `FilesDeltaStore/<filename>` |
| Hash snapshot | `FileHashDetails.json` (root of container) |

---

## Database Schema

The SQLite database (`database/AnalysisFileHash.db`) contains a single table:

```sql
CREATE TABLE IF NOT EXISTS analysis_file_hash (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_uploaded_at DATETIME NOT NULL,
    file_path TEXT UNIQUE NOT NULL,
    file_md5_hash TEXT NOT NULL,
    file_size_in_bytes BIGINT NOT NULL,
    file_status TEXT NOT NULL DEFAULT 'Original'
        CHECK(file_status IN ('Original', 'Modified', 'Deleted', 'Added')),
    file_updated_at DATETIME NOT NULL
);
```

| Column | Description |
|--------|-------------|
| `id` | Auto-incrementing primary key |
| `file_uploaded_at` | ISO timestamp when the file was first recorded |
| `file_path` | Relative path from the source root (unique) |
| `file_md5_hash` | Hex-encoded MD5 hash of the file contents |
| `file_size_in_bytes` | File size in bytes |
| `file_status` | One of: `Original`, `Added`, `Modified`, `Deleted` |
| `file_updated_at` | ISO timestamp of the most recent status change |

---

## Known Limitations

The following behaviors are present in the current codebase and should be understood before production use:

1. **Hardcoded source path**  
   `analysis_engine_folder_path` is hardcoded as an absolute path in `main.py` (line 33). You must edit the source code to point to your own directory.

2. **Container-wide deletion on every upload**  
       `blobfilesoperation.py` (`file_upload_to_blob`) deletes **all existing blobs** in the container before uploading a single file when `blobs_delete=True`. When `uploadfilesdelta.py` loops over multiple delta files, the container is wiped for each file upload. This means with the current logic, after an upload operation only the JSON snapshot may remain in Blob. **This is a critical behavior that needs architectural correction.**

3. **Unimplemented stub module**  
   `localfileprocess.py` exists as a placeholder but contains no actual logic.

4. **No formal CLI framework**  
   The tool relies on interactive `input()` rather than command-line arguments, making it unsuitable for non-interactive automation (e.g., cron, CI/CD) without piping input.

5. **No unit or integration tests**  
   There are currently no automated tests. Validation is entirely manual.

6. **Memory usage on upload**  
    While most MD5 calculations use 4 MB chunked reads, `blobfilesoperation.py` (`file_upload_to_blob`) reads the entire file into memory at once (`local_file_data.read()`) for its own hash calculation. Very large files may cause memory spikes.

---

## Roadmap & TODOs

This project is under active development. The following items are planned or in-progress:

- [ ] **Fix container-wipe bug**: Decouple blob deletion from the per-file upload routine so delta uploads are additive rather than destructive.
- [ ] **Configuration-driven source path**: Move `analysis_engine_folder_path` to `.env` or a `config.yaml` instead of hardcoding it.
- [ ] **Complete `localfileprocess.py`**: Implement auxiliary local file transformations (e.g., minification, compression) before upload.
- [ ] **Deleted file artifact handling**: Generate deletion manifests or tombstone files for downstream consumers.
- [ ] **Parallel uploads/downloads**: Leverage `asyncio` or threading to speed up Blob transfers for large delta sets.
- [ ] **Retention policies**: Auto-clean old `FileHashDetails.json` versions in Blob.
- [ ] **CLI argument parsing**: Replace interactive `input()` with a proper CLI framework (e.g., `argparse`, `typer`, or `click`) for automation-friendly usage.
- [ ] **Unified chunked hashing**: Ensure `blobfilesoperation.py` (`file_upload_to_blob`) also uses 4 MB chunked reads for consistency and memory efficiency.
- [ ] **Comprehensive logging**: Replace `print()` statements with Python's `logging` module for configurable log levels and file output.
- [ ] **Unit & integration tests**: Add pytest suites for hash computation, delta detection, and mock Azure Blob interactions.
- [ ] **Docker support**: Provide a `Dockerfile` and `docker-compose.yml` for containerized execution.

---

## Contributing

Contributions are welcome! Since this is a WIP project, feel free to:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-improvement`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/my-improvement`)
5. Open a Pull Request

Please ensure any new features include appropriate logging steps and maintain the existing step-level error-handling pattern (`status`, `script_name`, `step`, `message`) for consistency.

---

## License

This project is provided as-is for demonstration and development purposes. You may add an open-source license of your choice (e.g., MIT, Apache-2.0) once finalized.

---

<p align="center">
  <i>Built with Python, SQLite, and Azure Blob Storage.</i>
</p>
