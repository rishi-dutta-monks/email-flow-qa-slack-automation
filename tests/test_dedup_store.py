"""
Unit tests for DedupStore SQLite implementation.
"""

import os
import pytest
from dedup_store import DedupStore


@pytest.fixture
def temp_dedup_store(tmp_path):
    db_file = tmp_path / "test_dedup.db"
    return DedupStore(db_path=str(db_file))


def test_dedup_store_flow(temp_dedup_store):
    item_id = "123456"
    campaign_id = "26835"
    campaign_name = "26835 - YTV [Email] - Member Newsletter #19"
    slack_thread_ts = "1790615737.420869"
    checklist_url = "https://docs.google.com/spreadsheets/d/abc/edit"

    assert temp_dedup_store.is_processed(item_id) is False
    assert temp_dedup_store.get_record(item_id) is None

    temp_dedup_store.record_success(
        item_id=item_id,
        campaign_id=campaign_id,
        campaign_name=campaign_name,
        slack_thread_ts=slack_thread_ts,
        checklist_url=checklist_url,
    )

    assert temp_dedup_store.is_processed(item_id) is True
    record = temp_dedup_store.get_record(item_id)
    assert record is not None
    assert record["item_id"] == item_id
    assert record["campaign_id"] == campaign_id
    assert record["slack_thread_ts"] == slack_thread_ts
    assert record["checklist_url"] == checklist_url

    recent = temp_dedup_store.list_processed()
    assert len(recent) == 1
    assert recent[0]["item_id"] == item_id
