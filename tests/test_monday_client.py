"""
Unit tests for MondayClient parsing and filtering logic.
"""

import json
import pytest
from monday_client import MondayClient


@pytest.fixture
def monday_client():
    return MondayClient(api_token="dummy_token")


def test_parse_item_fields_viewer_hub(monday_client):
    raw_item = {
        "id": "12345678",
        "name": "26835 - YTV [Email] - Member Newsletter #19",
        "column_values": [
            {
                "id": "boolean_mkysmx2k",
                "text": "v",
                "value": json.dumps({"checked": True}),
                "type": "boolean",
            },
            {
                "id": "label3",
                "text": "Needs QA - Everything approved",
                "value": json.dumps({"index": 1}),
                "type": "color",
            },
            {
                "id": "label7",
                "text": "YTV",
                "value": None,
                "type": "color",
            },
            {
                "id": "person",
                "text": "Huy Bui, Jae Hong",
                "value": json.dumps({"personsAndTeams": [{"id": 41011989}, {"id": 73974758}]}),
                "type": "multiple-person",
            },
            {
                "id": "monday_doc",
                "text": "Brief",
                "value": json.dumps({
                    "files": [
                        {
                            "name": "Copy Doc",
                            "linkToFile": "https://docs.google.com/document/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit",
                        }
                    ]
                }),
                "type": "file",
            },
        ],
    }

    parsed = monday_client._parse_item_fields(raw_item, board_id=4209532311)

    assert parsed["id"] == "12345678"
    assert parsed["campaign_id"] == "26835"
    assert parsed["name"] == "26835 - YTV [Email] - Member Newsletter #19"
    assert parsed["is_email_flow"] is True
    assert parsed["stage"] == "Needs QA - Everything approved"
    assert parsed["product_area"] == "YTV"
    assert "Huy Bui" in parsed["assignees"]
    assert "Jae Hong" in parsed["assignees"]
    assert len(parsed["doc_links"]) == 1
    assert "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms" in parsed["doc_links"][0]
    assert monday_client._is_eligible_for_qa_thread(parsed) is True


def test_parse_item_fields_creators_hub(monday_client):
    raw_item = {
        "id": "87654321",
        "name": "99123 - Creators [Email] - Product Updates",
        "column_values": [
            {
                "id": "boolean_mm46ggd2",
                "text": "",
                "value": json.dumps({"checked": True}),
                "type": "boolean",
            },
            {
                "id": "status",
                "text": "QA in progress",
                "value": None,
                "type": "color",
            },
            {
                "id": "ytc_product_area",
                "text": "Channel Membership",
                "value": None,
                "type": "color",
            },
        ],
    }

    parsed = monday_client._parse_item_fields(raw_item, board_id=4209567424)

    assert parsed["campaign_id"] == "99123"
    assert parsed["is_email_flow"] is True
    assert parsed["stage"] == "QA in progress"
    assert parsed["product_area"] == "Channel Membership"
    assert monday_client._is_eligible_for_qa_thread(parsed) is True


def test_not_eligible_when_checkbox_false(monday_client):
    raw_item = {
        "id": "11111",
        "name": "12345 - Non Email Flow Item",
        "column_values": [
            {
                "id": "boolean_mkysmx2k",
                "text": "",
                "value": json.dumps({"checked": False}),
                "type": "boolean",
            },
            {
                "id": "label3",
                "text": "Needs QA - Everything approved",
                "value": None,
                "type": "color",
            },
        ],
    }

    parsed = monday_client._parse_item_fields(raw_item)
    assert parsed["is_email_flow"] is False
    assert monday_client._is_eligible_for_qa_thread(parsed) is False


def test_not_eligible_when_already_has_slack_thread_ts(monday_client):
    raw_item = {
        "id": "22222",
        "name": "12345 - Already Processed Item",
        "column_values": [
            {
                "id": "boolean_mkysmx2k",
                "text": "v",
                "value": json.dumps({"checked": True}),
                "type": "boolean",
            },
            {
                "id": "label3",
                "text": "Needs QA - Everything approved",
                "value": None,
                "type": "color",
            },
            {
                "id": "slack_thread_ts",
                "text": "1790615737.420869",
                "value": None,
                "type": "text",
            },
        ],
    }

    parsed = monday_client._parse_item_fields(raw_item)
    assert parsed["is_email_flow"] is True
    assert parsed["slack_thread_ts"] == "1790615737.420869"
    assert monday_client._is_eligible_for_qa_thread(parsed) is False
