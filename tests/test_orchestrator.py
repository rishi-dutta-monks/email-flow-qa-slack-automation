"""
Unit tests for EmailFlowOrchestrator end-to-end logic.
"""

from unittest.mock import MagicMock
import pytest
from email_flow_handoff_bot import EmailFlowOrchestrator


@pytest.fixture
def orchestrator(tmp_path):
    db_file = tmp_path / "test_orchestrator.db"
    orch = EmailFlowOrchestrator(db_path=str(db_file), dry_run=True)
    return orch


def test_process_item_success(orchestrator, mocker):
    item = {
        "id": "123456",
        "name": "26835 - YTV [Email] - Member Newsletter #19",
        "board_id": 4209532311,
        "is_email_flow": True,
        "stage": "Needs QA - Everything approved",
        "product_area": "YTV",
        "assignees": ["Huy Bui", "Jae Hong"],
        "doc_links": ["https://docs.google.com/document/d/doc_123/edit"],
        "slack_thread_ts": None,
    }

    # Mock drive duplicate
    mocker.patch.object(
        orchestrator.drive,
        "duplicate_qa_checklist",
        return_value="https://docs.google.com/spreadsheets/d/new_sheet/edit#gid=0",
    )
    # Mock slack dispatch
    mocker.patch.object(
        orchestrator.slack,
        "dispatch_qa_handoff",
        return_value="1790615737.420869",
    )
    # Mock monday writeback
    mock_writeback = mocker.patch.object(
        orchestrator.monday,
        "write_slack_thread_ts",
        return_value=True,
    )

    # Process first time
    thread_ts = orchestrator.process_item(item, board_id=4209532311)
    assert thread_ts == "1790615737.420869"

    # Verify recorded in dedup store
    assert orchestrator.dedup_store.is_processed("123456") is True

    # Process second time (should be skipped by dedup store)
    second_ts = orchestrator.process_item(item, board_id=4209532311)
    assert second_ts is None


def test_process_item_copy_doc_fallback(orchestrator, mocker):
    item = {
        "id": "789012",
        "name": "26835 - YTV [Email] - Member Newsletter #19",
        "board_id": 4209532311,
        "is_email_flow": True,
        "stage": "QA in progress",
        "product_area": "YTV",
        "assignees": ["Huy Bui"],
        "doc_links": [],  # Empty doc links
        "slack_thread_ts": None,
    }

    # Mock drive fallback finding the doc
    mocker.patch.object(
        orchestrator.drive,
        "find_copy_doc_fallback",
        return_value="https://docs.google.com/document/d/fallback_doc_found/edit",
    )
    mocker.patch.object(
        orchestrator.drive,
        "duplicate_qa_checklist",
        return_value="https://docs.google.com/spreadsheets/d/new_sheet/edit#gid=0",
    )
    mock_slack = mocker.patch.object(
        orchestrator.slack,
        "dispatch_qa_handoff",
        return_value="1790615737.420870",
    )

    thread_ts = orchestrator.process_item(item, board_id=4209532311)
    assert thread_ts == "1790615737.420870"

    # Check that fallback doc URL was passed to Slack dispatcher
    call_args = mock_slack.call_args[1]
    assert call_args["copy_doc_url"] == "https://docs.google.com/document/d/fallback_doc_found/edit"
    assert call_args["has_doc_alert"] is False
