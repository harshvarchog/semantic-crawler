from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl
from typing import Optional, List

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

@app.post("/monitor", response_model=MonitorResponse)
async def monitor(request: MonitorRequest):
    print(f"Received request to monitor: {request.url}")
    print(f"Will notify: {request.webhook_url}")
    print(f"Watching zones: {request.zones_to_watch}")

    return MonitorResponse(
        status="queued",
        message=f"URL accepted and queued for monitoring"
    )

@app.get("/health")
async def health():
    return {"status": "ok"}