"""
Unit tests for FastAPI Monday.com Webhook receiver.
"""

import pytest
from fastapi.testclient import TestClient
from webhook_server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_monday_webhook_challenge(client):
    payload = {"challenge": "xyz123abc456"}
    response = client.post("/webhook/monday", json=payload)
    assert response.status_code == 200
    assert response.json() == {"challenge": "xyz123abc456"}


def test_webhook_event_trigger_status_column(client, mocker):
    mock_process = mocker.patch("webhook_server.process_single_pulse")

    payload = {
        "event": {
            "userId": 41011989,
            "originalTriggerUuid": None,
            "boardId": 4209532311,
            "pulseId": 12345678,
            "pulseName": "26835 - YTV [Email] - Member Newsletter #19",
            "columnId": "label3",
            "columnType": "color",
            "columnTitle": "Stage",
            "value": {"label": {"index": 1, "text": "Needs QA - Everything approved"}},
            "previousValue": {"label": {"index": 0, "text": "In Development"}},
        }
    }

    response = client.post("/webhook/monday", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    assert response.json()["pulseId"] == 12345678


def test_webhook_event_trigger_checkbox_column(client, mocker):
    mock_process = mocker.patch("webhook_server.process_single_pulse")

    payload = {
        "event": {
            "boardId": 4209532311,
            "pulseId": 12345678,
            "columnId": "boolean_mkysmx2k",
            "value": {"checked": "true"},
        }
    }

    response = client.post("/webhook/monday", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "queued"


def test_webhook_event_ignored_for_unrelated_column(client, mocker):
    mock_process = mocker.patch("webhook_server.process_single_pulse")

    payload = {
        "event": {
            "boardId": 4209532311,
            "pulseId": 12345678,
            "columnId": "some_random_text_column",
            "value": "random text",
        }
    }

    response = client.post("/webhook/monday", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    mock_process.assert_not_called()


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_status_endpoint(client):
    response = client.get("/status")
    assert response.status_code == 200
    assert "processed_count" in response.json()
