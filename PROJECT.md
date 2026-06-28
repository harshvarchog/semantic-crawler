# Semantic Web Crawler and Intelligent Change Detection Engine

## What this project is

Most website monitoring tools alert you when HTML changes. That means
you get notified every time a company changes a button color, font size,
or footer link. This project does something different.

It monitors websites at the level of individual named sections and fires
an alert only when the actual meaning of that section changes. Visual
redesigns, code refactors, and irrelevant daily churn are completely
ignored. When a competitor updates their pricing, you find out. When
they just move things around on the page, you don't hear a thing.

The system also tells you exactly which section changed and summarizes
what specifically is different, so you are never just staring at a
"something changed" notification trying to figure out what matters.

## How it works

A user submits a URL to monitor and a webhook URL to receive alerts.
The system queues the task, visits the page using a full browser
(not a basic HTTP request, so JavaScript-heavy pages work correctly),
and splits the rendered page into named semantic zones based on its
structure. Each zone is converted into a vector embedding, which is a
mathematical representation of its meaning, and stored in a database.

On each subsequent crawl, the new embeddings are compared to the
previous ones. Instead of using a fixed similarity threshold to decide
whether something changed, the system runs a Sequential Probability
Ratio Test (SPRT) per zone. This is a statistical hypothesis test that
accumulates evidence across multiple crawl cycles before making a
decision. It only fires an alert when it is mathematically confident
that the change is real and not noise, guaranteeing a false positive
rate of no more than 5 percent.

When a genuine change is confirmed, the system calls an LLM to produce
a 2 to 3 sentence human-readable summary of exactly what changed in
that section. This summary, along with the zone name, confidence score,
and old and new text, is delivered to the user's webhook endpoint. If
delivery fails, the system retries with exponential backoff before
routing permanently failed deliveries to a dead letter queue for
inspection.

## Tech stack

- Python
- FastAPI for the API layer
- Playwright for full JavaScript rendering via headless Chromium
- sentence-transformers for generating vector embeddings
- PostgreSQL with the pgvector extension for vector storage and search
- RabbitMQ for the task queue and dead letter queue
- scipy and numpy for the SPRT statistical engine
- An LLM API for semantic diff summarization

## Architecture decisions

The page is split into zones using heading tags, ARIA landmark roles,
and semantic HTML elements. Zone identity is derived from heading text
content rather than DOM position, so minor page restructuring does not
cause false positives.

SPRT is configured with a significance level of alpha 0.05 and beta
0.20, meaning the system tolerates a 5 percent false positive rate and
a 20 percent false negative rate. The baseline distribution for each
zone is fitted from a sliding window of the last 30 observations. A
cold start guard prevents SPRT from running until at least 10
historical data points exist for a zone.

The H1 distribution (representing a genuine change) is defined as a
mean shifted down by 2 standard deviations from the baseline and a
standard deviation twice as wide, reflecting the assumption that a
changed page produces lower and more variable similarity scores.

Webhook retries follow a schedule of 5 seconds, then 25 seconds, then
125 seconds before the message is routed to the dead letter queue.

The embedding model used is all-MiniLM-L6-v2, which produces 384
dimensional vectors and offers a good balance of speed and quality for
semantic similarity tasks.

## Database schema

```sql
CREATE TABLE monitored_urls (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url          TEXT NOT NULL,
    webhook_url  TEXT NOT NULL,
    zones_filter TEXT[],
    created_at   TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE zone_snapshots (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url         TEXT NOT NULL,
    zone_name   TEXT NOT NULL,
    crawled_at  TIMESTAMPTZ DEFAULT now(),
    chunk_text  TEXT,
    embedding   vector(384),
    sim_score   FLOAT,
    sprt_state  TEXT,
    log_sum     FLOAT
);

CREATE INDEX ON zone_snapshots
USING ivfflat (embedding vector_cosine_ops);
```

## Build stages

Stage 1 - Git and GitHub setup
Stage 2 - FastAPI endpoint for URL submission
Stage 3 - PostgreSQL and pgvector schema
Stage 4 - RabbitMQ task queue and worker skeleton
Stage 5 - Playwright crawler and semantic zone chunker
Stage 6 - Embedding generation and similarity scoring
Stage 7 - SPRT change detection engine
Stage 8 - LLM diff summarization and webhook delivery
Stage 9 - Retry logic and dead letter queue

## Current status

Stages 1 through 6 complete. Embedding generation and cosine similarity
scoring implemented. Each zone's text is converted to a 384-dim vector
and compared against previous crawls.

## Key numbers

- Embedding dimensions: 384
- SPRT alpha: 0.05
- SPRT beta: 0.20
- Baseline sliding window: last 30 observations
- Cold start minimum: 10 observations
- Retry schedule: 5s, 25s, 125s before dead letter queue