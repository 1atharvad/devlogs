---
title: "Building a CPU-Aware Autoscaler"
description: "Why static concurrency doesn't work for CPU-bound workloads, and how asymmetric EWMA — fast to react to load spikes, slow to forget them — solves the oscillation problem that naive autoscalers always hit."
pubDate: "May 01 2026"
primaryTag: "n8n"
tags: ["Redis", "Python", "FastAPI", "Automation"]
---

The [queue mode setup](/devlogs/n8n-queue-mode) from the previous entry works. Workers pull jobs, execute them, and report back. The concurrency=1 limit means each worker's resource usage is predictable. What it doesn't do is answer the question that actually matters under variable load: how many workers should be running right now?

Fixed worker count is the obvious answer. Run three workers, always. But that means three workers sitting mostly idle on a quiet afternoon and three workers potentially insufficient during a burst. The math doesn't work for a workload that isn't consistent.

The autoscaler is a Python service (`processes/worker_autoscaler.py`) that watches CPU usage and Redis queue depth, then controls worker count via `docker compose --scale`.

## Reading CPU from the Host

The first decision: where to get CPU metrics. Container-scoped CPU from the Docker stats API would give usage within the container's cgroup — not useful here. What matters is host CPU, because n8n workers compete with everything else running on the machine.

The fix is mounting the host `/proc` filesystem read-only into the autoscaler container and reading directly from `/proc/stat`:

```python
def host_cpu_percent() -> float:
    for proc_path in ("/host/proc/stat", "/proc/stat"):
        try:
            lines = open(proc_path).readlines()
            break
        except FileNotFoundError:
            continue

    def parse(line: str):
        fields = line.split()
        total = sum(int(f) for f in fields[1:])
        idle = int(fields[4])
        return total, idle

    first = parse(lines[0])
    time.sleep(0.5)          # 0.5s delta window between two readings
    lines2 = open(proc_path).readlines()
    second = parse(lines2[0])

    total_delta = second[0] - first[0]
    idle_delta  = second[1] - first[1]
    return round((1 - idle_delta / total_delta) * 100, 1)
```

The 0.5s sleep is the delta window — two snapshots of `/proc/stat` with a gap between them gives an accurate instantaneous CPU percentage. This runs once per poll cycle (every 30 seconds), not continuously.

Falls back to `/proc/stat` directly if the host mount isn't present — useful for local development where you're not running inside Docker.

## The Asymmetric EWMA

Simple rolling averages cause oscillation. Spawn a new worker, its startup causes a brief CPU spike, the averager sees the spike and triggers an emergency scale-down, the worker gets killed before it processes anything, the queue grows, triggers a scale-up, repeat.

Asymmetric EWMA breaks this by reacting quickly to rising CPU but decaying slowly from peaks:

```python
if cpu_raw > cpu_ema:
    cpu_ema = EWMA_ALPHA_UP   * cpu_raw + (1 - EWMA_ALPHA_UP)   * cpu_ema
else:
    cpu_ema = EWMA_ALPHA_DOWN * cpu_raw + (1 - EWMA_ALPHA_DOWN) * cpu_ema
```

With `alpha_up = 0.5` and `alpha_down = 0.1`: a spike gets 50% weight immediately, so genuine load registers fast. A drop from that spike only gets 10% weight per sample, so the smoothed value stays elevated long after the raw reading has fallen.

For the actual scaling decisions, the effective CPU is `max(ema, raw)` — the more conservative of the two readings:

```python
cpu = round(max(cpu_ema, cpu_raw), 1)
```

This ensures a transient spike that hasn't propagated into the EMA yet still triggers the emergency threshold.

## The Scaling Rules

```python
# Emergency scale-down: host is critically overloaded
if cpu > CPU_SCALE_DOWN_EMERGENCY and workers > MIN_WORKERS:
    desired = workers - 1

# Scale up: work waiting AND both ema and raw have headroom
elif waiting > 0 and cpu_ema < CPU_SCALE_UP_MAX and cpu_raw < CPU_SCALE_UP_MAX and workers < MAX_WORKERS:
    desired = workers + 1

# Scale down: queue has been empty long enough
elif waiting == 0 and active == 0 and workers > MIN_WORKERS:
    if idle_since and (now - idle_since) >= IDLE_BEFORE_SCALEDOWN_SEC:
        desired = workers - 1
```

Scale-up requires *both* EMA and raw CPU below 65% — not either/or. If the raw reading is spiking while the EMA looks calm (because of slow decay), a new worker still shouldn't start. Both signals need headroom.

Emergency scale-down uses `max(ema, raw)` > 88% — the more aggressive reading triggers it. No point waiting for the EMA to catch up when the host is clearly overloaded right now.

Workers run between a minimum of 1 (always one running) and a maximum of 4. Between any two decisions there's a 90 second cooldown:

```python
if desired != workers and (now - last_scale_time) >= COOLDOWN_SEC:
    if scale_to(desired):
        last_scale_time = now
```

The cooldown is the piece that prevents the oscillation loop from reforming even with asymmetric EWMA. Ninety seconds is long enough for a newly spawned worker to start up, connect to Redis, and begin executing before the next scaling decision is made.

## Scaling via Docker Compose

Worker count is controlled with `docker compose up --scale`:

```python
cmd = ["docker", "compose", "-p", COMPOSE_PROJECT, "--env-file", ENV_FILE,
       "-f", COMPOSE_FILE, "-f", WORKER_COMPOSE_FILE,
       "up", "--scale", f"n8n-worker={n}", "-d", "--no-recreate", "n8n-worker"]
```

`--no-recreate` is important — without it, `docker compose up` would restart containers that are already running. With it, the command only creates or removes containers to reach the target count, leaving running workers untouched mid-execution.

## Redis as the Metrics Store

CPU samples are written to Redis after each poll — the same Redis that's running the Bull queue:

```python
snapshot = json.dumps({
    "ts": time.time(), "cpu_raw": cpu_raw, "cpu_ema": cpu_ema,
    "workers": workers, "waiting": waiting, "active": active,
})
r.lpush("autoscaler:metrics", snapshot)
r.ltrim("autoscaler:metrics", 0, 199)  # keep last 200 samples
```

No separate database. `ltrim` keeps the list capped at 200 entries — about 100 minutes of history at a 30 second poll interval. Enough to see recent trends, cheap to store.

## One Bug Worth Mentioning

Workers need access to any community nodes installed on the main n8n instance. Workers and the main instance share an n8n data volume. If workers start before the main instance finishes installing community packages, they find the packages directory empty — either crashing immediately or starting with silent missing-node failures.

The cleaner-looking fix would be a custom Dockerfile that pre-installs the community nodes into the worker image. That doesn't work here: community nodes live in the n8n user data directory, which is a Docker volume shared between the main instance and workers. The main instance is the source of truth — nodes get installed through the UI, into the volume. A Dockerfile layer at the same path gets shadowed by the volume mount at runtime, and even if you worked around that, you'd need to rebuild the worker image every time a node is added through the UI.

Docker Compose's `depends_on` with `condition: service_started` doesn't help here — that only means the n8n container process has launched, not that it's finished initializing and installing community packages. The gap between "container started" and "packages ready" is exactly where workers fall over.

The fix is a startup script that polls the packages directory before starting n8n in worker mode, waiting until it exists and is populated. Five minute timeout. Unglamorous, but it works with the architecture rather than against it. This is the kind of race condition that development hides (you start services by hand, in order) and production consistently surfaces (docker compose starts everything in parallel).

## Where This Stands

The system is built and tested. Not yet deployed across multiple distributed servers in production — that's the next step.

The planned production layout separates concerns cleanly: the main server runs only the n8n instance — UI, webhooks, triggers, scheduling. Worker servers are independent. Each one runs FastAPI, one or more n8n-worker containers, and its own autoscaler. The autoscaler manages only the workers local to that machine; it doesn't coordinate with other worker servers. Adding capacity means adding another worker server with the same stack, not touching the main instance.

The thresholds (65% up, 88% emergency) and EWMA alphas (0.5 rise, 0.1 fall) are calibrated for the current hardware profile and will likely need tuning under real production load patterns across multiple machines.

The full architecture writeup — including the system diagram, exact environment configuration, and the before/after comparison — is in the article [Beyond One Server](/articles/scaling-n8n-redis-autoscaling).
