"""
Slack Thread Dispatcher for Email.Flow QA Handoff Automation.
Posts the canonical Jae Hong handoff thread and sequential replies.
"""

import logging
from typing import List, Optional, Dict, Any
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from config import (
    SLACK_BOT_TOKEN,
    SLACK_CHANNEL_ID,
    SLACK_USER_DIRECTORY,
    REQUIRED_STAKEHOLDERS,
)

logger = logging.getLogger(__name__)


class SlackThreadDispatcher:
    def __init__(
        self,
        token: Optional[str] = None,
        channel_id: Optional[str] = None,
        dry_run: bool = False,
    ):
        self.token = token or SLACK_BOT_TOKEN
        self.channel_id = channel_id or SLACK_CHANNEL_ID
        self.dry_run = dry_run
        self.client = WebClient(token=self.token) if not dry_run else None

    def build_parent_mentions(self, assignees: List[str]) -> str:
        """
        Builds the user mentions string adhering to Jae Hong's canonical format.
        Ensures default QA leads and stakeholders are included.
        Format: *<@USER_ID|Name>*
        """
        mentions = []
        # Ensure default QA leads and stakeholders are included
        all_people = list(dict.fromkeys(assignees + REQUIRED_STAKEHOLDERS))

        for person in all_people:
            # Check directory by exact name
            if person in SLACK_USER_DIRECTORY:
                u_info = SLACK_USER_DIRECTORY[person]
                mentions.append(f"*<@{u_info['slack_id']}|{u_info['name']}>*")
            else:
                # Check case-insensitively or partial matches
                matched = False
                for name, u_info in SLACK_USER_DIRECTORY.items():
                    if name.lower() == person.lower() or person.lower() in name.lower():
                        mentions.append(f"*<@{u_info['slack_id']}|{u_info['name']}>*")
                        matched = True
                        break
                if not matched:
                    mentions.append(f"*{person}*")

        return " ".join(mentions)

    def dispatch_qa_handoff(
        self,
        campaign_name: str,
        campaign_id: str,
        assignees: List[str],
        copy_doc_url: str,
        gamma_url: str,
        checklist_url: str,
        has_doc_alert: bool = False,
    ) -> str:
        """
        Dispatches the canonical Jae Hong Slack handoff thread.

        1. Parent Message:
           *[Thread] {campaign_name}* {mentions_str}
        2. Reply 1:
           :memo: <{copy_doc_url}|Copy Doc>\n<{gamma_url}|Gamma>
        3. Reply 2:
           <{checklist_url}|Checklist>
        4. Reply 3:
           Proofs being sent
        """
        mentions_str = self.build_parent_mentions(assignees)
        alert_tag = " :warning: *[Alert: Missing Copy Doc - Verification Required]*" if has_doc_alert else ""
        parent_text = f"*[Thread] {campaign_name}*{alert_tag} {mentions_str}".strip()

        if self.dry_run or not self.client:
            logger.info(
                f"[DRY RUN] Slack Thread Dispatcher for '{campaign_name}' (ID: {campaign_id})"
            )
            logger.info(f"[DRY RUN] Channel: {self.channel_id}")
            logger.info(f"[DRY RUN] Parent: {parent_text}")
            logger.info(f"[DRY RUN] Reply 1: :memo: <{copy_doc_url}|Copy Doc>\n<{gamma_url}|Gamma>")
            logger.info(f"[DRY RUN] Reply 2: <{checklist_url}|Checklist>")
            logger.info(f"[DRY RUN] Reply 3: Proofs being sent")
            return f"dry_run_ts_{campaign_id}"

        try:
            # Step 1: Parent Message
            parent_res = self.client.chat_postMessage(
                channel=self.channel_id,
                text=parent_text,
                unfurl_links=False,
                unfurl_media=False,
            )
            thread_ts = parent_res["ts"]
            logger.info(f"Dispatched Slack thread parent: ts={thread_ts}")

            # Step 2: Reply 1 - Copy Doc & Gamma links
            reply1_text = f":memo: <{copy_doc_url}|Copy Doc>\n<{gamma_url}|Gamma>"
            self.client.chat_postMessage(
                channel=self.channel_id,
                thread_ts=thread_ts,
                text=reply1_text,
                unfurl_links=True,
            )

            # Step 3: Reply 2 - QA Checklist
            reply2_text = f"<{checklist_url}|Checklist>"
            self.client.chat_postMessage(
                channel=self.channel_id,
                thread_ts=thread_ts,
                text=reply2_text,
                unfurl_links=True,
            )

            # Step 4: Reply 3 - Proof Status
            reply3_text = "Proofs being sent"
            self.client.chat_postMessage(
                channel=self.channel_id,
                thread_ts=thread_ts,
                text=reply3_text,
            )

            return thread_ts

        except SlackApiError as e:
            logger.error(f"Error posting to Slack: {e.response.get('error', e)}")
            raise
