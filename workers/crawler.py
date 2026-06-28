import pika
import json
import asyncio
import sys
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from app.embeddings import get_embedding, cosine_similarity
from sqlalchemy.orm import Session
from app.models import engine, ZoneSnapshot

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


async def _crawl_page_async(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=30000, wait_until="networkidle")
        html = await page.content()
        await browser.close()
    return html


def crawl_page(url):
    return asyncio.run(_crawl_page_async(url))

SEMANTIC_TAGS = {"header", "nav", "main", "article", "section", "aside", "footer"}
def extract_zones(html):
    soup = BeautifulSoup(html, "html.parser")
    zones = []

    # First pass: zones from semantic HTML elements
    for tag in soup.find_all(SEMANTIC_TAGS):
        heading = tag.find(["h1", "h2", "h3", "h4", "h5", "h6"])
        if heading:
            zone_name = heading.get_text(strip=True)
        else:
            zone_name = tag.name

        text = tag.get_text(separator=" ", strip=True)
        if text:
            zones.append({"zone_name": zone_name, "text": text})
      # Second pass: headings that aren't inside semantic elements
    for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        if heading.find_parent(SEMANTIC_TAGS):
            continue

        zone_name = heading.get_text(strip=True)
        if not zone_name:
            continue

        texts = []
        current = heading.next_sibling
        while current:
            if hasattr(current, "name") and current.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                break
            if hasattr(current, "get_text"):
                t = current.get_text(separator=" ", strip=True)
                if t:
                    texts.append(t)
            current = current.next_sibling

        full_text = f"{zone_name} {' '.join(texts)}".strip()
        if full_text:
            zones.append({"zone_name": zone_name, "text": full_text})
        # Fallback: if no zones found, treat whole page as one zone
    if not zones:
        body = soup.find("body")
        if body:
            text = body.get_text(separator=" ", strip=True)
            if text:
                zones.append({"zone_name": "full_page", "text": text})

    return zones

def process_message(ch, method, properties, body):
    message = json.loads(body)
    url = message["url"]
    print(f"Worker received job: {url}")

    print(f"  Crawling {url}...")
    html = crawl_page(url)
    print(f"  Got {len(html)} characters of HTML")

    zones = extract_zones(html)
    print(f"  Found {len(zones)} zones:")

    session = Session(engine)

    for zone in zones:
        embedding = get_embedding(zone["text"])

        previous = session.query(ZoneSnapshot).filter_by(
            url=url, zone_name=zone["zone_name"]
        ).order_by(ZoneSnapshot.crawled_at.desc()).first()

        sim_score = None
        if previous and previous.embedding is not None:
            sim_score = cosine_similarity(embedding, previous.embedding)

        snapshot = ZoneSnapshot(
            url=url,
            zone_name=zone["zone_name"],
            chunk_text=zone["text"],
            embedding=embedding,
            sim_score=sim_score
        )
        session.add(snapshot)

        if sim_score is not None:
            print(f"    - {zone['zone_name']}: similarity = {sim_score:.4f}")
        else:
            print(f"    - {zone['zone_name']}: first crawl, no comparison yet")

    session.commit()
    session.close()

    ch.basic_ack(delivery_tag=method.delivery_tag)
    print(f"  Job done and acknowledged")



def start_worker():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )
    channel = connection.channel()

    # Make sure queue exists
    channel.queue_declare(queue='crawl_tasks', durable=True)

    # Only pick up one message at a time
    channel.basic_qos(prefetch_count=1)

    # Start listening
    channel.basic_consume(
        queue='crawl_tasks',
        on_message_callback=process_message
    )

    print("Worker is waiting for jobs. Press CTRL+C to stop.")
    channel.start_consuming()

if __name__ == "__main__":
    start_worker()
