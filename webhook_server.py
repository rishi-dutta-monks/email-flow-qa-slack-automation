"""
FastAPI Webhook Handler for Monday.com Webhooks.
Delivers real-time, sub-second Email.Flow QA handoffs via webhook events.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException, status
from fastapi.responses import JSONResponse

from config import (
    STAGE_COLUMN_KEYS,
    EMAIL_FLOW_CHECKBOX_KEYS,
)
from email_flow_handoff_bot import EmailFlowOrchestrator

logger = logging.getLogger("EmailFlowWebhook")

app = FastAPI(
    title="Email.Flow QA Handoff Receiver",
    description="Webhook listener for Monday.com column transitions to automate QA handoff.",
    version="1.0.0",
)

# Instantiate shared orchestrator
orchestrator = EmailFlowOrchestrator()


def process_single_pulse(pulse_id: int) -> None:
    """
    Background worker task to fetch pulse details from Monday API
    and trigger QA handoff if criteria are met.
    """
    try:
        logger.info(f"[Webhook Worker] Fetching pulse {pulse_id} from Monday.com...")
        item = orchestrator.monday.fetch_single_item(str(pulse_id))
        if not item:
            logger.warning(
                f"[Webhook Worker] Pulse {pulse_id} could not be resolved from Monday API."
            )
            return

        thread_ts = orchestrator.process_item(item, board_id=item.get("board_id"))
        if thread_ts:
            logger.info(
                f"[Webhook Worker] Handled pulse {pulse_id} -> Slack thread ts: {thread_ts}"
            )
        else:
            logger.info(
                f"[Webhook Worker] Pulse {pulse_id} skipped (not eligible or already processed)."
            )
    except Exception as e:
        logger.error(
            f"[Webhook Worker] Unhandled exception processing pulse {pulse_id}: {e}",
            exc_info=True,
        )


@app.post("/webhook/monday")
async def handle_monday_webhook(
    request: Request, background_tasks: BackgroundTasks
):
    """
    Monday.com webhook listener.
    1. Responds to the challenge handshake.
    2. Filters for relevant column events (status or Email.Flow checkbox changes).
    3. Offloads handoff processing to an asynchronous background task.
    """
    try:
        data: Dict[str, Any] = await request.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON payload: {e}",
        )

    # 1. Monday.com Webhook challenge handshake
    if "challenge" in data:
        logger.info(f"Received Monday webhook challenge: {data['challenge']}")
        return {"challenge": data["challenge"]}

    event = data.get("event", {})
    pulse_id = event.get("pulseId")
    column_id = event.get("columnId")

    # Recognized trigger columns: status/stage or checkbox columns
    trigger_columns = STAGE_COLUMN_KEYS + EMAIL_FLOW_CHECKBOX_KEYS

    logger.info(
        f"Webhook event received for pulseId={pulse_id}, columnId={column_id}, boardId={event.get('boardId')}"
    )

    if pulse_id and (column_id is None or column_id in trigger_columns):
        logger.info(
            f"Queuing background handoff processing for pulse {pulse_id} (triggered by {column_id})"
        )
        background_tasks.add_task(process_single_pulse, pulse_id)
        return {"status": "queued", "pulseId": pulse_id, "columnId": column_id}

    return {
        "status": "ignored",
        "reason": f"Column '{column_id}' is not in trigger columns {trigger_columns}",
    }


@app.get("/health")
def health_check():
    """Health check endpoint for container orchestrators (e.g. Cloud Run, Kubernetes)."""
    return {"status": "healthy", "service": "email-flow-handoff-receiver"}


@app.get("/status")
def get_service_status():
    """Returns overview of processed campaigns from SQLite deduplication store."""
    recent = orchestrator.dedup_store.list_processed(limit=20)
    return {
        "processed_count": len(recent),
        "recent_records": recent,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("webhook_server:app", host="0.0.0.0", port=8000, reload=True)
