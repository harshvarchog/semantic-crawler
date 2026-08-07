import httpx
import asyncio
import json
import pika
import os
from typing import Optional

WEBHOOK_RETRY_SCHEDULE = [5, 25, 125]  # seconds
DLQ_QUEUE = "webhook_dlq"


async def deliver_webhook(webhook_url: str, payload: dict, max_retries: int = 3) -> bool:
    """
    Deliver webhook with exponential backoff retry.
    Returns True on success, False if all retries exhausted.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        for attempt in range(max_retries):
            try:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                return True
            except (httpx.HTTPError, httpx.TimeoutException) as e:
                if attempt < max_retries - 1:
                    wait = WEBHOOK_RETRY_SCHEDULE[attempt]
                    print(f"  Webhook delivery failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    print(f"  Webhook delivery failed after {max_retries} attempts: {e}")
    return False


def route_to_dlq(message: dict):
    """Route failed webhook delivery to dead letter queue."""
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )
    channel = connection.channel()
    channel.queue_declare(queue=DLQ_QUEUE, durable=True)
    channel.basic_publish(
        exchange='',
        routing_key=DLQ_QUEUE,
        body=json.dumps(message),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    connection.close()
    print(f"  Routed to dead letter queue: {DLQ_QUEUE}")


async def notify_change(
    webhook_url: str,
    url: str,
    zone_name: str,
    old_text: str,
    new_text: str,
    similarity: float,
    sprt_state: str,
    log_sum: float,
    summary: str
):
    """
    Send change notification to webhook. On failure after retries, route to DLQ.
    """
    payload = {
        "event": "semantic_change_detected",
        "url": url,
        "zone_name": zone_name,
        "similarity_score": similarity,
        "sprt_state": sprt_state,
        "log_sum": log_sum,
        "summary": summary,
        "old_text": old_text,
        "new_text": new_text
    }

    success = await deliver_webhook(webhook_url, payload)
    if not success:
        # Add metadata for DLQ inspection
        dlq_message = {
            **payload,
            "dlq_reason": "webhook_delivery_failed_after_retries",
            "dlq_timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z"
        }
        route_to_dlq(dlq_message)