"""
Monday.com API Client for Email.Flow QA Handoff Automation.
Handles item polling, pulse queries, field parsing, and thread timestamp writeback.
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional
import requests

from config import (
    MONDAY_API_URL,
    MONDAY_API_VERSION,
    EMAIL_FLOW_CHECKBOX_KEYS,
    STAGE_COLUMN_KEYS,
    ASSIGNEE_COLUMN_KEYS,
    DOC_COLUMN_KEYS,
    PRODUCT_AREA_KEYS,
    SLACK_THREAD_TS_COLUMN,
    QUALIFYING_QA_STAGES,
    MONDAY_ID_TO_USER,
)

logger = logging.getLogger(__name__)


class MondayClient:
    def __init__(
        self,
        api_token: str,
        api_url: str = MONDAY_API_URL,
        api_version: str = MONDAY_API_VERSION,
    ):
        self.api_token = api_token
        self.api_url = api_url
        self.headers = {
            "Authorization": api_token,
            "Content-Type": "application/json",
            "API-Version": api_version,
        }

    def query(
        self, query: str, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Executes a GraphQL query against the Monday.com v2 API."""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = requests.post(
            self.api_url, headers=self.headers, json=payload, timeout=30
        )
        response.raise_for_status()
        res_json = response.json()

        if "errors" in res_json:
            raise RuntimeError(f"Monday API Error: {res_json['errors']}")

        return res_json.get("data", {})

    def fetch_email_flow_qa_ready_items(self, board_id: int) -> List[Dict[str, Any]]:
        """
        Fetches items from a board where Email.Flow is enabled and status is ready for QA.
        """
        graphql_query = """
        query GetBoardItems($boardId: [ID!]) {
          boards(ids: $boardId) {
            id
            name
            items_page(limit: 50) {
              items {
                id
                name
                column_values {
                  id
                  text
                  value
                  type
                }
              }
            }
          }
        }
        """
        data = self.query(graphql_query, {"boardId": [str(board_id)]})
        boards = data.get("boards", [])
        if not boards:
            logger.warning(f"No board found with ID: {board_id}")
            return []

        ready_items = []
        for item in boards[0].get("items_page", {}).get("items", []):
            parsed_item = self._parse_item_fields(item, board_id=board_id)
            if self._is_eligible_for_qa_thread(parsed_item):
                ready_items.append(parsed_item)

        return ready_items

    def fetch_single_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetches and parses a single item by ID (used for Webhook pulse processing).
        """
        graphql_query = """
        query GetItem($itemId: [ID!]) {
          items(ids: $itemId) {
            id
            name
            board {
              id
            }
            column_values {
              id
              text
              value
              type
            }
          }
        }
        """
        data = self.query(graphql_query, {"itemId": [str(item_id)]})
        items = data.get("items", [])
        if not items:
            logger.warning(f"No item found for ID: {item_id}")
            return None

        item = items[0]
        board_id = int(item["board"]["id"]) if "board" in item and item["board"] else None
        return self._parse_item_fields(item, board_id=board_id)

    def _parse_item_fields(
        self, item: Dict[str, Any], board_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Extracts and normalizes fields from Monday.com column values.
        """
        raw_values = {col["id"]: col for col in item.get("column_values", [])}

        # 1. Checkbox column check (boolean_mkysmx2k or boolean_mm46ggd2)
        is_email_flow = False
        for bool_key in EMAIL_FLOW_CHECKBOX_KEYS:
            if bool_key in raw_values:
                col = raw_values[bool_key]
                val = col.get("value")
                text = (col.get("text") or "").strip().lower()
                if val:
                    try:
                        val_json = json.loads(val)
                        if isinstance(val_json, dict) and (
                            val_json.get("checked") is True
                            or str(val_json.get("checked", "")).lower() == "true"
                        ):
                            is_email_flow = True
                    except Exception:
                        pass
                if text in ["v", "true", "checked", "yes"]:
                    is_email_flow = True

        # 2. Stage / Status check
        stage_text = ""
        for stage_key in STAGE_COLUMN_KEYS:
            if stage_key in raw_values and raw_values[stage_key].get("text"):
                stage_text = raw_values[stage_key].get("text")
                break

        # 3. Assignees extraction
        assignees = []
        for person_key in ASSIGNEE_COLUMN_KEYS:
            if person_key in raw_values:
                col = raw_values[person_key]
                # Extract by text representation (names separated by commas)
                if col.get("text"):
                    names = [n.strip() for n in col["text"].split(",") if n.strip()]
                    assignees.extend(names)
                # Also extract by person IDs in JSON value if available
                if col.get("value"):
                    try:
                        p_val = json.loads(col["value"])
                        persons_list = p_val.get("personsAndTeams", [])
                        for p in persons_list:
                            pid = str(p.get("id"))
                            if pid in MONDAY_ID_TO_USER:
                                assignees.append(MONDAY_ID_TO_USER[pid]["name"])
                    except Exception:
                        pass

        # 4. Doc / Link extraction
        doc_links = []
        for doc_key in DOC_COLUMN_KEYS:
            if doc_key in raw_values and raw_values[doc_key].get("value"):
                try:
                    doc_val = json.loads(raw_values[doc_key]["value"])
                    if "files" in doc_val and isinstance(doc_val["files"], list):
                        for f in doc_val["files"]:
                            if "linkToFile" in f:
                                doc_links.append(f["linkToFile"])
                            elif "url" in f:
                                doc_links.append(f["url"])
                    elif "url" in doc_val:
                        doc_links.append(doc_val["url"])
                except Exception:
                    pass
            # Also check text value for direct URLs
            if doc_key in raw_values and raw_values[doc_key].get("text"):
                txt = raw_values[doc_key]["text"].strip()
                if txt.startswith("http://") or txt.startswith("https://"):
                    doc_links.append(txt)

        # 5. Product Area
        product_area = ""
        for p_key in PRODUCT_AREA_KEYS:
            if p_key in raw_values and raw_values[p_key].get("text"):
                product_area = raw_values[p_key].get("text")
                break

        # 6. Check for existing Slack Thread TS on Monday item
        slack_thread_ts = None
        if SLACK_THREAD_TS_COLUMN in raw_values and raw_values[SLACK_THREAD_TS_COLUMN].get("text"):
            slack_thread_ts = raw_values[SLACK_THREAD_TS_COLUMN]["text"].strip()

        # 7. Extract Campaign ID via regex r"^(\d{5})"
        item_name = item.get("name", "")
        c_match = re.match(r"^(\d{5})", item_name)
        campaign_id = c_match.group(1) if c_match else str(item["id"])

        return {
            "id": str(item["id"]),
            "name": item_name,
            "campaign_id": campaign_id,
            "board_id": board_id,
            "is_email_flow": is_email_flow,
            "stage": stage_text,
            "product_area": product_area,
            "assignees": list(dict.fromkeys(assignees)),  # preserve order & unique
            "doc_links": doc_links,
            "slack_thread_ts": slack_thread_ts,
        }

    def _is_eligible_for_qa_thread(self, parsed: Dict[str, Any]) -> bool:
        """
        Determines whether the parsed Monday item meets trigger criteria:
        1. Email.Flow is enabled (checkbox true).
        2. Stage is in qualifying QA stages.
        3. Has not already posted a thread (tracked via slack_thread_ts).
        """
        if not parsed["is_email_flow"]:
            return False

        if parsed.get("slack_thread_ts"):
            # Already has a thread timestamp written to Monday
            return False

        item_stage = (parsed.get("stage") or "").lower()
        return any(stage.lower() in item_stage for stage in QUALIFYING_QA_STAGES)

    def write_slack_thread_ts(
        self, board_id: int, item_id: str, thread_ts: str, column_id: str = SLACK_THREAD_TS_COLUMN
    ) -> bool:
        """
        Writes the Slack thread timestamp back to Monday.com for tracking and deduplication.
        """
        mutation = """
        mutation UpdateThreadTs($boardId: ID!, $itemId: ID!, $columnId: String!, $value: String!) {
          change_simple_column_value(board_id: $boardId, item_id: $itemId, column_id: $columnId, value: $value) {
            id
          }
        }
        """
        try:
            self.query(
                mutation,
                {
                    "boardId": str(board_id),
                    "itemId": str(item_id),
                    "columnId": column_id,
                    "value": str(thread_ts),
                },
            )
            logger.info(
                f"Successfully wrote slack_thread_ts={thread_ts} to Monday item {item_id}"
            )
            return True
        except Exception as e:
            logger.warning(
                f"Could not write thread_ts back to Monday column '{column_id}' on item {item_id}: {e}"
            )
            return False
