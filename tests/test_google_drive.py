"""
Unit tests for GoogleDriveProvisioner.
"""

from unittest.mock import MagicMock
import pytest
from google_drive_client import GoogleDriveProvisioner


def test_duplicate_qa_checklist_mock_mode():
    provisioner = GoogleDriveProvisioner()
    provisioner.drive_service = None  # Force mock fallback mode
    url = provisioner.duplicate_qa_checklist(
        campaign_id="26835",
        campaign_name="26835 - YTV [Email] - Member Newsletter #19",
    )
    assert "mock-qacl-26835" in url


def test_duplicate_qa_checklist_service_call():
    provisioner = GoogleDriveProvisioner()
    mock_service = MagicMock()
    mock_files = MagicMock()
    mock_copy = MagicMock()
    mock_copy.execute.return_value = {"id": "new_sheet_id_456"}
    mock_files.copy.return_value = mock_copy

    mock_perms = MagicMock()
    mock_create_perm = MagicMock()
    mock_create_perm.execute.return_value = {"id": "perm_id_789"}
    mock_perms.create.return_value = mock_create_perm

    mock_service.files.return_value = mock_files
    mock_service.permissions.return_value = mock_perms
    provisioner.drive_service = mock_service
    provisioner.share_domain = "monks.com"

    url = provisioner.duplicate_qa_checklist(
        campaign_id="26835",
        campaign_name="26835 - YTV [Email] - Member Newsletter #19",
    )

    assert url == "https://docs.google.com/spreadsheets/d/new_sheet_id_456/edit#gid=0"
    mock_files.copy.assert_called_once()
    call_args = mock_files.copy.call_args[1]
    assert call_args["body"]["name"] == "[EF QACL] 26835 - 26835 - YTV [Email] - Member Newsletter #19"
    assert call_args["body"]["properties"]["campaign_id"] == "26835"
    assert call_args["body"]["properties"]["managed_by"] == "email_flow_bot"

    # Verify domain permissions created
    mock_perms.create.assert_called_once()
    perm_body = mock_perms.create.call_args[1]["body"]
    assert perm_body["type"] == "domain"
    assert perm_body["domain"] == "monks.com"
    assert perm_body["role"] == "writer"


def test_find_copy_doc_fallback():
    provisioner = GoogleDriveProvisioner()
    mock_service = MagicMock()
    mock_files = MagicMock()
    mock_list = MagicMock()
    mock_list.execute.return_value = {
        "files": [
            {
                "id": "doc_file_abc",
                "name": "[Copy Doc] 26835 - YTV",
                "webViewLink": "https://docs.google.com/document/d/doc_file_abc/edit",
            }
        ]
    }
    mock_files.list.return_value = mock_list
    mock_service.files.return_value = mock_files
    provisioner.drive_service = mock_service

    fallback_url = provisioner.find_copy_doc_fallback("26835")
    assert fallback_url == "https://docs.google.com/document/d/doc_file_abc/edit"
