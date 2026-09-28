# Email.Flow QA Slack Automation

Enterprise automation system connecting **Monday.com** campaign tracking boards, **Google Drive** assets, **Gamma** email deployment URLs, and **Slack** team communication channels.

Based on the *Email.Flow QA Handoff Automation Specification* by **Rishi Dutta** (MediaMonks Marketing Technology).

---

## 1. System Architecture & Workflow

```
┌──────────────────────────────────────────────┐
│ Monday.com Project Boards                    │
│ - Viewers Project Hub (Board ID: 4209532311) │
│ - Creators Project Hub (Board ID: 4209567424)│
│ (Trigger: Stage -> "Needs QA")               │
└──────────────────────┬───────────────────────┘
                       │ Webhook / Scheduled Poller
                       ▼
┌──────────────────────────────────────────────┐
│ Email Flow Orchestrator                      │
│ (Python Automation Worker)                   │
└──────────────┬───────────────────────────────┘
               │
       ┌───────┴────────────────────────┐
       │ 1. Clone                       │ 2. Post Thread & Replies
       ▼                                ▼
┌──────────────────────────────┐ ┌──────────────────────────────────────────────┐
│ Google Drive                 │ │ Slack Channel                                │
│ Master QACL Template         │ │ #C0ANGFFEFS8                                 │
│ (1AQOaskr3VWW...QkJ6I)       │ │ Parent: *[Thread] 26835 - YTV [Email]...*    │
│                              │ │ ├─ Reply 1: 📝 Copy Doc + Gamma URL          │
│ Target Title:                │ │ ├─ Reply 2: 📊 [EF QACL] Checklist Link      │
│ [EF QACL] <ID> - <Name>      │ │ └─ Reply 3: Proofs being sent                │
└──────────────────────────────┘ └──────────────────────────────────────────────┘
```

---

## 2. Key Features

1. **Dual Execution Modes**:
   - **Scheduled Poller** (`email_flow_handoff_bot.py`): Periodically queries Monday GraphQL API for candidate items entering QA.
   - **Real-Time Webhook Receiver** (`webhook_server.py`): FastAPI listener handling Monday challenge handshake and triggering sub-second handoffs via background tasks.
2. **Canonical Slack Thread Structure (Jae Hong Format)**:
   - **Parent Message**: `*[Thread] {campaign_name}* {mentions}` with required stakeholders automatically tagged (`<@USER_ID|Name>`).
   - **Reply 1**: `:memo: <{copy_doc_url}|Copy Doc>\n<{gamma_url}|Gamma>`
   - **Reply 2**: `<{checklist_url}|Checklist>`
   - **Reply 3**: `Proofs being sent`
3. **Google Drive Provisioning & Access Management**:
   - Clones canonical template: `1AQOaskr3VWWl7rCBzMr505uVXBjCBmQ96M_zn7QkJ6I`.
   - Names output spreadsheet: `[EF QACL] <Campaign ID> - <Campaign Name>`.
   - Embeds metadata properties: `{"campaign_id": "<id>", "managed_by": "email_flow_bot"}`.
   - Automatically grants read/write permissions to `@monks.com` domain or assignees.
4. **Operational Safeguards**:
   - **Deduplication Guard**: Prevents duplicate thread posts when users toggle Monday statuses using persistent SQLite cache (`email_flow_dedup.db`) and writing thread timestamp back to Monday column `slack_thread_ts`.
   - **MIME & Fallback Handling**: If Monday Doc column is empty, automatically searches Google Drive for `[Copy Doc] <Campaign ID>` before falling back to default doc with alert.

---

## 3. Directory Mapping & Stakeholders

| Team Member | Role | Monday User ID | Slack Member ID | Mention Syntax |
| :--- | :--- | :--- | :--- | :--- |
| **Huy Bui** | Lead Dev | `41011989` | `U01QH0F3DK8` | `<@U01QH0F3DK8\|Huy Bui>` |
| **Jae Hong** | Project Lead / PM | `73974758` | `U99HT1DCN` | `<@U99HT1DCN\|Jae Hong>` |
| **Julio Arredondo Villafranca** | QA Engineer | `41012035` | `US0H7JFNZ` | `<@US0H7JFNZ\|Julio Arredondo Villafranca>` |
| **Japega Pérez Garcia** | QA Specialist | `75954679` | `UUXPU1F7W` | `<@UUXPU1F7W\|Japega Pérez Garcia>` |
| **Rishi Dutta** | QA Automation Lead | `116473469` | `U0BMA4L3XUG` | `<@U0BMA4L3XUG\|Rishi Dutta>` |
| **Nikita Birmi** | QA / Delivery Lead | `111721785` | `U02T49WH05B` | `<@U02T49WH05B\|Nikita Birmi>` |

---

## 4. Monday.com Ingestion Schema

- **Monitored Boards**:
  - `4209532311`: Viewers Project Hub
  - `4209567424`: Creators Project Hub
  - `38880065`: Email.Flow Overview
- **Trigger Conditions**:
  1. `boolean_mkysmx2k` (Viewers) or `boolean_mm46ggd2` (Creators) is Checked (`true` or `"v"`).
  2. Stage (`label3` / `status`) contains:
     - `Needs QA - Everything approved`
     - `QA in progress`
     - `Needs QA - content not finalized`
  3. Item has not already generated a thread (no `slack_thread_ts` and not present in SQLite store).

---

## 5. Installation & Setup

### Prerequisites
- Python 3.10+
- Slack Bot with scopes: `chat:write`, `links:write`, `chat:write.public`
- Monday.com API v2 Token
- Google Cloud Service Account with Google Drive API enabled

### Quickstart

1. **Activate Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Fill in your tokens:
   - `SLACK_BOT_TOKEN=xoxb-...`
   - `SLACK_CHANNEL_ID=C0ANGFFEFS8`
   - `MONDAY_API_TOKEN=...`
   - Place your Google Service Account JSON at `credentials.json`.

---

## 6. Execution Modes

### A. Run Single Polling Cycle (CLI)
```bash
.venv/bin/python email_flow_handoff_bot.py
```

### B. Dry-Run Simulation (No external side-effects)
```bash
.venv/bin/python email_flow_handoff_bot.py --dry-run
```

### C. Continuous Poller Mode
```bash
.venv/bin/python email_flow_handoff_bot.py --watch --interval 60
```

### D. Single Pulse / Item Test
```bash
.venv/bin/python email_flow_handoff_bot.py --pulse 12345678 --dry-run
```

### E. FastAPI Webhook Server (Real-Time Handshake)
```bash
.venv/bin/python webhook_server.py
# Or with uvicorn directly:
.venv/bin/uvicorn webhook_server:app --host 0.0.0.0 --port 8000 --reload
```
Endpoint available at: `POST /webhook/monday`

---

## 7. Running Tests

Run the full pytest suite with 100% passing tests:
```bash
.venv/bin/pytest -v
```

Tests verify:
- Parsing of Monday checkboxes, statuses, and assignees.
- Master checklist duplication, permissions, and copy doc fallback.
- Exact Slack Jae Hong canonical thread structure and mentions.
- SQLite deduplication persistence across restarts.
- Monday webhook challenge handshake and column event filtering.
