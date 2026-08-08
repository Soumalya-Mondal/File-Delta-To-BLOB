# File-Delta-To-BLOB 🔁☁️

[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Azure](https://img.shields.io/badge/Azure-Blob%20Storage-0089D6?logo=microsoft-azure&logoColor=white)](https://azure.microsoft.com/en-us/services/storage/blobs/)
[![uv](https://img.shields.io/badge/uv-package%20manager-8A2BE2)](https://github.com/astral-sh/uv)
[![Status](https://img.shields.io/badge/status-beta-green.svg)](./README.md)

> **Intelligent file-delta detection and bidirectional Azure Blob Storage synchronization for codebases.**

`File-Delta-To-BLOB` is a Python-based CLI tool that monitors a local source directory (e.g., an analytics engine or any codebase), computes cryptographic file hashes, maintains a persistent state database, and **only uploads files that actually changed**—Added, Modified, or Deleted—to Azure Blob Storage. It also supports **downloading deltas** from Blob to keep a local workspace in sync. It minimizes network I/O, reduces storage costs, and guarantees integrity through end-to-end MD5 verification.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [A) Rebase Files Details](#a-rebase-files-details)
  - [B) Upload Files Delta](#b-upload-files-delta)
  - [C) Download Files Delta](#c-download-files-delta)
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
5. **Downloading deltas** from Azure Blob to synchronize a local workspace.
6. **Verifying integrity** at every step using blob-level content MD5 checks.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Delta Detection** | Identifies Added, Modified, and Deleted files by comparing MD5 hashes against historical state. |
| **Selective Upload** | Only changed files are uploaded to Azure Blob—saving bandwidth and time. |
| **Selective Download** | Downloads only the delta files from Blob and applies Add, Modified, and Delete operations locally. |
| **Integrity Verification** | Every upload/download is validated using MD5 checksums and file-size checks. |
| **SQLite Ledger** | Local `AnalysisFileHash.db` maintains full audit history (status, timestamps, sizes). |
| **JSON Snapshot** | `FileHashDetails.json` acts as a lightweight, portable state snapshot synced to Blob. |
| **Smart Exclusions** | Automatically ignores `node_modules`, `__pycache__`, `.git`, `.venv`, lock files, and dotenv files. |
| **Three Operation Modes** | **Rebase** for clean slate initialization; **Upload** for incremental updates; **Download** for local sync. |
| **Step-Level Observability** | Every operation returns a structured dict (`status`, `script_name`, `step`, `message`) for precise error tracing. |

---

## Architecture

```
┌──────────────────────┐         ┌──────────────────────┐
│   Source Codebase    │◄────────│   Source Codebase    │
│ (Analytics Engine)   │  Sync   │ (Another Workstation)│
└──────────┬───────────┘         └──────────┬───────────┘
           │                                ▲
           │ Upload                         │ Download
           ▼                                │
┌──────────────────────┐                    │
│   File-Delta-To-BLOB │                    │
│  ┌────────────────┐  │                    │
│  │  MD5 Hashing   │  │                    │
│  │  + Filtering   │  │                    │
│  └────────────────┘  │                    │
│           │          │                    │
│           ▼          │                    │
│  ┌────────────────┐  │                    │
│  │ SQLite Database│  │  ← analysis_file_hash table
│  │FileHashDetails │  │                    │
│  │     .json      │  │  ← portable snapshot
│  └────────────────┘  │                    │
│           │          │                    │
│           ▼          │                    │
│  ┌────────────────┐  │                    │
│  │  Delta Engine  │  │  ← Detect Added / Modified / Deleted
│  └────────────────┘  │                    │
│           │          │                    │
│           ▼          │                    │
│  ┌────────────────┐  │                    │
│  │ FilesDeltaStore│  │  ← staging folder for uploads/downloads
│  └────────────────┘  │                    │
└──────────┬───────────┘                    │
           │ Azure Blob Storage API         │
           ▼                                │
┌──────────────────────┐                    │
│    Azure Blob        │────────────────────┘
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
git clone <repository-url>
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

### Dependencies

The following packages are required (defined in `pyproject.toml`):

| Package | Version |
|---------|---------|
| `azure-storage-blob` | `>=12.30.0` |
| `python-dotenv` | `>=1.2.2` |

---

## Configuration

Copy `.env.example` to `.env` and fill in your Azure credentials:

```bash
cp .env.example .env
```

Then edit `.env`:

```dotenv
BLOB_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=your_account;AccountKey=your_key;EndpointSuffix=core.windows.net"
BLOB_CONTAINER_NAME="your-container-name"
```

> ⚠️ **Security Note:** Never commit your `.env` file or real connection strings to version control. The included `.gitignore` excludes `.env`, `.venv`, and Python build artifacts (`__pycache__/`, `build/`, `dist/`, etc.).
>
> ⚠️ **Important:** Runtime artifacts (`database/`, `FilesDeltaStore/`, `FileHashDetails.json`) are **not** currently excluded by `.gitignore` — take care not to commit them to version control.

### Important: Source Folder Path

The source directory to be scanned is currently **hardcoded** in `main.py`:

```python
analysis_engine_folder_path = Path('/home/soumalya/Desktop/Office-Work/Analytics-Engine')
```

You **must** change this to point to your own target directory before running the tool.

---

## Quick Start

After installation and [configuration](#configuration), run the tool:

```bash
python main.py
```

**Typical first-time workflow:**

1. Choose **A) Rebase Files Details** — scans your source directory, builds the local database, and pushes the initial snapshot to Azure Blob.
2. Make changes to your source code.
3. Choose **B) Upload Files Delta** — only the changed files are uploaded.
4. On another machine, choose **C) Download Files Delta** — pulls down the latest changes and applies them locally.

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
[C] -> Download Files Delta
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
5. Clears the Azure Blob container (including the old snapshot).
6. Stages added/modified files into the `FilesDeltaStore/` folder.
7. Upserts all changes into the SQLite database using `INSERT OR REPLACE`.
8. Updates the JSON snapshot with new states.
9. Uploads the delta files and the updated JSON snapshot to Azure Blob.

**When to use:**
- Daily development workflows after code changes.
- CI/CD pipelines that need to publish only artifacts that changed.

### C) Download Files Delta

**Purpose:** Download the latest delta from Azure Blob and apply it to the local codebase.

**What it does:**
1. Validates that the local environment, database, and JSON snapshot are present.
2. Deletes and recreates the local `FilesDeltaStore/` staging folder.
3. Downloads the remote `FileHashDetails.json` from Azure Blob.
4. Compares the remote snapshot against the local snapshot to compute deltas:
   - **Add** — files present in Blob but missing locally.
   - **Modified** — files whose remote hash differs from the local hash.
   - **Delete** — files present locally but missing in Blob.
5. Downloads the actual delta files from Azure Blob into `FilesDeltaStore/`.
6. **Applies changes locally:**
   - **Add** — copies new files from `FilesDeltaStore/` to the analysis engine (verifies size + MD5 after copy).
   - **Modified** — deletes the old local file, then copies the new version from `FilesDeltaStore/` (verifies size + MD5).
   - **Delete** — removes the file from the local analysis engine.
7. **Re-verifies integrity:** Re-scans the entire analysis engine directory, recomputes every file's MD5 hash, and cross-references it against the downloaded snapshot to guarantee 100% consistency before updating the local database and JSON snapshot.

**When to use:**
- Setting up a new workstation with the latest codebase state.
- Pulling down changes published by another developer or CI/CD pipeline.
- Recovering a local workspace to match the remote Blob state.

---

## Project Structure

```text
File-Delta-To-BLOB/
├── main.py                              # CLI entry point (interactive menu)
├── pyproject.toml                       # Project metadata & dependencies
├── .env                                 # Azure credentials (not committed)
├── .env.example                         # Example environment variables (safe to commit)
├── .gitignore
├── .python-version                      # Pin to Python 3.12
├── LICENSE                              # MIT License
├── README.md
├── uv.lock                              # uv lockfile for reproducible installs
│
├── database/                            # Runtime-generated SQLite DB
│   └── AnalysisFileHash.db
├── FilesDeltaStore/                     # Staging folder for delta uploads/downloads
│   └── ...
├── FileHashDetails.json                 # Portable hash snapshot (runtime-generated)
│
└── supportscript/                       # Modular operation scripts
    ├── rebasefilesdetails.py            # Full rebase: scan, hash, create DB/JSON, upload
    ├── uploadfilesdelta.py              # Incremental upload orchestrator
    ├── downloadfilesdelta.py            # Download remote delta and apply to local workspace
    ├── localfileprocess.py              # Local file add/modify/delete with integrity verification
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

### Upload Hash Comparison Flow

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

### Download Delta Flow

```
Remote Blob Snapshot            Local Snapshot
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
    Delete       Modified      Skip
    (local)      (download +   (no action)
                 replace)
```

### Integrity Guarantees

- **Upload:** The `Content-MD5` header is set on every blob. After upload, the tool queries blob properties and ensures the remote MD5 matches the local MD5.
- **Download:** After downloading from Blob, the tool re-computes the local MD5 and compares it to the blob's recorded `Content-MD5`. After applying changes locally, it performs a full re-scan of the analysis engine and cross-references every file against the blob snapshot to ensure complete consistency.
- **Local Apply:** After copying a downloaded file into the analysis engine, the tool verifies both file size and MD5 hash match the source in `FilesDeltaStore/`.

### Blob Path Conventions

| File Type | Blob Path |
|-----------|-----------|
| Delta files (added/modified) | `FilesDeltaStore/<relative_path>` |
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
   `analysis_engine_folder_path` is hardcoded as an absolute path in `main.py` (line 34). You must edit the source code to point to your own directory.

2. **Container-wide deletion on rebase & upload**  
   Both `rebasefilesdetails.py` and `uploadfilesdelta.py` clear **all** files from the Azure Blob container (including `FileHashDetails.json`) before uploading new state. A rebase is inherently destructive to remote state, and uploads replace the entire container contents.

3. **No formal CLI framework**  
   The tool relies on interactive `input()` rather than command-line arguments, making it unsuitable for non-interactive automation (e.g., cron, CI/CD) without piping input.

4. **Strict local verification gap**  
   `localfileprocess.py` checks copied files using `and` rather than `or` — a verification failure is only raised if **both** size and MD5 differ simultaneously. If a file changes content while retaining the same size (or vice versa), the mismatch can go undetected.

5. **No unit or integration tests**  
   There are currently no automated tests. Validation is entirely manual.

---

## Roadmap & TODOs

This project is under active development. The following items are planned or in-progress:

- [x] **Implement `localfileprocess.py`** — Local file transformations (add, modify, delete) with size + MD5 verification. *(Completed)*
- [x] **Implement `downloadfilesdelta.py`** — Download remote delta and apply to local workspace. *(Completed)*
- [x] **Add LICENSE and `.env.example`** — Standardize the repository for contributors. *(Completed)*
- [ ] **Configuration-driven source path**: Move `analysis_engine_folder_path` to `.env` or a `config.yaml` instead of hardcoding it.
- [ ] **Deleted file artifact handling**: Generate deletion manifests or tombstone files for downstream consumers.
- [ ] **Parallel uploads/downloads**: Leverage `asyncio` or threading to speed up Blob transfers for large delta sets.
- [ ] **Retention policies**: Auto-clean old `FileHashDetails.json` versions in Blob.
- [ ] **CLI argument parsing**: Replace interactive `input()` with a proper CLI framework (e.g., `argparse`, `typer`, or `click`) for automation-friendly usage.
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

See [LICENSE](./LICENSE) for details.

This project is licensed under the MIT License.

---

<p align="center">
  <i>Built with Python, SQLite, and Azure Blob Storage.</i>
</p>
