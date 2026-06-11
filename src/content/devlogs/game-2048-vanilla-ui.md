---
title: "2048 v1: The Interface — HTML, CSS, and the ::after Technique"
description: "January 2021 at Cybage. The first working 2048 prototype — a hardcoded 4×4 grid, tiles rendered entirely through CSS ::after pseudo-elements, and a fixed-size board with no concessions to responsive design."
pubDate: "Jan 27 2021"
primaryTag: "Portfolio"
tags: ["HTML", "CSS", "JavaScript"]
---

January 27 2021, written at Cybage. No framework, no build tool, no dependencies beyond a Google Fonts import. Three files: `index.html`, `css/app.css`, and `js/app.js`. The game worked — it had bugs, rough edges, and no game-over screen (just a `console.log`) — but the movement algorithm and the visual foundations built here carried through every version that followed. The JavaScript engine is covered in [the companion devlog](/devlogs/game-2048-vanilla-js); this is about the interface.

## The HTML Structure

`index.html` is 51 lines. The script tag uses `defer` so `app.js` runs after the DOM is fully parsed — which matters because the file queries elements on load. Without `defer`, the script would execute before the `.row` and `.col` elements exist and every query would return null.

The nav is straightforward: a title span and two score boxes, each holding an `<h4>` label and an `<h2>` value hardcoded to `0`. JavaScript updates those `<h2>` elements directly via `innerHTML` whenever the score changes. No IDs anywhere — everything is found by class selectors.

The board is a hardcoded 4×4 grid:

```html
<div class="board">
    <div class="row">
        <div class="col"></div>
        <div class="col"></div>
        <div class="col"></div>
        <div class="col"></div>
    </div>
    <!-- × 4 rows -->
</div>
```

Sixteen `.col` divs, four per `.row`, fully written out in HTML. There's no script generating the grid markup — it's static. The game state is tracked in a JavaScript array, and the visual state is tracked through CSS classes on these elements. An empty cell is a bare `.col`. A cell showing 256 is a `.col` with `tile-256` added to it. Nothing else changes in the DOM.

No IDs were used anywhere in the file. JavaScript navigates to specific cells by index: `querySelectorAll(".board .row")[row].querySelectorAll(".col")[col]`. This re-queries the DOM on every access — no caching — but with a 4×4 grid the performance cost is negligible.

## The CSS: Tiles as Pseudo-Elements

The tile rendering approach is the most interesting decision in the stylesheet. Rather than creating extra DOM elements for tile content, each tile value is represented by the `.col` element's `::after` pseudo-element:

```css
.col {
    position: relative;
    width: 99px;
    height: 99px;
    background-color: #ccc0b3;
    border-radius: 5px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.tile-2::after {
    content: "2";
    position: absolute;
    width: 99px;
    background-color: #eee4da;
    text-align: center;
    border-radius: 5px;
    font-weight: 900;
    font-size: 50px;
    animation: createBox .25s;
    padding: 13px 0;
}
```

`position: relative` on `.col` establishes the containing block for the absolute pseudo-element. The pseudo-element sits on top of the cell background, covering it entirely. The `content` property holds the number as a string literal — hardcoded per rule for all eleven values. Adding a tile class is the only thing JavaScript needs to do; the number, background color, and text color appear automatically through CSS.

This approach means there are no extra DOM nodes for tile values. The `.col` element itself carries both the empty-cell background and, when a class is present, the tile rendering. It's compact, and it works cleanly with the class-toggle approach the JavaScript uses.

## The Color Palette

The palette follows the original 2048 game's color scheme closely. Low tiles are warm beiges — tile-2 is `#eee4da`, tile-4 a slightly more saturated `#ede0c8`. Mid tiles shift through oranges and salmons: `#f2b179` at 8, deeper at 16 and 32, a dark orange-brown at 64. High tiles move into golds — `#edcf72` at 128, stepping through progressively richer yellows up to `#edc22e` at 2048.

Text color switches from dark (`#3c3a32`) to white at tile-8. Below that, the backgrounds are light enough that dark text reads better; at orange and above, white is the right call. That one switch point handles the whole range.

The surrounding palette is warm throughout. The board background is `#bbada0`, cell backgrounds are `#ccc0b3`, and the page is an off-white `#fcf4ed`. The nav's "2048" title uses `#795d04`, a deep golden-brown that ties back to the high-tile colors — the same family, darker.

## Font Size and Padding

Font size steps down manually at each digit-count threshold: 50px for one digit (2, 4, 8), 42px for two (16–64), 38px for three (128–512), 34px for four (1024, 2048). Each step also adjusts `padding` to keep the number visually centered in the 99×99px cell. These are not computed values — every rule has its own hardcoded font size and padding pair. It works exactly because the set of possible tile values is finite and known in advance.

## The Spawn Animation

New tiles pop in with a scale animation:

```css
@keyframes createBox {
    from { transform: scale(0); }
    to   { transform: scale(1); }
}
```

The animation runs over 0.25 seconds. `animation: createBox .25s` only appears in the `tile-2` and `tile-4` rules. Tiles 8 through 2048 appear without animation — merging into a higher tile snaps it in instantly while placing a 2 shows the pop. Since only 2 and 4 can actually spawn on the board, those are the rules that got the animation. Higher tiles appear through merges, not spawns — but visually, the missing animation on merge results is noticeable.

## The Z-Index Stack

The four `.col` elements in each row have staggered z-index values:

```css
.col:nth-child(1) { z-index: 4; }
.col:nth-child(2) { z-index: 3; }
.col:nth-child(3) { z-index: 2; }
.col:nth-child(4) { z-index: 1; }
```

Left cells sit above right cells in stacking order. Since the pseudo-elements are `position: absolute` and the board has no `overflow: hidden`, tiles technically extend beyond their cell boundaries if they were to animate across the board. The z-index stack would control which tile appeared on top during a crossing. No sliding animation was implemented in this version, so the stacking has no visible effect — but the intention to add tile movement animation at some point is readable in the CSS.

## Fixed Layout

The board is `450×450px` with `margin: 20px auto` to center it horizontally. Cells are `99×99px` with `space-evenly` gaps distributing the remaining space. The nav uses `margin: 20px 33%` to constrain it to the center third of the viewport.

None of it is responsive. On a phone-width viewport the board overflows, the nav gets clipped, and nothing adapts. This was a prototype running in a desktop browser — responsive design wasn't part of the brief.

---

The stylesheet solved the core visual problem cleanly: a fixed-dimension grid where tile values render as CSS-driven pseudo-elements, colors step through the canonical 2048 palette, and a 0.25s scale animation marks new tile placement. The fixed sizing and the missing animation on merges were rough edges, but for a first working version, the approach was solid.
