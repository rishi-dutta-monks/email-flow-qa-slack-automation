"""
Unit tests for SlackThreadDispatcher and Canonical Jae Hong format.
"""

import pytest
from unittest.mock import MagicMock
from slack_dispatcher import SlackThreadDispatcher
from config import SLACK_USER_DIRECTORY, REQUIRED_STAKEHOLDERS


def test_build_parent_mentions():
    dispatcher = SlackThreadDispatcher(dry_run=True)
    assignees = ["Huy Bui", "NonExistent Person"]
    mentions_str = dispatcher.build_parent_mentions(assignees)

    # All required stakeholders must be present
    for req in REQUIRED_STAKEHOLDERS:
        u_info = SLACK_USER_DIRECTORY[req]
        expected_tag = f"*<@{u_info['slack_id']}|{u_info['name']}>*"
        assert expected_tag in mentions_str

    # Non-existent user should be formatted as *{person}*
    assert "**NonExistent Person**" in mentions_str or "*NonExistent Person*" in mentions_str


def test_dispatch_qa_handoff_dry_run():
    dispatcher = SlackThreadDispatcher(dry_run=True)
    ts = dispatcher.dispatch_qa_handoff(
        campaign_name="26835 - YTV [Email] - Member Newsletter #19",
        campaign_id="26835",
        assignees=["Huy Bui", "Jae Hong"],
        copy_doc_url="https://docs.google.com/document/d/doc123/edit",
        gamma_url="https://gamma.corp.google.com/index.html#/campaign/26835/home",
        checklist_url="https://docs.google.com/spreadsheets/d/sheet123/edit#gid=0",
    )
    assert ts == "dry_run_ts_26835"


def test_dispatch_qa_handoff_calls(mocker):
    dispatcher = SlackThreadDispatcher(token="dummy-token", channel_id="C0ANGFFEFS8", dry_run=False)
    mock_client = MagicMock()
    mock_client.chat_postMessage.side_effect = [
        {"ts": "1790615737.420869"},  # parent
        {"ts": "1790615738.000001"},  # reply 1
        {"ts": "1790615739.000002"},  # reply 2
        {"ts": "1790615740.000003"},  # reply 3
    ]
    dispatcher.client = mock_client

    ts = dispatcher.dispatch_qa_handoff(
        campaign_name="26835 - YTV [Email] - Member Newsletter #19",
        campaign_id="26835",
        assignees=["Huy Bui"],
        copy_doc_url="https://docs.google.com/document/d/doc123/edit",
        gamma_url="https://gamma.corp.google.com/index.html#/campaign/26835/home",
        checklist_url="https://docs.google.com/spreadsheets/d/sheet123/edit#gid=0",
    )

    assert ts == "1790615737.420869"
    assert mock_client.chat_postMessage.call_count == 4

    # 1. Parent Message check
    call_args_parent = mock_client.chat_postMessage.call_args_list[0].kwargs
    assert call_args_parent["channel"] == "C0ANGFFEFS8"
    assert "*[Thread] 26835 - YTV [Email] - Member Newsletter #19*" in call_args_parent["text"]
    assert "*<@U01QH0F3DK8|Huy Bui>*" in call_args_parent["text"]
    assert call_args_parent["unfurl_links"] is False

    # 2. Reply 1 check (Copy Doc & Gamma)
    call_args_r1 = mock_client.chat_postMessage.call_args_list[1].kwargs
    assert call_args_r1["thread_ts"] == "1790615737.420869"
    assert ":memo: <https://docs.google.com/document/d/doc123/edit|Copy Doc>" in call_args_r1["text"]
    assert "<https://gamma.corp.google.com/index.html#/campaign/26835/home|Gamma>" in call_args_r1["text"]
    assert call_args_r1["unfurl_links"] is True

    # 3. Reply 2 check (Checklist)
    call_args_r2 = mock_client.chat_postMessage.call_args_list[2].kwargs
    assert call_args_r2["thread_ts"] == "1790615737.420869"
    assert "<https://docs.google.com/spreadsheets/d/sheet123/edit#gid=0|Checklist>" in call_args_r2["text"]
    assert call_args_r2["unfurl_links"] is True

    # 4. Reply 3 check (Proof Status)
    call_args_r3 = mock_client.chat_postMessage.call_args_list[3].kwargs
    assert call_args_r3["thread_ts"] == "1790615737.420869"
    assert call_args_r3["text"] == "Proofs being sent"
