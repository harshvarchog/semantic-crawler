# Semantic Web Crawler & Intelligent Change Detection Engine

A distributed system that monitors websites at the semantic zone level
and fires alerts only when a statistically significant content change 
is detected — powered by SPRT hypothesis testing and chunk-level 
vector embeddings.

## Tech Stack
- Python, FastAPI, Playwright
- sentence-transformers, pgvector, PostgreSQL
- RabbitMQ, scipy, numpy

## Status
 Stage 5 — Playwright crawler and zone chunker complete

## Build Stages
- [x] Stage 1 — Git + GitHub setup
- [x] Stage 2 — FastAPI endpoint
- [x] Stage 3 — PostgreSQL + pgvector(in progress)
- [x] Stage 4 — RabbitMQ + workers
- [x] Stage 5 — Playwright + chunker
- [ ] Stage 6 — Embeddings + similarity
- [ ] Stage 7 — SPRT engine
- [ ] Stage 8 — LLM diff + webhook
- [ ] Stage 9 — Retry logic + DLQ