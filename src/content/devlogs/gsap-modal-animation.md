---
title: "Animating a Modal with GSAP in React"
description: "The trick to smooth modal exit animations isn't a better animation library — it's never unmounting the modal in the first place. Here's how play() and reverse() on a single GSAP timeline make enter and exit animations two sides of the same thing."
pubDate: "Apr 23 2026"
primaryTag: "advi-ui"
tags: ["React", "GSAP", "Animation"]
---

The modal is live in Storybook — [view the demo](https://advi-ui.vercel.app/?path=/docs/ui-modal--docs) to see all three variants running.

Most animated modals look fine opening. The problem is closing. The content disappears instantly or cuts away mid-animation because the component unmounts before the exit animation can finish. The typical fix is to delay unmounting — track an `isAnimating` state, wait for the animation to complete, then remove the element.

That works, but it's the wrong model. The better fix is to never unmount at all.

## Stay Mounted, Play and Reverse

The modal in advi-ui stays permanently in the DOM. It doesn't mount on open or unmount on close. Instead, a single GSAP timeline is built once on mount, paused, and then either played or reversed depending on open state:

```ts
const tl = gsap.timeline({ paused: true, ease: "power1.out" });

tl.fromTo(overlay, { autoAlpha: 0 }, { autoAlpha: 1, duration }, 0);
tl.fromTo(
  content,
  { autoAlpha: opFrom, scale: scFrom, xPercent: xFrom, yPercent: yFrom },
  { autoAlpha: opTo,   scale: scTo,   xPercent: xTo,   yPercent: yTo, duration },
  0
);
```

Open → `tl.play()`. Close → `tl.reverse()`. The exit animation is the enter animation running backwards. No second timeline, no exit state management, no timing hacks.

`autoAlpha` is GSAP's shorthand for `opacity` + `visibility` together — when opacity reaches 0, visibility is set to `hidden` automatically, which takes the element out of tab order and pointer events without removing it from the DOM.

## Variants via CSS Custom Properties

The second interesting decision is how variants are handled. Instead of hardcoding animation values for each modal style in JavaScript, the component reads them from CSS custom properties at runtime:

```ts
const getCSSVar = (el, prop) => {
  const val = getComputedStyle(el).getPropertyValue(prop).trim();
  const [a, b] = val.split(",").map(parseFloat);
  return [a, b]; // [fromValue, toValue]
};
```

Each variant class defines four properties — opacity, scale, x translation, y translation — as `from, to` pairs in SCSS:

```scss
// Centered dialog — scale + fade
.vi-modal-content {
  --modal-opacity:     0, 1;
  --modal-scale:       0.95, 1;
  --modal-translate-x: -50, -50;
  --modal-translate-y: -50, -50;
}

// Right panel — slides in from the right edge
.vi-modal-slide-right {
  --modal-opacity:     0, 1;
  --modal-scale:       1, 1;
  --modal-translate-x: 100, 0;
  --modal-translate-y: 0, 0;
}
```

GSAP reads these when building the timeline. The result: adding a new animation variant means writing SCSS only — no JavaScript changes, no new component logic. A fully custom animation is just a class with overridden CSS vars:

```scss
.my-modal-bounce {
  --modal-opacity:     0, 1;
  --modal-scale:       0.5, 1;
  --modal-translate-x: -50, -50;
  --modal-translate-y: -80, -50;
}
```

```tsx
<Modal className="my-modal-bounce" duration={0.6} ...>
```

## The Portal Timing Bug

The modal renders into a portal — by default `document.body`, but configurable via `modalRootSelector`. The first version resolved the portal target in `useMemo`:

```ts
// wrong
const modalRootEl = useMemo(
  () => document.querySelector(modalRootSelector),
  [modalRootSelector]
);
```

`useMemo` runs during the render phase. The DOM isn't guaranteed to be in its final state there, and in Storybook the target element simply didn't exist yet when the component first rendered. The portal silently fell back to `document.body`, which meant the modal appeared in the wrong place in Docs view.

The fix was moving it to `useEffect` with a state update:

```ts
const [modalRootEl, setModalRootEl] = useState<Element | null>(null);

useEffect(() => {
  setModalRootEl(document.querySelector(modalRootSelector));
}, [modalRootSelector]);
```

The portal is suppressed until `modalRootEl` is confirmed, and the GSAP timeline is built only after the portal target exists. Reading the DOM after commit, not during render.

## Accessibility

One detail worth noting: when the modal is closed, the content div gets the `inert` attribute instead of `aria-hidden`. `inert` is more complete — it blocks all keyboard interaction, pointer events, and assistive technology traversal in one attribute, without needing to manage focus manually for the closed state.

On open, focus moves to the close button. On close, focus returns to whichever element triggered the modal. Escape key closes it. The overlay click closes it. Standard expectations, all covered.

---

The permanently-mounted model is the part I'd apply elsewhere. Any component where you want a smooth exit — drawers, toasts, tooltips — the instinct to unmount on hide is the wrong instinct. Keep it mounted, animate the visibility, and the enter/exit problem becomes one timeline instead of two.
