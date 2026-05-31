---
title: "Replacing the Autoscaler with a CPU Gate"
description: "The autoscaler scaled up into failures. The fix was stopping execution before it started."
pubDate: "May 30 2026"
primaryTag: "n8n"
tags: ["Python", "Redis", "Docker", "Infrastructure"]
---

The [autoscaler](/devlogs/n8n-autoscaler) would spin up a new worker whenever CPU dropped below 65%. The logic was sound on paper — idle capacity, bring in more work. The problem was what happened when a brief spike caused it to scale up right as another heavy job was queued.

Two workers, both running CPU-intensive video generation workflows at the same time, on a machine that couldn't handle even one cleanly. Both would cap on CPU, hit memory limits, and fail. But failing wasn't the end of it. The sub-workflows — the parts responsible for actually generating and writing video files — kept running after the main workflow stopped. Background processes with no parent, still writing large files to disk, with nothing to stop them.

This created a cleanup problem that got worse as servers were added. Files were scattered across machines. Some of them were valid and needed for future use — blindly deleting everything after a failure wasn't an option. Every incident needed manual intervention at both the database and server level to identify what was corrupted and what needed to be kept.

The autoscaler made the problem worse by solving the wrong thing. The issue wasn't that there weren't enough workers — it was that two heavy jobs were running simultaneously on hardware that couldn't support it. Adding workers under load amplified the contention rather than relieving it.

## The Fix: Gate Before Execution

Instead of controlling worker count, the new approach gates whether a job starts at all.

The `cpu_gate.py` router exposes a single endpoint the n8n workflow hits before any heavy execution steps. If host CPU is above threshold, the endpoint rejects with a 503 and the workflow waits. If it's below, execution proceeds.

```python
@router.get("")  # mounted at /cpu-gate
async def get_cpu():
    snapshot = await _latest_snapshot()  # reads from worker-monitor Redis
    if snapshot:
        return _build_result(snapshot["cpu_raw"], snapshot["cpu_ema"], source="worker-monitor")
    return _sample_local()               # fallback: measure directly from /proc/stat
```

The result includes `cpu_effective` (the max of raw and EMA), a `ready` boolean, and `source` — so the caller knows whether it's looking at a fresh worker-monitor reading or a local fallback.

What handles brief spikes is the asymmetric EWMA — it rises quickly on load increases but decays slowly, so a momentary dip to 60% doesn't immediately read as ready. The gate is checking a smoothed view of CPU, not raw instantaneous noise.

A job that never starts can't produce orphaned sub-workflows. Files that don't get written don't need to be cleaned up.

No Docker socket. No scale commands. No cooldown timers. Workers stay running at a fixed count; they just don't accept heavy work when the machine is loaded.

## What the Autoscaler Became

With scaling logic removed, `worker_autoscaler.py` became `worker_monitor.py` — same CPU reading, same EWMA, writes metrics to Redis and nothing else. The Redis key is `worker-monitor:metrics:<SERVER_ID>` where `SERVER_ID` is set as a stable env var in compose (not Docker's random container hostname, which caused stale keys to pile up in the dashboard server selector). A 10-poll TTL expires entries for offline servers automatically.

Each server runs its own monitor. The dashboard reads all keys and shows a server selector when there's more than one — switching servers swaps the charts. Single-server deployments see no change.

## Observability Along the Way

Verifying the gate was working meant actually being able to read the logs. The log viewer turned out to be broken in two ways.

The stream selector was using `{job="docker"}` as the Loki label. That label doesn't exist — the correct one is `container`. Loki returns an empty result with no error, so the viewer had been silently showing nothing for the "all containers" path.

The polling approach (replacing the entire log list every 5 seconds) also caused a race condition on filter changes: a slow response from the previous filter would overwrite the new one. Replaced with SSE — the backend streams new entries as they arrive, advancing the timestamp cursor by 1ns after each batch. A generation counter on the frontend discards events from stale streams when filters change quickly.

Neither was the goal. They came up because the monitoring needed to actually work to confirm the gate was doing what it was supposed to.

The gate moves the intervention point from "after the failure, figure out what's salvageable" to "before the execution, check if it's safe to run."
