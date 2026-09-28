"""
Email.Flow QA Handoff Automation
Author: Rishi Dutta
Monks - MediaMonks Marketing Technology

Description:
Polls Monday.com for campaigns marked for Email.Flow entering 'Needs QA',
duplicates the master QA checklist on Google Drive, and creates the standardized
Slack handoff thread with copy docs, checklist, and Gamma URLs.
"""

import argparse
import logging
import os
import re
import sys
import time
from typing import Dict, Any, List, Optional

from config import (
    SLACK_BOT_TOKEN,
    SLACK_CHANNEL_ID,
    MONDAY_API_TOKEN,
    WATCH_BOARDS,
    MASTER_CHECKLIST_TEMPLATE_ID,
    GOOGLE_CREDENTIALS_FILE,
    DEDUP_DB_PATH,
    POLL_INTERVAL_SECONDS,
    GAMMA_BASE_URL,
)
from dedup_store import DedupStore
from google_drive_client import GoogleDriveProvisioner
from monday_client import MondayClient
from slack_dispatcher import SlackThreadDispatcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("EmailFlowAutomation")


class EmailFlowOrchestrator:
    def __init__(
        self,
        monday_token: Optional[str] = None,
        slack_token: Optional[str] = None,
        slack_channel: Optional[str] = None,
        google_creds_path: Optional[str] = None,
        template_id: str = MASTER_CHECKLIST_TEMPLATE_ID,
        db_path: str = DEDUP_DB_PATH,
        dry_run: bool = False,
    ):
        self.dry_run = dry_run
        self.monday = MondayClient(api_token=monday_token or MONDAY_API_TOKEN)
        self.drive = GoogleDriveProvisioner(
            credentials_path=google_creds_path or GOOGLE_CREDENTIALS_FILE,
            template_id=template_id,
        )
        self.slack = SlackThreadDispatcher(
            token=slack_token or SLACK_BOT_TOKEN,
            channel_id=slack_channel or SLACK_CHANNEL_ID,
            dry_run=dry_run,
        )
        self.dedup_store = DedupStore(db_path=db_path)

    def process_item(
        self, item: Dict[str, Any], board_id: Optional[int] = None
    ) -> Optional[str]:
        """
        Orchestrates QA handoff for an individual candidate item.
        Performs deduplication check, asset resolution, checklist cloning,
        Slack posting, and status writeback.
        """
        item_id = str(item["id"])
        c_name = item["name"]

        # Deduplication Guard 1: Local persistent DB check
        if self.dedup_store.is_processed(item_id):
            logger.info(
                f"[Dedup Guard] Item {item_id} ('{c_name}') has already been processed in SQLite cache. Skipping."
            )
            return None

        # Deduplication Guard 2: Monday column check
        if item.get("slack_thread_ts"):
            logger.info(
                f"[Dedup Guard] Item {item_id} already has Slack thread TS '{item['slack_thread_ts']}' on Monday. Skipping."
            )
            return None

        # Verify eligibility
        if not self.monday._is_eligible_for_qa_thread(item):
            logger.info(
                f"Item {item_id} ('{c_name}') is not currently eligible for QA handoff (stage: '{item.get('stage')}', email_flow: {item.get('is_email_flow')})."
            )
            return None

        # 1. Resolve Campaign ID via regex r"^(\d{5})"
        c_match = re.match(r"^(\d{5})", c_name)
        campaign_id = c_match.group(1) if c_match else item_id
        logger.info(f"Processing candidate item: {c_name} (Campaign ID: {campaign_id})")

        # 2. Resolve Copy Doc (Section 6.9 Safeguard)
        has_doc_alert = False
        if item.get("doc_links"):
            copy_doc = item["doc_links"][0]
            logger.info(f"Resolved Copy Doc from Monday doc column: {copy_doc}")
        else:
            logger.info(
                f"No Copy Doc in Monday doc column. Searching Drive fallback for [Copy Doc] {campaign_id}..."
            )
            fallback_doc = self.drive.find_copy_doc_fallback(campaign_id)
            if fallback_doc:
                copy_doc = fallback_doc
                logger.info(f"Resolved Copy Doc from Google Drive fallback: {copy_doc}")
            else:
                copy_doc = (
                    f"https://docs.google.com/document/d/default-copy-{campaign_id}/edit"
                )
                has_doc_alert = True
                logger.warning(
                    f"No Copy Doc found on Monday or Drive for campaign {campaign_id}. Flagging alert."
                )

        # 3. Derive Gamma Campaign URL
        gamma_url = GAMMA_BASE_URL.format(campaign_id=campaign_id)

        # 4. Provision Fresh QA Checklist from Master Template (Section 1 & 6.8)
        checklist_url = self.drive.duplicate_qa_checklist(campaign_id, c_name)

        # 5. Post Canonical Jae Hong Slack Thread (Section 3)
        thread_ts = self.slack.dispatch_qa_handoff(
            campaign_name=c_name,
            campaign_id=campaign_id,
            assignees=item.get("assignees", []),
            copy_doc_url=copy_doc,
            gamma_url=gamma_url,
            checklist_url=checklist_url,
            has_doc_alert=has_doc_alert,
        )

        # 6. Record in SQLite Deduplication Store (Section 6.7)
        self.dedup_store.record_success(
            item_id=item_id,
            campaign_id=campaign_id,
            campaign_name=c_name,
            slack_thread_ts=thread_ts,
            checklist_url=checklist_url,
        )

        # 7. Write Thread TS back to Monday.com column (Section 6.7)
        target_board = board_id or item.get("board_id")
        if target_board and not self.dry_run:
            self.monday.write_slack_thread_ts(
                board_id=target_board, item_id=item_id, thread_ts=thread_ts
            )

        logger.info(
            f"Successfully completed QA handoff for campaign {campaign_id}! Slack thread ts: {thread_ts}"
        )
        return thread_ts

    def run_automation_cycle(
        self, boards: Optional[List[int]] = None
    ) -> List[str]:
        """
        Executes a single polling cycle across all target boards.
        """
        logger.info("Starting Email.Flow QA Handoff Automation cycle...")
        target_boards = boards or WATCH_BOARDS
        dispatched_threads: List[str] = []

        for board_id in target_boards:
            logger.info(f"Inspecting Board ID: {board_id}")
            try:
                items = self.monday.fetch_email_flow_qa_ready_items(board_id)
                logger.info(f"Found {len(items)} ready item(s) on Board {board_id}")
                for item in items:
                    ts = self.process_item(item, board_id=board_id)
                    if ts:
                        dispatched_threads.append(ts)
            except Exception as e:
                logger.error(f"Error inspecting board {board_id}: {e}", exc_info=True)

        logger.info(
            f"Completed automation cycle. Total threads dispatched: {len(dispatched_threads)}"
        )
        return dispatched_threads

    def run_continuous(
        self, interval_seconds: int = POLL_INTERVAL_SECONDS, boards: Optional[List[int]] = None
    ) -> None:
        """
        Runs the orchestrator continuously as a scheduled poller.
        """
        logger.info(
            f"Starting continuous poller with interval={interval_seconds}s across boards: {boards or WATCH_BOARDS}"
        )
        while True:
            try:
                self.run_automation_cycle(boards=boards)
            except Exception as e:
                logger.error(f"Unhandled error in polling cycle: {e}", exc_info=True)
            time.sleep(interval_seconds)


def run_automation_cycle() -> None:
    """Convenience top-level function matching specification in Section 4."""
    orchestrator = EmailFlowOrchestrator()
    orchestrator.run_automation_cycle()


def main():
    parser = argparse.ArgumentParser(
        description="Email.Flow QA Handoff Automation Worker"
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Run continuously in scheduled poller mode",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=POLL_INTERVAL_SECONDS,
        help=f"Polling interval in seconds (default: {POLL_INTERVAL_SECONDS})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate run without modifying Slack, Drive, or Monday",
    )
    parser.add_argument(
        "--pulse",
        type=str,
        help="Process a specific Monday item (pulse ID) directly",
    )
    parser.add_argument(
        "--board",
        type=int,
        action="append",
        help="Specific Monday board ID(s) to inspect (can specify multiple)",
    )

    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a demonstration using realistic sample Monday campaign data",
    )

    args = parser.parse_args()

    orchestrator = EmailFlowOrchestrator(dry_run=args.dry_run or args.demo)

    if args.demo:
        logger.info("Running Email.Flow Automation in DEMO mode with realistic sample item...")
        mock_sample_item = {
            "id": "12345678",
            "name": "26835 - YTV [Email] - Member Newsletter #19 (10/9)",
            "board_id": 4209532311,
            "is_email_flow": True,
            "stage": "Needs QA - Everything approved",
            "product_area": "YTV",
            "assignees": ["Huy Bui", "Jae Hong"],
            "doc_links": [
                "https://docs.google.com/document/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit"
            ],
            "slack_thread_ts": None,
        }
        res = orchestrator.process_item(mock_sample_item, board_id=4209532311)
        logger.info(f"[DEMO RESULT] Dispatched Thread TS: {res}")
        logger.info("[DEMO RESULT] SQLite Database Records:")
        for r in orchestrator.dedup_store.list_processed(limit=5):
            logger.info(f"  -> {r}")
    elif args.pulse:
        logger.info(f"Manually processing pulse ID: {args.pulse}")
        item = orchestrator.monday.fetch_single_item(args.pulse)
        if not item:
            logger.error(f"Pulse ID {args.pulse} not found on Monday.com.")
            sys.exit(1)
        res = orchestrator.process_item(item, board_id=item.get("board_id"))
        if res:
            logger.info(f"Pulse {args.pulse} processed successfully. Thread ts: {res}")
        else:
            logger.info(f"Pulse {args.pulse} was not processed (not eligible or duplicate).")
    elif args.watch:
        orchestrator.run_continuous(interval_seconds=args.interval, boards=args.board)
    else:
        orchestrator.run_automation_cycle(boards=args.board)


if __name__ == "__main__":
    main()
