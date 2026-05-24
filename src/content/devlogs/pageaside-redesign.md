---
title: "Redesigning PageAside: From Wrapper to Real Sidebar"
description: "The original PageAside was a styled shell with no behaviour. Getting collapse-to-icon-rail working required rethinking the API, moving from children to an items array, and solving a gap timing problem in pure CSS."
pubDate: "May 03 2026"
primaryTag: "advi-ui"
tags: ["React", "TypeScript", "CSS"]
---

The v0.1.9 PageAside was a styled wrapper and nothing more. You passed children as `<PageAsideNavItem />` elements, it rendered them inside a `w-64` fixed sidebar, and that was the whole component. No collapse, no toggle, no active state. Fine for a static admin shell — useless the moment a project needs a sidebar that can get out of the way.

## What Actually Triggered This

I was building a telemetry and log dashboard for my n8n queue mode project — a monitoring UI where you can watch job queues, worker health, and pipeline runs in real time. The reference point I kept coming back to was Firebase's dashboard: the collapsing icon-rail sidebar that stays out of the way when you're reading dense log data, expands when you need to navigate. That's the pattern I wanted.

The old PageAside wasn't close to that. It had no collapse, no active item state, and the API made it impossible to add either without breaking every existing usage.

## Why the Children API Had to Go

The fundamental problem: if the component renders whatever children you pass, it doesn't know what those children contain. It can't animate a label it doesn't own. The component would need to inspect children at runtime, find the label elements, and animate them — which is fragile and wrong. The only clean solution is for the component to own the item markup itself.

The core problem: if the component renders whatever children you pass, it doesn't know what those children contain. It can't animate a label it doesn't own. The component would need to inspect children at runtime, find the label elements, and animate them — which is fragile and wrong. The only clean solution is for the component to own the item markup itself. That means an `items` array, not children.

Moving to `items: AsideItem[]` gave the component everything it needed:

```ts
interface AsideItem {
  icon: React.ReactNode
  label: string
  onClick: () => void
  active?: boolean
}
```

Now each item's label is rendered by the component, inside a `vi-aside-item-label` element the CSS can target. The old `PageAsideNavItem` export was replaced by `AsideBtn` — the same styled button, but also exported so the footer slot can use it without duplicating markup.

## Two Modes, One Component

The redesign had a specific goal: a single `PageAside` that works in both static and toggleable modes, with the mode determined by the props you pass — no `mode` prop, no separate components.

Static mode — sidebar is always expanded, no chevron rendered:

```tsx
<PageAside items={navItems} />
```

Toggleable mode — pass both `open` and `onToggle`, you get the collapse/expand control:

```tsx
const [open, setOpen] = useState(true);
<PageAside open={open} onToggle={() => setOpen(o => !o)} items={navItems} />
```

The detection inside is one line:

```ts
const toggleable = open !== undefined && onToggle !== undefined
const isOpen = open !== undefined ? open : true
```

The `&&` matters. If you pass `open` but forget `onToggle`, you'd get a toggle button that fires nothing. Checking both means the chevron only appears when the component can actually function in toggle mode. Both modes share the same rendering path — no branching component tree, just conditional classes and one `{toggleable && <ChevronButton />}`.

## The CSS Collapse

No JS measuring, no `useRef`, no height animation. The entire collapse is pure CSS driven by a `vi-aside--open` class toggling on the `<aside>`.

**Width** is handled by a fixed `3.5rem` collapsed width in SCSS and an `openWidth` prop (defaulting to `w-44`) applied as a Tailwind class when open. `transition-all duration-200` on the sidebar handles the interpolation between them.

**Label visibility** uses `max-width` + `opacity` rather than `display: none` or `width`:

```scss
.vi-aside-item-label {
  @apply overflow-hidden transition-[max-width,opacity] duration-200;
  max-width: 0;
  opacity: 0;
}

.vi-aside--open .vi-aside-item-label {
  max-width: 200px;
  opacity: 1;
}
```

`width: 0` would collapse the text but break the icon alignment — the item is a flex row with `justify-content: flex-start`, so a zero-width label pulls the icon position as the label collapses. `max-width: 0` collapses the text content without touching the icon's position in the row.

## The Gap Timing Problem

When collapsed, the gap between icon and (invisible) label should be zero. But a straightforward `gap: 0` on collapse causes a visible snap: the gap disappears immediately while the label is still fading out. For 200ms, you're looking at an icon sitting in space with nothing next to it, then the label vanishes.

The fix is asymmetric transition timing on `gap`:

```scss
// Collapsing: delay gap→0 by 200ms — wait for label to finish animating out
.vi-aside-item {
  gap: 0;
  transition: gap 0s 200ms;
}

// Expanding: snap gap immediately — label fades in with correct spacing already in place
.vi-aside--open .vi-aside-item {
  gap: 0.625rem;
  transition: gap 0s 0s;
}
```

`0s duration, 200ms delay` on collapse means the gap only jumps to zero after the label has already disappeared. On expand, `0s duration, 0s delay` snaps the gap to `0.625rem` before the label starts fading in, so the label appears in the right position from the first frame.

## Specificity

`PageAside` uses `Button` (`.vi-btn`) underneath each nav item. `Button` carries its own hover and variant styles, which means a straightforward `.vi-aside-item` rule will lose. The SCSS uses explicit selector depth to beat the specificity without `!important`:

```scss
// (0,2,0) — beats .vi-btn (0,1,0)
.vi-aside .vi-aside-item { ... }

// (0,3,0) — beats .vi-btn-variant-ghost:hover (0,2,0)
.vi-aside .vi-aside-item--active:hover { ... }
```

Active items need to hold their `bg-primary/10 text-primary` on hover. Without the extra nesting level, Button's ghost hover would override it.

---

The part that would apply elsewhere: the `max-width` + asymmetric gap timing pattern. Any animated show/hide where you have a flex row with an icon and a text label — drawers, nav rails, collapsed sidebars — the problem is always the same. Animating `width` breaks alignment; animating `display` gives you no animation at all. `max-width` + `opacity` with a gap delay is the clean path through.
