# Project Context

**Last Updated:** 2026-09-28
**Updated By:** repo-research skill

---

## Project Structure

### Repo Map

```text
email-flow-qa-slack-automation/
├── .env.example
├── .gitignore
├── credentials.example.json
├── pytest.ini
├── requirements.txt
├── README.md
├── email_flow_dedup.db
├── config.py
├── dedup_store.py
├── email_flow_handoff_bot.py
├── google_drive_client.py
├── monday_client.py
├── slack_dispatcher.py
├── webhook_server.py
└── tests/
    ├── test_dedup_store.py
    ├── test_google_drive.py
    ├── test_monday_client.py
    ├── test_orchestrator.py
    ├── test_slack_dispatcher.py
    └── test_webhook_server.py
```

### Key File Classifications

- **Root Config & Dependency Files**:
  - [requirements.txt](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/requirements.txt): Pinned Python package dependencies.
  - [pytest.ini](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/pytest.ini): Pytest testpaths and pythonpath configuration.
  - [.gitignore](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/.gitignore): Git ignore rules for virtualenvs, caches, keys, and DBs.
- **Configuration & Secret Templates**:
  - [.env.example](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/.env.example): Environment variable template.
  - [credentials.example.json](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/credentials.example.json): Google Cloud Service Account credentials format.
- **Documentation**:
  - [README.md](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/README.md): System architecture, execution modes, stakeholder directory, and setup instructions.
- **Entry Points**:
  - [webhook_server.py](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/webhook_server.py): FastAPI real-time webhook listener for Monday.com column event triggers.
  - [email_flow_handoff_bot.py](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/email_flow_handoff_bot.py): CLI poller, batch runner, and core orchestrator runner.
- **Core Modules & Business Logic**:
  - [config.py](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/config.py): Central environment configuration, board IDs, column mappings, and user directories.
  - [dedup_store.py](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/dedup_store.py): SQLite-backed deduplication store preventing repeated thread creation.
  - [google_drive_client.py](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/google_drive_client.py): Google Drive v3 client for master QA checklist cloning, permissions, and fallback copy doc search.
  - [monday_client.py](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/monday_client.py): Monday.com GraphQL API v2 client for pulse fetching, column normalization, and thread TS writeback.
  - [slack_dispatcher.py](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/slack_dispatcher.py): Slack SDK client formatting and publishing the canonical Jae Hong thread and nested replies.
- **Data & Storage**:
  - `email_flow_dedup.db`: SQLite database file storing processed item and thread records.
- **Test Suite**:
  - [tests/test_dedup_store.py](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/tests/test_dedup_store.py): SQLite store CRUD, idempotence, and persistence tests.
  - [tests/test_google_drive.py](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/tests/test_google_drive.py): Checklist cloning, permissions, and Drive fallback search tests.
  - [tests/test_monday_client.py](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/tests/test_monday_client.py): Column parsing, board eligibility checks, and GraphQL mutations.
  - [tests/test_orchestrator.py](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/tests/test_orchestrator.py): End-to-end orchestration pipeline and fallback flows.
  - [tests/test_slack_dispatcher.py](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/tests/test_slack_dispatcher.py): Jae Hong message formatting, user mentions, and dry-run output.
  - [tests/test_webhook_server.py](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/tests/test_webhook_server.py): FastAPI webhook challenge, filtering, and background task queuing.

---

## Project Identity

- **Name**: Email.Flow QA Handoff Automation
- **Type**: Enterprise Automation Service (Scheduled CLI Poller + Real-Time FastAPI Webhook Server)
- **Author / Lead**: Rishi Dutta (MediaMonks Marketing Technology)
- **Purpose**: Connects Monday.com campaign tracking boards, Google Drive QA checklists and copy docs, Gamma email deployment URLs, and Slack team communication channels to trigger, provision, and post automated QA handoffs.
- **Domain**: Marketing Technology / Email Marketing Campaign Production & QA Automation for Google / MediaMonks.

---

## Technology Stack

- **Runtime / Language**: Python 3.10+ (Local venv: Python 3.14.7)
- **API & Web Framework**:
  - `fastapi` (0.141.1)
  - `starlette` (1.7.0)
  - `uvicorn` (0.54.0)
- **Third-Party API SDKs & HTTP Clients**:
  - `slack_sdk` (3.44.1) for Slack WebClient operations
  - `google-api-python-client` (2.200.0) & `google-auth` (2.58.1) for Google Drive API v3
  - `requests` (2.34.2) for Monday.com GraphQL v2 requests
  - `httpx` (0.28.1) for test clients and async HTTP operations
- **Data Modeling & Serialization**:
  - `pydantic` (2.13.5) & `pydantic_core` (2.46.5)
- **Configuration & Environment**:
  - `python-dotenv` (1.2.3)
- **Local Persistence**:
  - SQLite (`sqlite3` built-in module)
- **Testing**:
  - `pytest` (9.1.1)
  - `pytest-mock` (3.16.0)

---

## Configuration

- **Primary Configuration Module**: [config.py](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/config.py)
- **Environment Template**: [.env.example](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/.env.example)
- **Credentials Template**: [credentials.example.json](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/credentials.example.json)
- **Environment Variables**:
  - `SLACK_BOT_TOKEN`: Slack bot token (`xoxb-...`) requiring `chat:write`, `links:write`, `chat:write.public`. Default: `xoxb-your-bot-token`.
  - `SLACK_CHANNEL_ID`: Slack channel ID for QA handoff threads. Default: `C0ANGFFEFS8`.
  - `MONDAY_API_TOKEN`: Monday.com API v2 token. Default: `your-monday-token`.
  - `MONDAY_API_URL`: Monday.com GraphQL endpoint. Default: `https://api.monday.com/v2`.
  - `MONDAY_API_VERSION`: Monday.com API version header. Default: `2023-10`.
  - `WATCH_BOARDS`: Comma-separated list of Monday board IDs to monitor. Default: `4209532311,4209567424` (Viewers and Creators Project Hubs).
  - `MONDAY_THREAD_TS_COLUMN`: Monday column ID storing Slack thread timestamp for traceability. Default: `slack_thread_ts`.
  - `MASTER_CHECKLIST_TEMPLATE_ID`: Master Google Sheet ID for QA Checklist. Default: `1AQOaskr3VWWl7rCBzMr505uVXBjCBmQ96M_zn7QkJ6I`.
  - `GOOGLE_APPLICATION_CREDENTIALS`: Path to Google Service Account credentials JSON. Default: `credentials.json`.
  - `GOOGLE_DRIVE_SHARE_DOMAIN`: Domain for automatic Google Drive permission granting. Default: `monks.com`.
  - `DEDUP_DB_PATH`: SQLite database file path. Default: `email_flow_dedup.db`.
  - `POLL_INTERVAL_SECONDS`: Delay between polling cycles in seconds. Default: `60`.
  - `GAMMA_BASE_URL`: URL template for the Gamma deployment tool. Default: `https://gamma.corp.google.com/index.html#/campaign/{campaign_id}/home`.

---

## Development Workflow

- **Virtual Environment & Dependencies**:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```
- **Configuration Setup**:
  ```bash
  cp .env.example .env
  # Update tokens in .env
  # Place Google Service Account credentials JSON at credentials.json
  ```
- **Running Test Suite**:
  ```bash
  .venv/bin/pytest -v
  ```
- **Running Execution Modes**:
  - Single Polling Pass: `.venv/bin/python email_flow_handoff_bot.py`
  - Dry-Run Poller: `.venv/bin/python email_flow_handoff_bot.py --dry-run`
  - Continuous Poller: `.venv/bin/python email_flow_handoff_bot.py --watch --interval 60`
  - Demo with Sample Campaign: `.venv/bin/python email_flow_handoff_bot.py --demo`
  - Single Pulse Test: `.venv/bin/python email_flow_handoff_bot.py --pulse 12345678 --dry-run`
  - Webhook Server: `.venv/bin/uvicorn webhook_server:app --host 0.0.0.0 --port 8000 --reload`

---

## Architecture Patterns

- **Dual Execution Pattern**:
  1. *Push Mode (Real-Time)*: [webhook_server.py](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/webhook_server.py) receives Monday.com column modification events via webhook, performs security handshake (`challenge`), verifies column eligibility, and spawns non-blocking asynchronous `BackgroundTasks`.
  2. *Pull Mode (Scheduled Poller)*: [email_flow_handoff_bot.py](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/email_flow_handoff_bot.py) periodically queries Monday.com boards via GraphQL API across monitored boards (`WATCH_BOARDS`).
- **Orchestration Pipeline**:
  The [EmailFlowOrchestrator](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/email_flow_handoff_bot.py#L44) manages the 7-step pipeline:
  1. *Deduplication Guard 1*: Check local SQLite DB (`processed_campaigns` table) for item ID.
  2. *Deduplication Guard 2*: Check Monday item's `slack_thread_ts` column to prevent duplicate runs across distributed workers.
  3. *Eligibility Check*: Confirm `is_email_flow` checkbox is `True` and `stage` matches qualifying QA stages (`Needs QA - Everything approved`, `QA in progress`, `Needs QA - content not finalized`).
  4. *Campaign ID & Asset Resolution*: Extract 5-digit campaign ID (`r"^(\d{5})"`). Resolve copy doc link from Monday doc column, or fall back to searching Google Drive for `[Copy Doc] <ID>`, or generate default fallback URL with visual alert. Formulate Gamma campaign URL.
  5. *Checklist Provisioning*: Clone master Google Spreadsheet template (`duplicate_qa_checklist`), inject custom properties, and grant domain/user write permissions.
  6. *Slack Thread Dispatch*: Post canonical Jae Hong thread parent with team mentions (`<@USER_ID|Name>`), followed by 3 structured replies.
  7. *Persistence & Writeback*: Insert record into SQLite and write back `slack_thread_ts` to Monday column.
- **Fail-Safe & Idempotency Patterns**:
  - SQLite database commits use `INSERT OR REPLACE` with unique `item_id` primary key.
  - Dry-run mode (`--dry-run`) enables end-to-end execution simulation without modifying external APIs or sending Slack notifications.
  - Drive client falls back gracefully to mock URLs if credentials are not present in non-production environments.

---

## External Integrations

- **Monday.com API v2**:
  - Protocol: GraphQL over HTTP POST (`https://api.monday.com/v2`).
  - Auth: API token via `Authorization` header, with `API-Version: 2023-10`.
  - Operations: Board items query (`GetBoardItems`), single item query (`GetItem`), and column value mutation (`change_simple_column_value`).
- **Google Drive API v3**:
  - Protocol: Google API Client Discovery over HTTPS.
  - Auth: Service Account JSON file (`credentials.json`) or GCP Application Default Credentials (ADC).
  - Scope: `https://www.googleapis.com/auth/drive`.
  - Operations: Template cloning (`files().copy()`), domain/user permission granting (`permissions().create()`), and search queries (`files().list()`).
- **Slack Web API**:
  - Protocol: Slack SDK WebClient (`chat.postMessage`).
  - Auth: Bot User OAuth Token (`xoxb-...`).
  - Scopes: `chat:write`, `links:write`, `chat:write.public`.
  - Features: Thread parent message posting, threaded reply messages (`thread_ts`), rich link unfurling configuration.
- **Gamma Deployment Tool**:
  - Target URL format: `https://gamma.corp.google.com/index.html#/campaign/{campaign_id}/home`.
- **SQLite**:
  - Local database `email_flow_dedup.db` using Python's standard `sqlite3` driver.

---

## API Surface / Route Map

The FastAPI webhook listener in [webhook_server.py](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/webhook_server.py) provides the following routes:

| Method | Path | Purpose |
| :--- | :--- | :--- |
| `POST` | `/webhook/monday` | Receives Monday.com webhook payloads, responds to `challenge` handshake, filters trigger column events, and enqueues background QA handoff tasks. |
| `GET` | `/health` | Liveness and health check endpoint for container orchestrators (returns service name and status). |
| `GET` | `/status` | Service diagnostic endpoint returning total processed count and recent records from SQLite. |

---

## Runtime Dependency Graph

```text
[Monday.com Webhook] ──────────► POST /webhook/monday (:8000)
                                        │
                                        ▼ (FastAPI BackgroundTasks)
[Scheduled Poller (CLI)] ──────► EmailFlowOrchestrator
                                        │
         ┌──────────────────────────────┼──────────────────────────────┐
         ▼                              ▼                              ▼
    MondayClient              GoogleDriveProvisioner         SlackThreadDispatcher
(GraphQL api.monday.com)     (Google Drive API v3)            (Slack Web API)
         │                              │                              │
         │ - Query Ready Items          │ - Clone Master Spreadsheet   │ - Post Parent Thread
         │ - Update slack_thread_ts     │ - Grant @monks.com Access    │ - Post 3 Nested Replies
         │                              │ - Search Fallback Copy Docs  │
         │                              ▼                              │
         └──────────────────────►  DedupStore  ◄───────────────────────┘
                              (email_flow_dedup.db)
```

---

## Local Dev Runbook

1. **Clone & Enter Workspace**:
   ```bash
   cd /Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation
   ```
2. **Set Up Python Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Configure Environment Secrets**:
   ```bash
   cp .env.example .env
   # Edit .env with your SLACK_BOT_TOKEN and MONDAY_API_TOKEN
   # Ensure credentials.json is placed in the project root
   ```
4. **Execute Unit and Integration Tests**:
   ```bash
   .venv/bin/pytest -v
   ```
5. **Run Application**:
   - *Option 1: Test Demo Run*:
     ```bash
     .venv/bin/python email_flow_handoff_bot.py --demo
     ```
   - *Option 2: Run Poller Dry-Run*:
     ```bash
     .venv/bin/python email_flow_handoff_bot.py --dry-run
     ```
   - *Option 3: Launch Local Webhook Server*:
     ```bash
     .venv/bin/uvicorn webhook_server:app --host 0.0.0.0 --port 8000 --reload
     ```
   - *Option 4: Run Continuous Poller*:
     ```bash
     .venv/bin/python email_flow_handoff_bot.py --watch --interval 60
     ```

---

## Environment Variable Dependency Chain

| Variable | Consumed By | Consequence if Missing or Invalid |
| :--- | :--- | :--- |
| `SLACK_BOT_TOKEN` | [SlackThreadDispatcher](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/slack_dispatcher.py) | Slack operations fail with `SlackApiError: invalid_auth` or unauthorized errors. |
| `SLACK_CHANNEL_ID` | [SlackThreadDispatcher](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/slack_dispatcher.py) | Messages fail to send; Slack API returns `channel_not_found`. |
| `MONDAY_API_TOKEN` | [MondayClient](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/monday_client.py) | Monday GraphQL queries and mutations fail with 401/403 or API authentication error. |
| `MONDAY_API_URL` | [MondayClient](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/monday_client.py) | Defaults to `https://api.monday.com/v2`; if invalid, connection errors occur. |
| `MONDAY_API_VERSION` | [MondayClient](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/monday_client.py) | Defaults to `2023-10`; passed as `API-Version` header. |
| `WATCH_BOARDS` | [EmailFlowOrchestrator](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/email_flow_handoff_bot.py) | Defines boards scanned by poller; defaults to `4209532311,4209567424`. |
| `MONDAY_THREAD_TS_COLUMN`| [MondayClient](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/monday_client.py) | Column ID for writing Slack timestamp; defaults to `slack_thread_ts`. |
| `MASTER_CHECKLIST_TEMPLATE_ID` | [GoogleDriveProvisioner](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/google_drive_client.py) | Drive spreadsheet copy fails (`HttpError 404 / File not found`). |
| `GOOGLE_APPLICATION_CREDENTIALS` | [GoogleDriveProvisioner](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/google_drive_client.py) | Drive client falls back to ADC or mock URLs if not found. |
| `GOOGLE_DRIVE_SHARE_DOMAIN` | [GoogleDriveProvisioner](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/google_drive_client.py) | Defaults to `monks.com`; permissions grant is skipped if empty. |
| `DEDUP_DB_PATH` | [DedupStore](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/dedup_store.py) | Defaults to `email_flow_dedup.db`; invalid path causes `sqlite3.OperationalError`. |
| `POLL_INTERVAL_SECONDS` | [EmailFlowOrchestrator](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/email_flow_handoff_bot.py) | Controls polling sleep duration; defaults to `60` seconds. |
| `GAMMA_BASE_URL` | [EmailFlowOrchestrator](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/email_flow_handoff_bot.py) | Base URL template for Google Gamma links (`{campaign_id}` substitution). |

---

## Domain Glossary

- **Pulse / Item**: Individual task or row in Monday.com representing a marketing email campaign.
- **Email.Flow**: Automated production workflow indicated by specific board checkbox columns (`boolean_mkysmx2k` on Viewers hub, `boolean_mm46ggd2` on Creators hub).
- **QACL (QA Checklist)**: Spreadsheet duplicated from the Master QA Checklist template (`1AQOaskr3VWWl7rCBzMr505uVXBjCBmQ96M_zn7QkJ6I`) named `[EF QACL] <Campaign ID> - <Campaign Name>`.
- **Copy Doc**: Google Doc containing finalized email creative, copy, and layout instructions.
- **Gamma**: Google internal deployment platform for email campaigns (`https://gamma.corp.google.com/index.html#/campaign/{campaign_id}/home`).
- **Jae Hong Format**: Canonical Slack thread structure:
  - Parent message: `*[Thread] {campaign_name}* {mentions}` with required stakeholders (`Huy Bui`, `Jae Hong`, `Julio Arredondo Villafranca`, `Japega Pérez Garcia`, `Rishi Dutta`).
  - Reply 1: `:memo: <{copy_doc_url}|Copy Doc>\n<{gamma_url}|Gamma>`
  - Reply 2: `<{checklist_url}|Checklist>`
  - Reply 3: `Proofs being sent`
- **slack_thread_ts**: Timestamp string identifying a Slack message thread parent, stored both in SQLite and Monday.com to guarantee deduplication.

---

## Data Model Overview

### SQLite Schema (`processed_campaigns`)

Location: `email_flow_dedup.db`
Managed by: [DedupStore](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/dedup_store.py)

```sql
CREATE TABLE IF NOT EXISTS processed_campaigns (
    item_id TEXT PRIMARY KEY,
    campaign_id TEXT NOT NULL,
    campaign_name TEXT NOT NULL,
    slack_thread_ts TEXT NOT NULL,
    checklist_url TEXT,
    created_at TIMESTAMP NOT NULL
);
```

- **`item_id`** (TEXT PRIMARY KEY): Unique Monday.com pulse / item identifier.
- **`campaign_id`** (TEXT NOT NULL): Extracted 5-digit campaign ID (or fallback item ID).
- **`campaign_name`** (TEXT NOT NULL): Full campaign title as recorded on Monday.
- **`slack_thread_ts`** (TEXT NOT NULL): Slack parent message timestamp ID (`ts`).
- **`checklist_url`** (TEXT): Direct URL to the cloned Google Sheet QA Checklist.
- **`created_at`** (TIMESTAMP NOT NULL): UTC ISO8601 timestamp recording when handoff occurred.

---

## Stakeholder Directory

Directory mapping between Monday.com user identities and Slack member IDs defined in [config.py](file:///Users/rdutta/.gemini/antigravity/scratch/email-flow-qa-automation/config.py):

| Team Member | Role | Monday User ID | Slack Member ID | Mention Syntax |
| :--- | :--- | :--- | :--- | :--- |
| **Huy Bui** | Lead Dev | `41011989` | `U01QH0F3DK8` | `*<@U01QH0F3DK8\|Huy Bui>*` |
| **Jae Hong** | Project Lead / PM | `73974758` | `U99HT1DCN` | `*<@U99HT1DCN\|Jae Hong>*` |
| **Julio Arredondo Villafranca** | QA Engineer | `41012035` | `US0H7JFNZ` | `*<@US0H7JFNZ\|Julio Arredondo Villafranca>*` |
| **Japega Pérez Garcia** | QA Specialist | `75954679` | `UUXPU1F7W` | `*<@UUXPU1F7W\|Japega Pérez Garcia>*` |
| **Rishi Dutta** | QA Automation Lead | `116473469` | `U0BMA4L3XUG` | `*<@U0BMA4L3XUG\|Rishi Dutta>*` |
| **Nikita Birmi** | QA / Delivery Lead | `111721785` | `U02T49WH05B` | `*<@U02T49WH05B\|Nikita Birmi>*` |
