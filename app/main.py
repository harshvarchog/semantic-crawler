from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
import pika
import json

app = FastAPI(
    title="Semantic Web Crawler",
    description="Monitors websites for semantic content changes",
    version="0.1.0"
)

class MonitorRequest(BaseModel):
    url: HttpUrl
    webhook_url: HttpUrl
    zones_to_watch: Optional[List[str]] = None

class MonitorResponse(BaseModel):
    status: str
    message: str

def publish_to_queue(message: dict):
    # Connect to RabbitMQ
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )
    channel = connection.channel()

    # Create queue if it doesn't exist
    channel.queue_declare(queue='crawl_tasks', durable=True)

    # Publish the message
    channel.basic_publish(
        exchange='',
        routing_key='crawl_tasks',
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2  # makes message persistent
        )
    )

    connection.close()
    print(f"Published to queue: {message}")

@app.post("/monitor", response_model=MonitorResponse)
async def monitor(request: MonitorRequest):
    message = {
        "url": str(request.url),
        "webhook_url": str(request.webhook_url),
        "zones_to_watch": request.zones_to_watch
    }

    publish_to_queue(message)

    return MonitorResponse(
        status="queued",
        message="URL accepted and queued for monitoring"
    )

@app.get("/health")
async def health():
    return {"status": "ok"}