# Content Guide

A personal reference for deciding what goes on the blog, what type of post it is, and how to write it.

---

## The Core Test

Before writing anything, ask: **does this have a point of view?**

Not "did I do something" — but "do I have something to say about it that would be useful or interesting to someone who isn't me?"

If yes → it belongs here.  
If it's purely activity or record-keeping → git commit message, private notes, or changelog.

---

## Articles vs Devlogs

### Articles
Long-form. Argue something. Have a thesis someone can agree or disagree with.

Good fit for:
- Mindset shifts ("how n8n changed how I think about automation")
- Architectural decisions with reasoning behind them
- Project retrospectives with a takeaway
- Things you wish you'd known before starting something
- Opinions about tools, tradeoffs, approaches

Ask yourself: *Is there a claim in here that I'm making?* If yes, it's an article.

**Length:** 800–2000 words. Long enough to develop the idea, short enough that it doesn't pad.

---

### Devlogs
Short-form. Document a specific thing you built or figured out — with enough context that someone else could understand it or learn from it.

Good fit for:
- A pipeline or workflow you built (with the "why" included)
- A component or feature that had an interesting implementation decision
- A bug that taught you something
- A tool setup that took more thinking than it should have

Ask yourself: *Would this have saved me time if I'd read it before doing it?* If yes, it's a devlog.

**Length:** 300–700 words. One focused thing. Not a full project dump.

---

## The Line Between Them

| This | Goes where |
|---|---|
| "I redesigned the sidebar because the single-mode version was too rigid — here's what changed and why" | Devlog |
| "I updated the PageAside component" | Changelog, not a post |
| "Building a personal component library changed how I think about starting new projects" | Article |
| "Here's how I wired up the RAG pipeline and what each node does" | Devlog |
| "Why I stopped writing automation infrastructure from scratch" | Article |
| "I added a Table component" | Not a post |

---

## Content Areas (what this blog covers)

These are the things you actually build and think about — stay inside them.

- **Automation & AI** — n8n workflows, RAG pipelines, AI agents, LLMs in practice
- **Frontend & Design Systems** — React, component libraries, advi-ui, UI decisions
- **Personal Projects** — things you build for yourself, what you learned, what you'd do differently
- **Developer Thinking** — tool choices, architecture reasoning, mindset shifts from experience (Google, etc.)

If an idea doesn't fit any of these, it probably doesn't fit the blog.

---

## When You Have an Idea

Run it through these questions:

1. **What's the one thing I'm saying?** If you can't state it in one sentence, the idea isn't ready yet.
2. **Who does this help or interest?** Another developer? A future version of me? If the answer is nobody, skip it.
3. **Is there a real decision or tradeoff in here?** Posts with a decision at the center are more interesting than posts that just describe what happened.
4. **Is this a moment or a pattern?** A one-off incident is a devlog. A pattern you've noticed across multiple projects is an article.

---

## What to Capture in the Moment

When you're building something, note down:
- What problem made you build this
- What you tried first and why it didn't work
- The decision that made it click
- What you'd do differently

You don't need to write the post immediately. But capturing these four things while they're fresh means you have everything you need when you do sit down to write.

---

## Things That Don't Belong Here

- Version release notes → put these in GitHub releases
- "I updated X" with no context → changelog
- Tutorial-style walkthroughs of other people's tools with no original thinking → skip
- Day-by-day activity logs → private notes
- Anything you're writing just to have something posted → skip

Frequency doesn't matter. A few good posts compound better than a lot of thin ones.

---

## Quick Reference

**Should I write about this?**

```
Does it have a point of view?
├── No  → Not a post
└── Yes → Is it one specific thing or a broader idea?
           ├── One specific thing (pipeline, component, bug) → Devlog
           └── Broader idea, argument, or retrospective    → Article
```
