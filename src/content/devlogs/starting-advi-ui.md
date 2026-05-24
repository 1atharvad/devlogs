---
title: "Starting advi-ui: The First Decisions"
description: "What day one of building a personal React component library actually looks like — the tool choices, the build setup, and what you decide to build first when starting from a blank repo."
pubDate: "Apr 20 2026"
primaryTag: "advi-ui"
tags: ["React", "TypeScript", "Vite", "Storybook"]
---

The motivation for advi-ui is [in the article](/articles/building-advi-ui-component-library) — the short version is: I was tired of rewriting the same components across every personal project with no consistency between them. This devlog is what actually happened when I sat down to start it.

## The Tooling Decisions

**Vite over everything else.** Vite has a library mode built into its build config — `build.lib` — that handles dual ESM/CJS output without a separate bundler config. Rollup under the hood, but you don't write Rollup config. For a component library that needs to work in both module systems, that's the right amount of abstraction.

**Both Tailwind and SCSS.** This one needs explaining because it looks redundant. Tailwind handles utilities inside component markup — spacing, layout, responsive behavior, the things you'd write inline anyway. SCSS handles the design token layer: CSS custom properties defined as variables, the `vi-*` component class namespace, anything that needs to cascade or be overridden by consumers. They don't overlap — they handle different things. Tailwind without SCSS would mean no clean token system. SCSS without Tailwind would mean writing layout utilities by hand.

**Storybook from day one.** This was the decision I'm most glad I made. The instinct is to wire up Storybook after the components exist — as a docs step. The better approach is to use it as the development environment from the start. Building a component in Storybook means writing the story alongside the component, which forces you to think about the API from the consumer's perspective before you've gotten too attached to any particular implementation. It's a design review built into the workflow.

**`vite-plugin-dts` for types.** TypeScript declarations without a separate `tsc` emit step. The plugin generates `dist/src/index.d.ts` as part of the normal build. Consumers get accurate prop types without me managing a separate compile step.

## The Build Output

The goal from the start was a package consumers could install without thinking about format:

```
dist/
  advi-ui.es.js     ← ESM
  advi-ui.cjs.js    ← CommonJS
  advi-ui.css       ← All styles
  src/index.d.ts    ← TypeScript types
```

Styles are a separate explicit import (`advi-ui/styles`) rather than side-effect auto-import. That gives consumers control over where in their stylesheet the library styles land — important when cascade order matters.

## What to Build First

The first question with a blank component library: where do you start?

Button. Always Button. Not because it's the most interesting component — it isn't — but because Button sets the baseline that everything else references. Get the variant system right on Button and the pattern applies everywhere. Get it wrong and you're refactoring it out of every subsequent component.

After Button: the form inputs (Input, Textarea), Card, and the overlay components (Dialog, Modal, Toast). These are the components that appear in every project regardless of what the project does. If the library can't handle these well, it's not useful.

The layout components — Header, PageAside, PageNotFound — came in the same initial push. These are more opinionated and more specific to my projects, but having them from the start meant I could actually drop the library into a real project immediately and see whether it worked.

## What v0.1.0 Actually Looked Like

The scaffold was functional but rough. The components existed and rendered. The Storybook ran. The build produced output. But the design token system wasn't fully established yet, the variant patterns weren't consistent across components, and Storybook was configured but not yet used as a real development environment.

That's fine for a first version. The point of v0.1.0 wasn't to ship something polished — it was to have something working that I could actually use and iterate on. The consistency came in the releases after.
