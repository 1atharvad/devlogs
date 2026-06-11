---
title: "2048 v1: The Game Engine in Vanilla JavaScript"
description: "How the first 2048 prototype worked under the hood — global state, the directional movement algorithm, and the bugs that came with a first working version."
pubDate: "Jan 27 2021"
primaryTag: "Portfolio"
tags: ["JavaScript", "HTML", "CSS"]
---

`js/app.js` is 191 lines of vanilla JavaScript — no modules, no classes, no bundler. Global functions, global state, and `document.onkeydown`. This is the engine behind the [first prototype's interface](/devlogs/game-2048-vanilla-ui), January 27 2021, at Cybage.

## Initialization

The file ends with six statements that run on load:

```js
var grid = createGrid();
var score = 0;
updateBestScore();
arrowBtnPress();
addTile();
addTile();
```

The sequence matters: build the grid array, initialize the score, display any stored best score, attach the keyboard listener, then place two starting tiles. `var` throughout — no `const`, no `let`. At the time this was written, ES6 style wasn't the default assumption for small personal projects.

`createGrid()` builds the 4×4 array:

```js
function createGrid() {
    var grid = [];
    for (var i = 0; i < 4; i++) {
        var list = [];
        for (var j = 0; j < 4; j++) { list[j] = 0; }
        grid[i] = list;
    }
    return grid;
}
```

A 4×4 matrix filled with `0`. Zero means empty. Non-zero means a tile with that value. The grid array is the source of truth for game logic; the DOM reflects it. Both are always updated together via `toggleTile`.

## Reading the Grid: getTiles

`getTiles(emptyTiles)` scans the entire grid and returns a flat list of `[row, col]` positions — either the occupied ones or the empty ones depending on the flag:

```js
function getTiles(emptyTiles = false) {
    var tiles = [];
    var count = 0;
    for (var i = 0; i < grid.length; i++) {
        for (var j = 0; j < grid[i].length; j++) {
            if (emptyTiles === true) {
                if (grid[i][j] === 0) { tiles[count] = [i, j]; count++; }
            } else {
                if (grid[i][j] !== 0) { tiles[count] = [i, j]; count++; }
            }
        }
    }
    return tiles;
}
```

The iteration order is row-by-row, left-to-right, top-to-bottom. That ordering is what makes `moveTiles` work correctly without extra logic — the natural traversal order is already right for left and up moves. Right and down just need it reversed.

`emptyTiles=false` is used by `moveTiles` to get the tiles that need to be moved. `emptyTiles=true` is used by `addTile` to find somewhere to place a new tile.

## The Movement Algorithm: getNextPos

`getNextPos(position, direction)` is the core of the game. Given a tile's current `[row, col]` and a direction, it scans outward from that position and determines where the tile should land and what value it should carry.

```js
function getNextPos(position, direction) {
    var nextPos;
    var tileVal;
    switch (direction) {
        case "ArrowLeft":
            for (var i = position[1] - 1; i >= 0; i--) {
                if (grid[position[0]][i] !== 0) {
                    if (grid[position[0]][position[1]] === grid[position[0]][i]) {
                        tileVal = grid[position[0]][position[1]] * 2;
                        score += tileVal;
                        nextPos = [position[0], i];
                        toggleTile(nextPos, 0);
                    }
                    break;
                }
                tileVal = grid[position[0]][position[1]];
                nextPos = [position[0], i];
            }
            break;
        // ArrowUp, ArrowRight, ArrowDown follow the same pattern
    }
    return [nextPos, tileVal];
}
```

Walking through a left move step by step: starting from the tile's column, scan leftward one cell at a time (`i = col - 1` down to `0`).

If the scanned cell is empty, the tile can slide there — `nextPos` and `tileVal` update and the loop continues, because there may be more empty space further along. If the cell is occupied and the values match, the tile merges: the value doubles, the score increments, the target cell is cleared via `toggleTile(nextPos, 0)`, and the loop breaks. If the cell is occupied with a different value, the tile is blocked — the loop breaks without updating `nextPos`, leaving the tile at the last empty position it found, or in place if none was found.

All four directions use the same logic with the axis and scan direction swapped. ArrowRight scans `col + 1` up to `3`. ArrowUp scans `row - 1` down to `0`. ArrowDown scans `row + 1` up to `3`.

The return value is `[nextPos, tileVal]`. If `nextPos` is still `undefined` after the loop — meaning the tile was already flush against the edge with no empty space and no merge possible — `moveTiles` treats that as no movement and leaves the tile alone.

This algorithm carried forward through the [2023 TypeScript rewrite](/devlogs/game-2048-ts-engine) and the [2025 React migration](/devlogs/game-2048-react-electron). The data structures around it changed — raw `[row, col]` arrays became `Position` objects, the grid state moved — but the directional traversal logic is the same.

## Traversal Order: moveTiles

`moveTiles(direction)` collects all occupied positions and applies `getNextPos` to each. The traversal order determines correctness:

```js
function moveTiles(direction) {
    var tiles;
    if (direction === "ArrowRight" || direction === "ArrowDown") {
        tiles = getTiles().reverse();
    } else {
        tiles = getTiles();
    }
    tiles.forEach(function(position) {
        var data = getNextPos(position, direction);
        var nextPos = data[0];
        console.log(nextPos, data[1]);
        if (nextPos !== undefined) {
            toggleTile(nextPos, data[1]);
            toggleTile(position, 0);
        }
    });
}
```

Consider a row `[2, 0, 0, 2]` with a right move. The rightmost tile is at column 3 — it has nowhere to go. The leftmost tile is at column 0 — it needs to slide all the way to column 3 and merge. If you process left-to-right (natural `getTiles()` order), the column 0 tile gets processed first. `getNextPos` scans right, finds column 3 occupied by a matching value, and merges — correctly. But if there had been a tile at column 1 (`[2, 2, 0, 2]`), processing left-to-right would move column 0's tile to column 1 (blocked by the existing tile), then move column 1's already-settled tile again. Processing right-to-left — `getTiles().reverse()` — means column 1's tile evaluates first, slides to column 3 and merges into a 4. Column 0's tile then scans right, finds column 2 empty, then hits the merged 4 at column 3 (which doesn't match), and stops at column 2. Correct.

Left and up moves use the natural top-left-first order for the same reason: tiles closer to the destination edge settle first.

There is one bug in this version: no double-merge guard. In the 2023 rewrite, `moveTiles` runs a second pass to detect positions that were already merged and prevent them from merging again. Here, there is no such check. In practice the bug rarely surfaces — it requires a specific sequence where a tile merges into a position, and that position then gets merged into again before the frame updates — but it's possible.

The `console.log(nextPos, data[1])` in the forEach body was never removed. Every tile movement logs its destination and value to the console during a real game session.

## Updating the DOM: toggleTile

```js
function toggleTile(position, value) {
    var tile = document.querySelectorAll(".board .row")[position[0]]
                       .querySelectorAll(".col")[position[1]];
    if (value !== 0) {
        tile.classList.add("tile-" + value);
        grid[position[0]][position[1]] = value;
    } else {
        tile.classList.remove(tile.classList[1]);
        grid[position[0]][position[1]] = 0;
    }
}
```

`toggleTile` is the only function that touches both the DOM and the grid array, keeping them in sync. To add a tile, it adds the appropriate class and writes the value to the grid. To clear a tile, it removes `classList[1]` — the second class, which is always the tile class since `classList[0]` is always `"col"` — and zeros out the grid position.

The `classList[1]` removal is a minor fragility: it assumes the tile class is always the second and only extra class on the element. That's true here, but if any other class were added to `.col` elements the removal would break.

The DOM query re-runs every call — no caching of cell references. `querySelectorAll` on 16 elements is fast enough that it doesn't matter in practice.

## Placing Tiles: addTile

```js
function addTile() {
    var notList = getTiles(true);
    var position = notList[Math.floor((Math.random() * notList.length) + 1) - 1];
    if (position !== undefined) {
        toggleTile(position, 2);
    } else {
        console.log("Game Over");
    }
}
```

Gets all empty positions, picks one at random, places a `2`. If `notList` is empty, `position` is `undefined` and the function logs `"Game Over"` to the console — no UI feedback, no modal, no score display. The game continues accepting keypresses; it just stops placing new tiles. There's also no check for whether any merge is still possible on a full board, so a locked board with adjacent equal values triggers the console message prematurely.

New tiles always spawn as `2`. The real 2048 game spawns `4` roughly 10% of the time. That behavior wasn't implemented here.

## Score and Best Score

```js
function updateScore() {
    document.querySelector(".score h2").innerHTML = score;
    updateBestScore();
}

function updateBestScore() {
    var key = "high-score";
    if (sessionStorage.getItem(key) === null) {
        sessionStorage.setItem(key, 0);
    } else if (sessionStorage.getItem(key) < score) {
        sessionStorage.setItem(key, score);
    }
    document.querySelector(".best-score h2").innerHTML = sessionStorage.getItem(key);
}
```

Score is a global `var` incremented inside `getNextPos` on every merge. `updateScore` writes it to the DOM and calls `updateBestScore`. The best score is stored in `sessionStorage` under the key `"high-score"` — not `localStorage`, so it resets when the tab is closed. Session scope was probably fine for a local prototype, but it means no persistent best across sessions.

The comparison `sessionStorage.getItem(key) < score` compares a string to a number. JavaScript coerces the string to a number for the comparison, so it works correctly. The intent is clear even if the types don't match.

## The Input Handler

```js
function arrowBtnPress() {
    document.onkeydown = function(e) {
        moveTiles(e.key);
        updateScore();
        addTile();
    };
}
```

`document.onkeydown` instead of `addEventListener` — only one handler can be attached this way, which is fine here since nothing else sets it. The handler fires on every keydown with no filtering: pressing spacebar, a letter, or any non-arrow key calls `moveTiles`, `updateScore`, and `addTile` with that key string. `moveTiles` passes the key to `getNextPos` via a `switch`, which has no `default` case — so non-arrow keys produce no grid change. `updateScore` then writes the same score again. `addTile` places a new tile on the board even though nothing moved.

The sequence always adds a new tile after every keypress, regardless of whether the move changed the board. In a real game session, pressing a key that produces no movement (all tiles blocked in that direction) still spawns a new tile.

---

The limitations were the limitations of a working first draft: no key filtering, silent game over, session-scoped score, a merge bug that rarely triggered, and debug logging left in. The interface responded, tiles moved and merged, the score counted up. The movement algorithm — `getNextPos` and the traversal-order reversal in `moveTiles` — was correct from the start and never needed replacing.
