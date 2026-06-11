---
title: "2048 v2: Rewriting the Game Engine in TypeScript"
description: "The 2023 rewrite replaced global functions and raw arrays with a typed Game2024 class, a unified movement algorithm, two-pass merge logic, and proper game-over detection — fixing every structural bug from the 2021 version."
pubDate: "Oct 13 2023"
primaryTag: "Portfolio"
tags: ["TypeScript", "SCSS", "Webpack", "Flask"]
---

The [2021 prototype](/devlogs/game-2048-vanilla-js) worked, but everything about how it was structured was a first-draft decision — global functions, `var` throughout, raw `[row, col]` arrays, no key filtering, a merge bug that could double-merge tiles, and a game-over check that was just `console.log`. The October 2023 rewrite replaced all of it. Same game, different foundation. The build setup and SCSS side of this phase are covered in [the companion devlog](/devlogs/game-2048-webpack-scss).

## Class Structure and Cached DOM

The 2021 version had no class — game state was global variables and functions defined in module scope. The rewrite wraps everything in a `Game2024` class:

```ts
export class Game2024 {
  bestScoreEl: HTMLElement;
  gameGridEl: HTMLElement;
  gameScoreEl: HTMLElement;
  gridCellList: HTMLElement[][];
  score: number;
}
```

`gridCellList` is a 2D array of the actual DOM elements, built once in the constructor. The 2021 version re-ran `querySelectorAll(".board .row")[row].querySelectorAll(".col")[col]` on every `toggleTile` call. Here, the cells are cached upfront and accessed by index.

The grid array no longer holds numbers. In the 2021 version there were two parallel data structures — a number grid and the DOM — that had to be kept in sync manually. Here the DOM is the single source of truth: tile values are read from `element.innerText`. There's nothing to sync.

## Types: Position, Selector, Event

`constants.ts` replaces the raw arrays and hardcoded strings scattered through the 2021 code:

```ts
export interface Position { x: number; y: number; }

export enum Selector {
  BOARD_GRID = 'board-grid',
  GRID_CELL = 'grid-cell',
  JS_BEST_SCORE = 'js-best-score',
  TILE_UPDATED = 'tile-updated',
  // ...
}

export enum Event {
  ANIMATION_END = 'animationend',
  ARROW_DOWN = 'ArrowDown',
  KEY_DOWN = 'keydown',
  // ...
}
```

`Position` with named `x` and `y` properties replaces the `[row, col]` tuples. Every DOM class name and every event string is a typed constant — no bare string literals in game logic.

## Input Handling

The 2021 handler fired on every keypress with no filtering and always spawned a new tile regardless of whether anything moved:

```js
// 2021
document.onkeydown = function(e) {
  moveTiles(e.key);
  updateScore();
  addTile();
}
```

The rewrite fixes both problems:

```ts
document.addEventListener(Event.KEY_DOWN, (event: KeyboardEvent) => {
  const key = event.key;
  const keyList = ['ArrowLeft', 'ArrowUp', 'ArrowRight', 'ArrowDown'];

  if (keyList.includes(key)) {
    const addNewTile = this.moveTiles(key);
    this.moveTiles(key, false);
    this.updateScore();
    if (addNewTile) {
      this.addTile();
    }
  }
});
```

`addEventListener` instead of `document.onkeydown` — multiple handlers can coexist. Arrow keys are filtered explicitly before any game logic runs. `addTile` only fires if `moveTiles` returned `true` — meaning at least one tile actually moved.

## The Unified Movement Algorithm

The 2021 `getNextPos` had four separate `for` loops, one per direction, each with the same logic duplicated. The rewrite collapses them into one:

```ts
getNextPos(pos: Position, arrowEvent: string, mergeTiles = true): [Position, number] {
  let initPos: number;
  let direction: number;
  let condition: Function;
  let getAdjPos: Function;

  switch (arrowEvent) {
    case Event.ARROW_LEFT:
      initPos = pos.x - 1; direction = -1;
      condition = () => initPos >= 0;
      getAdjPos = () => ({ x: initPos, y: pos.y });
      break;
    // ArrowRight, ArrowUp, ArrowDown set different initPos/direction/condition/getAdjPos
  }

  for (; condition(); initPos += direction) {
    // same traversal logic runs for all 4 directions
  }
}
```

The `switch` sets four variables — starting position, step direction, loop boundary condition, and adjacent-position resolver — then a single loop body runs for all directions. Adding a new direction requires only a new `case` block, not a new loop.

## Fixing the Double-Merge Bug

The 2021 version had no guard against a tile merging twice in one move. In a case like `[2, 2, 2, 0]` moving left, the first 2 could merge with the second, producing a 4 at column 0, which could then merge with the third 2 — incorrect. The fix is a two-pass move:

```ts
const addNewTile = this.moveTiles(key);        // first pass: move and merge
this.moveTiles(key, false);                    // second pass: slide only, no merging
```

The first pass handles merges. The second pass, with `mergeTiles = false`, slides any remaining tiles into their final positions without allowing a second merge. The 2021 version had no equivalent.

## Fixing the classList Bug

```ts
// 2021 — removes only classList[1], breaks if more than one extra class exists
tile.classList.remove(tile.classList[1]);

// 2023 — removes all classes beyond the first
tileEl.classList.remove(...[...tileEl.classList].slice(1));
tileEl.innerText = '';
```

The 2021 approach assumed the tile class was always the second and only extra class on the element. The rewrite spreads and removes everything after index 0, then clears `innerText` — both the class and the displayed value are reset cleanly.

## Game-Over Detection

The 2021 version had no real game-over detection — `addTile` logged to the console when there were no empty cells, but didn't check if any merge was still possible on a full board. The rewrite adds `sameAdjacentCells()`:

```ts
sameAdjacentCells(): boolean {
  return this.gridCellList.some((gridRow, rowIndex) => {
    return gridRow.some((gridCell, colIndex) => {
      return [[1, 0], [0, 1]].some(([dx, dy]) => {
        const neighbor = this.gridCellList[rowIndex + dy]?.[colIndex + dx];
        return neighbor && gridCell.innerText === neighbor.innerText;
      });
    });
  });
}
```

Checks every cell against its right and bottom neighbour. If any adjacent pair has equal values, a move is still possible and the game isn't over. Combined with an empty-cell check, this correctly identifies a locked board. When the game ends, a `data-game-over` attribute is set on the body — which the CSS uses to show the overlay and dim the board — rather than logging to the console.

## The Animation System

In the 2021 version, `animation: createBox .25s` was hardcoded on the `::after` pseudo-element rule for `tile-2` and `tile-4`. It played once on first render and never again, because the class was never removed and re-added. Higher tiles had no animation at all.

The rewrite fixes this with a `tile-updated` class and an `animationend` listener:

```ts
tileEl.classList.add(Selector.TILE_UPDATED);
tileEl.addEventListener(Event.ANIMATION_END, () => {
  tileEl.classList.remove(Selector.TILE_UPDATED);
});
```

The SCSS ties the animation to `tile-updated` rather than to the tile value class. Adding the class triggers the animation; the `animationend` listener removes it immediately after, so it can fire again on the next spawn or merge. Every tile value gets the animation now, not just 2 and 4.

---

Every structural problem in the 2021 version had a specific fix here: the double-merge bug, the classList fragility, the missing key filter, the missing game-over logic, the permanent animation class, the re-querying DOM. The game logic itself — the directional traversal, the merge-then-slide sequence — stayed the same. The foundation around it is what changed.
