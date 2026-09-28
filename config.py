"""
Configuration module for Email.Flow QA Handoff Automation.
Contains credentials, board IDs, column mappings, and user directories.
"""

import os
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# ==========================================
# CREDENTIALS & API CONFIGURATION
# ==========================================
SLACK_BOT_TOKEN: str = os.getenv("SLACK_BOT_TOKEN", "xoxb-your-bot-token")
SLACK_CHANNEL_ID: str = os.getenv("SLACK_CHANNEL_ID", "C0ANGFFEFS8")
MONDAY_API_TOKEN: str = os.getenv("MONDAY_API_TOKEN", "your-monday-token")
MONDAY_API_URL: str = os.getenv("MONDAY_API_URL", "https://api.monday.com/v2")
MONDAY_API_VERSION: str = os.getenv("MONDAY_API_VERSION", "2023-10")

# Google Drive Configuration
MASTER_CHECKLIST_TEMPLATE_ID: str = os.getenv(
    "MASTER_CHECKLIST_TEMPLATE_ID", "1AQOaskr3VWWl7rCBzMr505uVXBjCBmQ96M_zn7QkJ6I"
)
GOOGLE_CREDENTIALS_FILE: str = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS", "credentials.json"
)
GOOGLE_DRIVE_SHARE_DOMAIN: str = os.getenv("GOOGLE_DRIVE_SHARE_DOMAIN", "monks.com")

# Local Storage / Deduplication
DEDUP_DB_PATH: str = os.getenv("DEDUP_DB_PATH", "email_flow_dedup.db")
POLL_INTERVAL_SECONDS: int = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))

# Gamma URL Base
GAMMA_BASE_URL: str = os.getenv(
    "GAMMA_BASE_URL", "https://gamma.corp.google.com/index.html#/campaign/{campaign_id}/home"
)

# ==========================================
# BOARDS TO MONITOR
# ==========================================
# Viewers Project Hub (4209532311), Creators Project Hub (4209567424), Email.Flow Overview (38880065)
WATCH_BOARDS: List[int] = [
    int(bid.strip())
    for bid in os.getenv("WATCH_BOARDS", "4209532311,4209567424").split(",")
    if bid.strip()
]

# ==========================================
# MONDAY COLUMN IDENTIFIERS & TRIGGER RULES
# ==========================================
EMAIL_FLOW_CHECKBOX_KEYS: List[str] = [
    "boolean_mkysmx2k",  # Viewers Project Hub
    "boolean_mm46ggd2",  # Creators Project Hub
]

STAGE_COLUMN_KEYS: List[str] = ["label3", "status"]

ASSIGNEE_COLUMN_KEYS: List[str] = ["person", "people0", "people7"]

DOC_COLUMN_KEYS: List[str] = ["monday_doc"]

PRODUCT_AREA_KEYS: List[str] = ["label7", "ytc_product_area"]

# Monday column ID used to store the Slack Thread TS for deduplication / traceability
SLACK_THREAD_TS_COLUMN: str = os.getenv("MONDAY_THREAD_TS_COLUMN", "slack_thread_ts")

QUALIFYING_QA_STAGES: List[str] = [
    "Needs QA - Everything approved",
    "QA in progress",
    "Needs QA - content not finalized",
]

# ==========================================
# TEAM MEMBER DIRECTORY MAPPING
# ==========================================
# Maps Monday User Name / Monday ID -> Slack Member Details
SLACK_USER_DIRECTORY: Dict[str, Dict[str, str]] = {
    "Huy Bui": {
        "slack_id": "U01QH0F3DK8",
        "name": "Huy Bui",
        "monday_id": "41011989",
        "role": "Lead Dev",
    },
    "Jae Hong": {
        "slack_id": "U99HT1DCN",
        "name": "Jae Hong",
        "monday_id": "73974758",
        "role": "Project Lead / PM",
    },
    "Julio Arredondo Villafranca": {
        "slack_id": "US0H7JFNZ",
        "name": "Julio Arredondo Villafranca",
        "monday_id": "41012035",
        "role": "QA Engineer",
    },
    "Japega Pérez Garcia": {
        "slack_id": "UUXPU1F7W",
        "name": "Japega Pérez Garcia",
        "monday_id": "75954679",
        "role": "QA Specialist",
    },
    "Rishi Dutta": {
        "slack_id": "U0BMA4L3XUG",
        "name": "Rishi Dutta",
        "monday_id": "116473469",
        "role": "QA Automation Lead",
    },
    "Nikita Birmi": {
        "slack_id": "U02T49WH05B",
        "name": "Nikita Birmi",
        "monday_id": "111721785",
        "role": "QA / Delivery Lead",
    },
}

# Reverse lookup by Monday User ID
MONDAY_ID_TO_USER: Dict[str, Dict[str, str]] = {
    v["monday_id"]: v for v in SLACK_USER_DIRECTORY.values()
}

# Default required stakeholders that must always be included in the parent thread mention
REQUIRED_STAKEHOLDERS: List[str] = [
    "Huy Bui",
    "Jae Hong",
    "Julio Arredondo Villafranca",
    "Japega Pérez Garcia",
    "Rishi Dutta",
]
