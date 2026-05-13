---
title: "How n8n Changed the Way I Think About Automation"
description: "From writing everything in Python from scratch to architecture-first thinking — the mindset shift a developer goes through when they stop resisting visual workflow tools and start using them strategically."
pubDate: "Dec 18 2025"
heroImage: '@/assets/n8n-coder.jpg'
heroImageAlt: "A developer staring at a glowing screen showing a visual workflow diagram, bathed in warm amber light"
primaryTag: "Automation"
tags: ["n8n", "Automation", "Architecture", "FastAPI"]
---

For a long time, I thought automation meant code. Python scripts, scheduled jobs, custom retry logic, hand-rolled orchestration. Every piece written from scratch, every edge case handled explicitly. That felt like the right way to do it — the developer way. Full control over execution, full ownership of the logic, no black boxes.

Visual workflow tools existed, but I'd mentally filed them under "no-code." For non-developers. For people who couldn't write the thing properly. The thought that would surface whenever someone mentioned a tool like n8n or Zapier: *why would I use this when I can just code it?*

That thinking was wrong. It took me an embarrassingly long time to figure out why.

## The Old Mental Model

The developer instinct to build from scratch isn't irrational. It comes from a real place: experience getting burned by tools that couldn't do what you needed, by abstractions that leaked at the worst moment, by third-party dependencies that introduced more problems than they solved.

So you learn to trust your own code. You build the API client yourself. You write the retry logic yourself. You schedule the job yourself. You instrument the logs yourself. You own the whole thing, and that ownership feels like control.

What I didn't see clearly enough was the cost. Every project I built had a wrapper around some API, a scheduler, a queue of some kind, retry logic, error handling, logging. Not because the problem was complex — because I was rebuilding infrastructure on every project. The actual problem I was trying to solve? That was maybe 20% of the work. The other 80% was plumbing I'd written before, in slightly different shapes.

> I wasn't solving business problems. I was rebuilding infrastructure.

## The Turning Point

The first n8n workflow I built was simple. It called an API, transformed the response, and sent a message to Slack. Twenty minutes. In code, that would have been a script, a scheduler, environment variables, error handling, and eventually a service running somewhere.

But that wasn't what made me pause.

What made me pause was watching the execution. Each node lit up in sequence. The data moved through the workflow step by step, visible at every stage. I could see exactly what went in, what came out, where it slowed down. No mental model required — the workflow *was* the mental model.

> The workflow isn't just execution. It's documentation.

That line hit me harder than I expected. Every system I'd built in code required separate documentation, or comments, or just memory — "the thing that does X lives in this file." Here, the system explained itself. The structure of the workflow was the explanation.

## Clarity Over Control

The assumption I'd carried was that visual tools trade power for simplicity. You get ease of use, you give up flexibility. That's roughly true at the extremes — if you need to implement a custom machine learning pipeline or optimize a tight loop, you're writing code. But for the vast majority of automation work, that tradeoff doesn't actually apply.

What visual workflows actually give you is observability built into the architecture. In a code-first system, if you want to see what's happening at each step, you have to add that visibility yourself — logging, tracing, debugging instrumentation. In n8n, that visibility is structural. Every execution is stored. Every node shows its input and output. You can debug by looking, not by reasoning.

The contrast is real:

Code is powerful but opaque. Visual is constrained but transparent.

For automation work specifically — integrations, data pipelines, multi-service orchestration — that transparency is more valuable than the marginal flexibility you're giving up. The failures are clearer. The logic is shareable. The system is readable by someone who didn't write it.

## The Hybrid Architecture

This is the shift that actually changed how I architect things.

n8n isn't no-code. It's *use code where it matters, not everywhere*. Inside any n8n workflow, you can write JavaScript or Python in a Code node. You can call any API. You can run any logic. The visual layer handles the orchestration — the sequencing, the triggers, the branching, the retries — while code handles the parts that genuinely need code.

The architecture I've settled into now:

- **n8n** handles orchestration, integrations, triggers, and routing
- **FastAPI** handles CPU-intensive operations, complex algorithms, anything performance-critical
- **Custom nodes** encapsulate reusable business logic

Each component has a clear responsibility. n8n doesn't try to be a compute engine. FastAPI doesn't try to be an orchestrator. The boundary between them is explicit, and that boundary is what makes each part independently understandable and scalable.

This is separation of concerns at the workflow level. It sounds obvious in retrospect. It wasn't obvious when I was writing everything in one Python service.

## Validate Before Optimizing

My bachelor's project was an IoT-based inventory management system with recipe recommendation — sensors on a Raspberry Pi tracking ingredient quantities, a collaborative filtering algorithm scoring thousands of recipes in real-time, an Android app built with Kivy. The kind of project where you can spend a year building infrastructure before you know if the actual idea works.

Everything was custom. The data pipeline, the scraping system, the recommendation engine, the app. It worked, and I learned a lot building it. But the ratio of infrastructure work to problem-solving work was badly skewed.

The same core architecture today — IoT data collection, processing, recommendation, notification — could be prototyped in n8n in a day. Not production-ready, not optimized, but working well enough to validate whether the idea does what you think it does. Then you optimize selectively: replace the parts that are too slow with proper code, keep the orchestration layer visual, iterate.

> Build fast, validate, then optimize — only the parts that need it.

That's a different way of working than I had before. Before, I optimized everything upfront because I'd already invested weeks in it. Now the investment is small enough that changing direction isn't painful.

## The Decision Framework I Use Now

The question I used to ask: *should I code this or use a tool?*

That's the wrong question. It frames the choice as code (real, serious) versus tool (convenient, limited). The question that actually produces better systems:

*What's the fastest way to build something maintainable?*

For orchestration, integrations, multi-service workflows, rapid prototyping, anything where the logic is mostly sequencing and data transformation — n8n. For performance-critical operations, complex algorithms, core business logic where you need full control of the execution — code.

Practically, this breaks down to:

**When I reach for n8n:**
- Connecting multiple services
- Scheduling and triggering
- Data transformation pipelines
- Anything I want to debug visually
- Prototypes I need running today

**When I write code:**
- CPU-intensive processing
- Custom algorithms
- Logic that needs to be tested rigorously
- Performance-sensitive paths

The line between them isn't always sharp. But having a framework for thinking about it is better than defaulting to "I'll just code it."

## Addressing the Misconception

Visual tools aren't less engineering. They're higher-level abstraction. The skill of a good engineer isn't writing everything from scratch — it's choosing the right level of abstraction for each problem.

You wouldn't write your own HTTP library for every project. You wouldn't build a database from scratch when Postgres exists. The same principle applies here. n8n is an abstraction over orchestration, just like a web framework is an abstraction over HTTP. Using it well is an engineering skill, not a shortcut around engineering.

Control over implementation details isn't the goal. Control over the outcome is.

## Where This Led

Once I started thinking architecturally about automation — n8n for orchestration, code for compute — the next question became obvious: what happens when the workflows scale?

A single n8n instance has limits. When multiple heavy workflows fire concurrently, they compete for resources. That's what pushed me into queue mode, Redis distribution, and eventually building a custom autoscaler — which is what the next article covers.

The mindset shift came first. The scaling architecture followed from it.

Are you still coding your automation infrastructure from scratch, or have you started reaching for the right tool for each layer?
