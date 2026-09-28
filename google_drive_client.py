"""
Google Drive Provisioner for Email.Flow QA Handoff Automation.
Handles QA Checklist cloning, permission grants, and Copy Doc fallback searches.
"""

import os
import logging
from typing import Optional, List, Dict, Any

from google.oauth2 import service_account
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import (
    MASTER_CHECKLIST_TEMPLATE_ID,
    GOOGLE_CREDENTIALS_FILE,
    GOOGLE_DRIVE_SHARE_DOMAIN,
)

logger = logging.getLogger(__name__)


class GoogleDriveProvisioner:
    def __init__(
        self,
        credentials_path: Optional[str] = None,
        template_id: str = MASTER_CHECKLIST_TEMPLATE_ID,
        share_domain: str = GOOGLE_DRIVE_SHARE_DOMAIN,
    ):
        self.template_id = template_id
        self.share_domain = share_domain
        self.credentials_path = credentials_path or GOOGLE_CREDENTIALS_FILE
        self.scopes = ["https://www.googleapis.com/auth/drive"]
        self.drive_service = self._init_drive_service()

    def _init_drive_service(self):
        """Initializes Google Drive v3 client via service account or default credentials."""
        creds = None
        if self.credentials_path and os.path.exists(self.credentials_path):
            try:
                creds = service_account.Credentials.from_service_account_file(
                    self.credentials_path, scopes=self.scopes
                )
                logger.info(
                    f"Initialized Google Drive credentials from {self.credentials_path}"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to load service account file {self.credentials_path}: {e}"
                )

        if not creds:
            try:
                creds, _ = google.auth.default(scopes=self.scopes)
                logger.info("Initialized Google Drive client using Application Default Credentials (ADC)")
            except Exception as e:
                logger.warning(
                    f"ADC not available ({e}). Drive operations will require valid credentials."
                )
                return None

        return build("drive", "v3", credentials=creds, cache_discovery=False)

    def duplicate_qa_checklist(
        self,
        campaign_id: str,
        campaign_name: str,
        user_emails: Optional[List[str]] = None,
    ) -> str:
        """
        Copies the canonical Master QA Checklist spreadsheet and returns the editable URL.
        Grants write permissions to the team / domain as required by Section 6 Safeguards.
        """
        title = f"[EF QACL] {campaign_id} - {campaign_name}"
        body = {
            "name": title,
            "properties": {
                "campaign_id": str(campaign_id),
                "managed_by": "email_flow_bot",
            },
        }

        if not self.drive_service:
            # Fallback for environments without live Google credentials
            logger.warning(
                "[MOCK/FALLBACK] Google Drive client not configured with live credentials. "
                "Returning mock checklist URL."
            )
            mock_id = f"mock-qacl-{campaign_id}"
            return f"https://docs.google.com/spreadsheets/d/{mock_id}/edit#gid=0"

        try:
            copied_file = (
                self.drive_service.files()
                .copy(fileId=self.template_id, body=body)
                .execute()
            )
            file_id = copied_file.get("id")
            logger.info(
                f"Provisioned fresh checklist on Google Drive: {title} (ID: {file_id})"
            )

            # Safeguard 8: Access Permissions
            self._grant_access_permissions(file_id, user_emails=user_emails)

            return f"https://docs.google.com/spreadsheets/d/{file_id}/edit#gid=0"

        except HttpError as e:
            logger.error(f"Google Drive API error while copying checklist: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error copying checklist template: {e}")
            raise

    def _grant_access_permissions(
        self, file_id: str, user_emails: Optional[List[str]] = None
    ) -> None:
        """
        Grants 'writer' permissions to domain (e.g. monks.com) or explicit user emails.
        """
        if not self.drive_service:
            return

        # 1. Share with domain if configured
        if self.share_domain:
            try:
                domain_permission = {
                    "type": "domain",
                    "role": "writer",
                    "domain": self.share_domain,
                }
                self.drive_service.permissions().create(
                    fileId=file_id, body=domain_permission, fields="id"
                ).execute()
                logger.info(
                    f"Shared checklist {file_id} with domain @{self.share_domain} (role: writer)"
                )
            except Exception as e:
                logger.warning(f"Failed to share file {file_id} with domain @{self.share_domain}: {e}")

        # 2. Share with specific user emails if provided
        if user_emails:
            for email in user_emails:
                if not email or "@" not in email:
                    continue
                try:
                    user_permission = {
                        "type": "user",
                        "role": "writer",
                        "emailAddress": email.strip(),
                    }
                    self.drive_service.permissions().create(
                        fileId=file_id, body=user_permission, fields="id"
                    ).execute()
                    logger.info(f"Granted writer permission on {file_id} to {email}")
                except Exception as e:
                    logger.warning(f"Failed to share file {file_id} with {email}: {e}")

    def find_copy_doc_fallback(self, campaign_id: str) -> Optional[str]:
        """
        Safeguard 9: If Monday Doc column contains no uploaded copy document link,
        search Google Drive for titles containing '[Copy Doc]' and '<Campaign ID>'.
        """
        if not self.drive_service:
            return None

        query = (
            f"name contains '[Copy Doc]' and name contains '{campaign_id}' "
            "and trashed = false"
        )
        try:
            results = (
                self.drive_service.files()
                .list(q=query, spaces="drive", fields="files(id, name, webViewLink)")
                .execute()
            )
            files = results.get("files", [])
            if files:
                doc_id = files[0]["id"]
                doc_title = files[0].get("name", "Copy Doc")
                logger.info(
                    f"Found fallback Copy Doc on Google Drive for campaign {campaign_id}: {doc_title} (ID: {doc_id})"
                )
                return f"https://docs.google.com/document/d/{doc_id}/edit"
        except Exception as e:
            logger.warning(
                f"Error searching Google Drive for fallback Copy Doc for {campaign_id}: {e}"
            )

        return None
