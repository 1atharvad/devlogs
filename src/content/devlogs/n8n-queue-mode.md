---
title: "Queue Mode and the Concurrency Lie"
description: "n8n's queue mode solves the duplication problem: one main instance, workers that just execute. But its concurrency is a job count, not a resource limit — useless for CPU-bound workflows."
pubDate: "Apr 14 2026"
primaryTag: "n8n"
tags: ["Redis", "Automation"]
---

Queue mode is n8n's answer to distributed execution. Instead of each server running a full n8n instance with all workflows and credentials, you have one main instance that handles everything — UI, webhooks, triggers, scheduling — and worker servers that do nothing except pull jobs off a Redis queue and execute them.

New server needed? Start it as a worker. No credential setup. No workflow duplication. No configuration to keep in sync. The worker connects to Redis, connects to the shared PostgreSQL database, and starts pulling jobs. That's it.

This is the architecture that actually solves the operational problem from the previous approach. One place for workflows. One place for credentials. Workers are interchangeable.

## The Setup

A few environment variables do most of the work. On the main instance:

```env
EXECUTIONS_MODE=queue
QUEUE_BULL_REDIS_HOST=redis
QUEUE_BULL_REDIS_PORT=6379
OFFLOAD_MANUAL_EXECUTIONS_TO_WORKERS=true
```

On the worker:

```env
EXECUTIONS_MODE=queue
QUEUE_BULL_REDIS_HOST=redis
QUEUE_BULL_REDIS_PORT=6379
N8N_CONCURRENCY_PRODUCTION_LIMIT=1
```

`OFFLOAD_MANUAL_EXECUTIONS_TO_WORKERS=true` is the one that catches you if you miss it. Without it, when you trigger a workflow manually in the n8n UI — for testing, for debugging — it runs directly on the main instance. Which means the main instance is doing execution work again, which means you're back to the original problem under a different name. Every execution, manual or scheduled, should go through workers.

## The Concurrency Problem

Setting the workers up was straightforward. The first configuration I tried was `N8N_CONCURRENCY_PRODUCTION_LIMIT=5` — let each worker handle up to five workflows at a time. More parallel capacity per machine.

What that actually means: n8n will assign five jobs to a worker regardless of what those jobs do. A single video generation workflow that runs at 100% CPU for two minutes will share a worker with four other things. The worker doesn't know the first job is CPU-intensive. It just counts: five slots open, job comes in, fill a slot.

The problem is that n8n's concurrency is a count, not a resource limit. It has no visibility into what a job actually costs to run. Five light API polling workflows might be totally fine at concurrency 5. One video encoding workflow is not fine at concurrency 5 — it's not fine at concurrency 2.

Setting concurrency to 1 was the fix that worked. One job per worker, full stop. The behavior becomes predictable: each worker is either executing one thing or it's idle. No contention, no surprises, no CPU spikes from over-assignment.

The tradeoff is underutilization. A worker running one lightweight workflow is using maybe 10% CPU. At concurrency 1, it sits there doing nothing for the rest of that capacity. For CPU-intensive workflows this doesn't matter — one job already takes everything. For lightweight workflows it's wasteful.

## The Actual Problem

Concurrency = 1 makes the system stable. It doesn't make it efficient. And the underlying issue — that n8n distributes work by count rather than by resource cost — doesn't go away just because you set concurrency to 1. It just becomes less visible.

The right model is something that knows what the CPU is actually doing right now and makes dispatch decisions based on that. Not: how many jobs are assigned to this worker. But: can this worker take another job without degrading?

That requires building outside of n8n's concurrency model entirely.
