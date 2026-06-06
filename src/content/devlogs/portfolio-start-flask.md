---
title: "Starting the Portfolio in Flask"
description: "The real starting point — replicating a Flask + Webpack + TypeScript + SCSS scaffold from memory after 2.5 years at Google, using the portfolio to test it out."
pubDate: "Dec 01 2023"
updatedDate: "Sep 01 2025"
primaryTag: "Portfolio"
tags: ["Flask", "Python", "TypeScript", "SCSS"]
---

After 2.5 years at Google, I had a clear picture of the kind of development scaffold I liked working with. The internal stack was Flask, Webpack, Gulp, Python, TypeScript, and SCSS — a setup that felt well-structured, productive, and clean. When I started building on my own, the first thing I wanted was to recreate that scaffold from memory.

The portfolio wasn't the original goal. The scaffold was.

## Replicating the Google Stack

The setup I remembered and wanted to rebuild: Flask for routing and templating, Webpack to bundle TypeScript and SCSS, Gulp for task automation, Jinja2 as the template engine. Clean separation between backend logic and frontend assets, with a compile step that produced optimized output.

Recreating it from scratch outside Google meant building it without the internal tooling and configuration that made it work. That was the challenge and the point — understanding the system well enough to rebuild it from first principles. The structure I landed on: Flask views render Jinja2 templates, TypeScript compiles to JS, SCSS compiles to CSS, Webpack bundles everything. The same pattern, rebuilt with open-source equivalents.

## The Portfolio as a Test Bed

The portfolio became the project I used to validate the scaffold. It was the right fit — enough sections and interactive behavior to stress-test the template system, the asset pipeline, and the data management approach, but scoped well enough that it could actually be finished.

The data management was one of the things I wanted to get right. At this stage, all content — project details, experience entries, skills — was structured data flowing from Python into Jinja2 templates. The template received a context dict and rendered HTML from it. Simple, explicit, and easy to reason about.

## Frozen-Flask

One of the things that made this setup interesting was [Frozen-Flask](https://frozen-flask.readthedocs.io/). It takes a dynamic Flask application — with real routes, real views, real data — and crawls it to produce a set of static HTML, CSS, and JS files. The output is a fully static site that can be deployed anywhere without a running server.

The workflow: build the Flask app with real dynamic data, run Frozen-Flask to generate static files, deploy the output. The development experience is a full web framework; the production output is static files. Best of both.

This is the same approach used for many large-scale sites — a dynamic authoring environment that compiles down to static output for serving. At the time it was how I was thinking about the CMS side of things: a backend-driven content system that could produce deployable static output.

## Two Bigger Inspirations

The portfolio was one direction. There were two broader things I was working toward:

**A scaffold tool** — a reusable project starter based on this Flask + Webpack + TypeScript + SCSS structure. Something I could use to spin up new projects quickly with a setup I trusted, instead of configuring it from scratch each time.

**A CMS / app system** — an application layer for managing the content that flows into the templates. The data management patterns I was building in the portfolio — structured content, clean template contexts, Frozen-Flask for output — were the foundation for something more generalized.

Both were inspired directly by the systems I'd worked with at Google. The portfolio was where I tested the ideas in practice before building them out further.

The scaffold tool never became a standalone package — but the patterns it established did. Every project after this used the same separation: backend logic handling data and routing, frontend assets compiled through a build step, static output as the deployment target. The CMS idea evolved more concretely: structured content in Python flowing into templates, with Frozen-Flask generating static output, eventually gave way to a proper Django backend with a database, an admin interface, and an API layer.

The scaffold itself evolved when I [migrated to Django](/devlogs/portfolio-flask-to-django) — but the core decisions made here, Jinja2 templates, TypeScript, SCSS, Webpack — stayed in place throughout. The portfolio is live at [atharvadevasthali.com](https://atharvadevasthali.com).
