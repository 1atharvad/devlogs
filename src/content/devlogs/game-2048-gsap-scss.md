---
title: "2048 v3: GSAP Animations and the SCSS Overhaul"
description: "The 2025 migration introduced GSAP for modal animations and touch controls, a height-aware responsive breakpoint system, CSS custom properties for runtime board sizing, and a D-pad controller built from a rotated flex grid."
pubDate: "Oct 23 2025"
primaryTag: "Portfolio"
tags: ["GSAP", "SCSS", "TypeScript", "React"]
---

The 2023 SCSS was functional but fixed — pixel-based sizes, no responsive system, no animations beyond the tile spawn. The 2025 migration replaced it with a breakpoint system that accounts for both viewport width and height, CSS custom properties for runtime board sizing, and GSAP for all animation. The React/Electron setup for this phase is in [the companion devlog](/devlogs/game-2048-react-electron).

## GSAP from CDN: Manual Type Definitions

GSAP is loaded from a CDN script tag in `index.html` rather than bundled as an npm package — which means there are no built-in TypeScript type definitions for it. A full manual declaration was written in `src/renderer/src/types/global.ts`:

```ts
declare global {
  interface Window {
    gsap: { fromTo, set, timeline, to }
    Observer: Observer
  }
}

declare namespace GSAPCore {
  class Animation { kill; pause; play; reverse; progress; eventCallback; duration }
  class Timeline extends Animation { fromTo; from; to; set; add }
}

export type GSAPTimeline = GSAPCore.Timeline
const gsap = window.gsap
export { gsap, _Observer as Observer }
```

`GSAPObserver.ObserverVars` is fully typed — `onDown`, `onUp`, `onLeft`, `onRight`, `tolerance`, `type`, `lockTouch`, `preventDefault`. The exports pull `gsap` and `Observer` off `window` and re-export them as named imports, so the rest of the codebase imports them as normal module dependencies even though they live on the global scope at runtime.

## PageModal: CSS Variables Drive the GSAP Timeline

The modal animation system uses a single GSAP timeline with `play()` to open and `reverse()` to close. The approach is the same one that ended up in [advi-ui's modal component](/devlogs/gsap-modal-animation) — build the timeline once on mount, paused, and let the CSS define the animation values.

```ts
createTimeline(): void {
  const opacity = getCSSProperty(this.contentEl, '--opacity')     // "0, 1"
  const translateX = getCSSProperty(this.contentEl, '--translateX') // "-50%, 50%"
  const scale = getCSSProperty(this.contentEl, '--scale')

  this.timeline = gsap.timeline({ paused: true })
  this.timeline.fromTo(this.contentEl,
    { autoAlpha: from(opacity), xPercent: from(translateX), scale: from(scale) },
    { autoAlpha: to(opacity),   xPercent: to(translateX),   scale: to(scale), duration }
  )
}
```

Each CSS custom property holds a `from, to` pair read as a string and split at runtime. The modal variant — slide-from-right on mobile, zoom-from-center on desktop — is defined entirely in `page-modal.scss`:

```scss
/* Mobile: slides in from the right */
.page-modal {
  --opacity: 1, 1;
  --translateX: -50%, 50%;
  --scale: 1, 1;
}

/* Desktop: zooms in from center */
@include bp(lg) {
  @include bp-height(ml) {
    .page-modal {
      --opacity: 0, 1;
      --translateX: 50%, 50%;
      --scale: 0.5, 1;
    }
  }
}
```

Changing a modal animation is a CSS change, not a TypeScript change. The `PageModal` class reads these values when building the timeline and doesn't need to know which variant it's animating.

On breakpoint-crossing resize — mobile ↔ desktop — `killTimeline()` destroys and rebuilds the timeline so the animation reflects the current breakpoint's CSS values, not the ones it was built under.

## GSAP Observer: Touch and Swipe Input

Touch support uses GSAP Observer rather than raw touch events:

```ts
Observer.create({
  target: boardEl,
  type: 'touch',
  tolerance: 40,
  lockTouch: true,
  onUp: () => game.eventsOnPlay('ArrowUp'),
  onDown: () => game.eventsOnPlay('ArrowDown'),
  onLeft: () => game.eventsOnPlay('ArrowLeft'),
  onRight: () => game.eventsOnPlay('ArrowRight'),
})
```

`tolerance: 40` filters out small incidental finger movements — casual taps don't register as swipes. `lockTouch: true` prevents the same gesture from triggering both the Observer handler and a scroll event on the page. Without it, a swipe on the board scrolls the page simultaneously on mobile. Both settings came from real problems in early testing.

## The Breakpoint System: Width and Height

`global-mixins.scss` defines two separate breakpoint mixins:

```scss
@mixin bp($breakpoint) {
  /* sm: 376px, ml: 426px, md: 600px, tab: 769px, lg: 1024px, xl: 1440px */
}

@mixin bp-height($breakpoint) {
  /* sm: 350px, ml: 650px, md: 750px, mx: 850px, lg: 1024px */
}
```

Width breakpoints alone don't work for a game that must fit on screen. On landscape mobile the viewport is wide but short — standard width breakpoints would trigger desktop layouts that overflow vertically. Height breakpoints gate anything that requires vertical space. The fixed header, for example, is only `position: fixed` when the viewport is both 600px wide and 650px tall — on landscape mobile it falls back to `position: static` so it doesn't consume a significant portion of the usable height.

The two mixins nest together to express conditions like "tablet-width AND enough height":

```scss
.desktop-header {
  display: none;
  @include bp-height(ml) { @include bp(tab) { display: flex; } }
}
```

## CSS Custom Properties for Board Sizing

The board dimension is set at runtime by `Game2024.setMinBoardSize()`, which calculates the available space and writes a single CSS custom property:

```ts
document.documentElement.style.setProperty('--board-side', `${size}px`)
```

Portrait and landscape get different calculations — portrait constrains against viewport width, landscape against viewport height. Everything that depends on board size derives from `--board-side` in CSS:

```scss
.game-board {
  width: var(--board-side, 0);
  height: var(--board-side, 0);
}

.grid-cell {
  width: calc(var(--board-side, 0) * 0.22);
  height: calc(var(--board-side, 0) * 0.22);
}
```

`setMinBoardSize` runs once on mount and again in `eventsOnResize()`, which is debounced to prevent layout thrashing during window drag. The resize handler sets one value; the cascade handles everything else.

## Body Overlay via Animated CSS Custom Property

Modals need a darkening overlay behind them. Rather than a separate overlay element toggled per modal, the `<body>` has a `::after` pseudo-element whose opacity is a CSS custom property animated by GSAP:

```scss
.body-tag {
  --bg-opacity: 0;
  &::after {
    background: rgba($black, var(--bg-opacity));
    height: calc(100% - 64px);
    position: fixed; top: 64px;
    pointer-events: none;
    transition: none;
  }
}
```

When a modal opens, GSAP tweens `--bg-opacity` from `0` to the target value. When it closes, GSAP tweens it back. One element, one property, one GSAP tween — covers every modal.

## D-Pad Controller: Rotation Trick

The on-screen arrow controller is a diamond-shaped D-pad. The trick: a 2×2 flex grid rotated 45°, with each button rotated −45° to stay upright.

```scss
.game-controller {
  transform: translateX(-14px) rotate(45deg);
  width: $controller-size;
  height: $controller-size;
  display: flex;
  flex-wrap: wrap;
  row-gap: 14px;
}

.arrow-btn {
  border-radius: 50%;
  height: 48px;
  width: 48px;
  transform: rotate(-45deg);
}
```

The four buttons in a 2×2 grid form a square. Rotating the grid 45° makes it a diamond. Rotating each button −45° cancels the parent rotation so button content (the chevron SVG) stays upright. Each direction class then rotates only the SVG to point the correct way.

On non-touch devices the D-pad is hidden entirely — `[data-touch-device='false']` on the body suppresses it. On touch devices, the text-based button panel is hidden and the D-pad is shown. The game detects touch capability once on load and sets the attribute; the CSS handles the rest.

## grid-tiles: Responsive Font Sizes

The 2023 stylesheet had one fixed font size per digit count. The 2025 version adds breakpoints at each threshold:

```scss
@if string.length($tile-num) == 1 {
  font-size: 36px;
  @include bp(sm)  { font-size: 42px; }
  @include bp-height(ml) { @include bp(ml) { font-size: 50px; } }
}
```

Small mobile gets a smaller font; the full-size font only appears when both the viewport width and height indicate enough room. The same pattern applies to two-, three-, and four-digit tiles. Combined with the CSS custom property cell sizing, tiles scale correctly across phones, tablets, and desktop without a single hardcoded pixel dimension.

---

The SCSS and GSAP work is what makes the 2025 version feel different from the 2023 one. The game logic was ported unchanged. The visual layer — responsive across orientations, animated, touch-native — is where the rebuild time actually went.
