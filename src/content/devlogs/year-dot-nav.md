---
title: "Building a Year Dot Navigator"
description: "A fixed right-side dot navigation for year-grouped content — inspired by a timeline component I built at Google for the Sustainability Refresh project. Five-pixel dots, hover labels, and a scroll that centers the year in the viewport."
pubDate: "May 15 2026"
primaryTag: "advi-ui"
tags: ["React", "TypeScript", "CSS"]
---

One of the first projects I worked on after joining Google was the Sustainability Refresh — a page that lived in the footer of google.com, visible to US audiences, in the same section where you'd find links to how Search works, the Google Store, and company information. It published Google's sustainability commitments as a public roadmap spanning 2020 to 2030. Not a blog post, not a PDF — an actual designed page, right there at the bottom of the most visited website on the internet.

The page was live for around two years before Google replaced the footer links and it came down. But while it was up, it had a timeline component I'd built from a Figma spec: a vertical page where each year was a full section, and on the right side of the screen there was a column of small green dots — one per year — that let you jump between them.

The spec was precise: dots at 5px diameter, vertically stacked with 7–8px gaps, fixed to the right edge of the viewport. On hover, the year label appears to the left of the dot. On click, the page scrolls to that year — and the year heading lands at the exact vertical center of the screen, not the top. The RTL version mirrored it: dots on the left, label to the right.

I built it, it shipped, and then I moved on to other things. It was one of those small components that you don't think about much after the fact, but the pattern is genuinely useful.

## Bringing It Back

The devlogs on this site are going to span 2020 to now eventually. A flat list with no navigation is fine when there are five entries — it stops working at thirty. I'd already added year grouping with sticky pills, but what I wanted was the dot nav from the Google project: a permanent right-side navigator that tells you where you are in the timeline and lets you jump.

The component here isn't the Google one — that was built on internal infrastructure, designed for a specific visual language, and not mine to reuse. But the idea translates directly.

## The Scroll Math

The most non-obvious part is the click behavior. `scrollIntoView()` puts the element at the top of the viewport by default. `scrollIntoView({ block: 'center' })` exists, but its behavior varies across browsers and doesn't account for fixed headers.

The explicit calculation is more reliable:

```ts
const scrollToYear = (year: number) => {
  const el = document.getElementById(`year-${year}`);
  if (!el) return;
  const top = el.getBoundingClientRect().top + window.scrollY;
  window.scrollTo({ top: top - window.innerHeight / 2 + el.offsetHeight / 2, behavior: 'smooth' });
};
```

`getBoundingClientRect().top` gives the distance from the viewport top to the element. Adding `window.scrollY` converts it to a document-relative position. Then subtract half the viewport height and add back half the element height — the element's midpoint lands at the viewport midpoint.

## Active State via IntersectionObserver

Each dot has an active state (darker, slightly scaled up) that tracks which year is currently in view. The naive approach is a scroll event listener that checks which section is visible — expensive and jittery.

IntersectionObserver is the right tool. One observer per year section, with a rootMargin that defines an activation zone:

```ts
const obs = new IntersectionObserver(
  ([entry]) => {
    if (entry.isIntersecting) setActiveYear(year);
  },
  { threshold: 0, rootMargin: '-30% 0px -60% 0px' }
);
```

`-30% 0px -60% 0px` means the section has to enter the top 30%–40% band of the viewport to trigger. This puts the active dot update early enough to feel responsive as you scroll but not so early that the wrong year activates.

## Hit Target vs Visual Size

5px dots are not 5px click targets. A 5px button is effectively impossible to click on touch and awkward on desktop. The solution is padding on the button element itself, offset with negative margin to keep the visual layout intact:

```tsx
<button
  className="p-2 -m-2 flex items-center justify-center"
  onClick={() => scrollToYear(year)}
>
  <div style={{ width: '5px', height: '5px' }} className="rounded-full ..." />
</button>
```

The visual dot stays 5px. The actual click area is `5px + 16px padding` on each side — around 37px square, which is a reasonable touch target. The `-m-2` keeps the dots from pushing each other apart visually.

## The Label Animation

The year label appears to the left of the dot on hover. It's positioned absolute, right-anchored relative to the dot, and slides in with `opacity` + `translateX`:

```tsx
<span
  style={{
    opacity: hoveredYear === year ? 1 : 0,
    transform: hoveredYear === year ? 'translateX(0)' : 'translateX(4px)',
    pointerEvents: 'none',
  }}
>
  {year}
</span>
```

`pointer-events: none` on the label means it doesn't interfere with the hover state of nearby dots — the label can overlap them visually without capturing mouse events.

## What Shipped

The component landed in advi-ui as `YearDotNav` (v0.1.12), with an `items: YearDotNavItem[]` prop (`{ year: number; months?: number[] }`) — year-only usage works by omitting `months`.

v0.1.14 extended it with month-level navigation. Month dots collapse and expand below the active year dot, acting as a breadcrumb. Each month gets its own `IntersectionObserver` targeting `#year-{year}-month-{month}` anchors on the page. Clicking a month dot smooth-scrolls to that anchor and updates both `activeYear` and `activeMonth`. The hover pill shows three-letter month abbreviations from a `MONTH_LABELS` map.
