---
title: "2048 v2: Webpack, SCSS Architecture, and Flask Templates"
description: "The build side of the 2023 rewrite — Webpack with ts-loader and sass-loader, modular SCSS replacing 11 hardcoded CSS blocks with a single @each loop, Flask serving data-driven Jinja2 templates, and a week of Flask/Werkzeug version troubleshooting."
pubDate: "Oct 15 2023"
primaryTag: "Portfolio"
tags: ["Webpack", "SCSS", "Flask", "TypeScript"]
---

October 2023 rebuilt the 2048 game from a blank repo — everything from the 2021 prototype was deleted in a single commit before the rewrite started. The TypeScript game engine changes are in [the companion devlog](/devlogs/game-2048-ts-engine). This is about the build toolchain, SCSS architecture, Flask templates, and the week of deployment configuration that followed.

## The Webpack Setup

The 2021 version had no build step — `index.html` loaded `app.js` and `app.css` directly. The rewrite introduced Webpack with separate dev and prod configs.

`webpack.config.js` has two entry points:

```js
entry: ['./src/index.ts', './src/index.scss'],
output: { filename: 'index.min.js', path: './src/static' }
```

TypeScript and SCSS both go through Webpack. `ts-loader` compiles TypeScript, `sass-loader` compiles SCSS, `css-loader` processes the result, and `MiniCssExtractPlugin` writes it to `index.min.css` alongside `index.min.js` in `src/static/`. Flask serves that directory as static files.

`webpack.prod.js` is minimal — it merges the dev config and disables source maps:

```js
const { merge } = require('webpack-merge');
const devConfig = require('./webpack.config');
module.exports = merge(devConfig, { mode: 'production', devtool: false });
```

The dev config runs with `devtool: 'inline-source-map'` — source maps embedded in the bundle for browser devtools. Production strips them.

BrowserSync is loaded conditionally — only when `--mode development` is passed:

```js
if (process.argv[process.argv.indexOf('--mode') + 1] === 'development') {
  const BrowserSyncPlugin = require('browser-sync-webpack-plugin');
  config.plugins.push(new BrowserSyncPlugin({
    proxy: 'http://127.0.0.1:8080/',
    open: false, notify: false,
    files: ['src/static/**'],
  }));
}
```

This means production builds don't require `browser-sync-webpack-plugin` to be installed. Earlier in the phase BrowserSync was always imported at the top of the config file — conditional loading was the final architecture decision of the phase.

The dev npm script runs both Webpack watch and the Flask server simultaneously:

```json
"dev": "webpack --watch --config webpack.config.js --mode development & python3 src/app.py"
```

The `&` runs both processes in parallel — Webpack recompiles TypeScript and SCSS on every file save, BrowserSync refreshes the browser when `src/static/` changes, and Flask serves the result.

## ESLint

ESLint with `standard-with-typescript` was added alongside the game code:

```json
{
  "env": { "browser": true, "es2021": true },
  "extends": "standard-with-typescript",
  "rules": {
    "@typescript-eslint/indent": ["error", 2, { "SwitchCase": 1 }],
    "@typescript-eslint/explicit-function-return-type": "off",
    "@typescript-eslint/ban-types": ["error", { "types": { "Object": false, "Function": false } }}],
    "no-trailing-spaces": ["error", { "skipBlankLines": true }]
  }
}
```

2-space indentation enforced. `explicit-function-return-type` turned off — return types are inferred where possible. `Object` and `Function` as types are explicitly allowed, overriding the standard preset's ban. The lint script runs across all TypeScript source files: `eslint ./src/**/**.ts`.

## Flask: Content-Driven Templates

Flask does very little, but it does it more deliberately than the 2021 version. The route passes a `content` dict to the template:

```python
@app.route("/game-2048/")
def game_2048():
    content = {
        'site_name': '2048 Game',
        'game_nav': {
            'title': '2048',
            'score_board': [
                {'title': 'Score', 'value': 0, 'class_name': 'js-game-score'},
                {'title': 'Best Score', 'value': 0, 'class_name': 'js-best-score'}
            ]
        },
        'board_size': 4,
        'gameover_details': {
            'title': 'Game Over',
            'play_again_button': 'Play Again'
        }
    }
    return render_template('pages/game-2048.jinja', content=content)
```

All text — score labels, button copy, game title — comes from Python. The Jinja2 template generates the grid from `board_size` instead of hardcoding 16 cells:

```jinja
{% set board_size = content.board_size|int %}
<div class="board-grid">
  {% for row in range(board_size) %}
    <div class="grid-row">
      {% for col in range(board_size) %}
        <div class="grid-cell"></div>
      {% endfor %}
    </div>
  {% endfor %}
</div>
```

The game-over overlay is a real UI element now — a `<section class="gameover-container">` with a "Play Again" button, rendered into the template from `content.gameover_details`. When the game ends, JavaScript sets a `data-game-over` attribute on the body; CSS handles the rest.

## SCSS Architecture

The 2021 stylesheet was 211 lines of flat CSS with 11 identical `::after` blocks, one per tile value, all hardcoded. The rewrite splits styling into five files with a clear separation of concerns.

`global-colors.scss` defines the tile palette as a SCSS list:

```scss
$tiles:
  "2" #eee4da,
  "4" #ede0c8,
  "8" #f2b179,
  // ...
  "2048" #edc22e;
```

`global-vars.scss` derives cell size from board size proportionally:

```scss
$board-side: 500px;
$box-side: $board-side * 0.22;
$box-size: $board-side * 0.25;
```

Board size went from 450px to 500px. Cell dimensions are computed percentages of the board — not hardcoded `99px` values. Change `$board-side` and everything scales.

`global-mixins.scss` defines two mixins used throughout:

```scss
@mixin flex-center($direction: row) {
  align-items: center; display: flex;
  flex-direction: $direction; justify-content: center;
}

@mixin keyframes($name) {
  @keyframes #{$name} { @content; }
  @-o-keyframes #{$name} { @content; }
  @-moz-keyframes #{$name} { @content; }
}
```

`flex-center` replaces repetitive flexbox declarations. The `keyframes` mixin wraps every animation definition with vendor prefixes automatically.

`grid-board.scss` handles the board layout and the game-over overlay. The z-index stack that was manually written as four `:nth-child` rules in the 2021 CSS becomes a loop:

```scss
@for $i from 1 through 4 {
  &:nth-child(#{$i}) { z-index: 5 - $i; }
}
```

The overlay visibility is driven entirely by a data attribute:

```scss
.gameover-container { display: none; }
[data-game-over] .gameover-container { display: flex; }
[data-game-over] .board-grid { opacity: 0.4; }
```

No JavaScript class toggling needed — setting `data-game-over` on the body triggers both the overlay appearance and the board dimming in one attribute change.

## grid-tiles.scss: The @each Loop

The biggest improvement in the stylesheet. The 2021 CSS had 11 separate `.tile-N::after` blocks with hardcoded values repeated in each. The rewrite generates all of them from a single loop:

```scss
@each $tile-num, $bg-color in colors.$tiles {
  .tile-#{$tile-num} {
    &::after {
      background: $bg-color;
      content: $tile-num;

      @if $tile-num == "2" or $tile-num == "4" { color: colors.$box-font-color1; }
      @else { color: colors.$box-font-color2; }

      @if str-length($tile-num) == 1 { font-size: 50px; }
      @else if str-length($tile-num) == 2 { font-size: 42px; }
      @else if str-length($tile-num) == 3 { font-size: 38px; }
      @else if str-length($tile-num) == 4 { font-size: 34px; }
    }

    &.tile-updated { animation: createBox .25s; }
  }
}
```

Text color, font size, and background all derive from the tile value — no per-tile duplication. Adding a new tile value means adding one entry to `$tiles` in `global-colors.scss`. The `tile-updated` animation is scoped to the class, not the pseudo-element, so it only plays when the class is explicitly added by JavaScript.

## Deployment: Flask/Werkzeug Version Conflicts

Getting Flask running on the deployment environment took six commits across two days. Flask 2.3.x, 2.2.x, and 2.1.x were each tried; Werkzeug went through `2.3.7` and `2.2.3`; gunicorn went from `20.1.0` to `19.7.1` and back. At one point `requirements.txt` expanded to the full `pip freeze` output — nine packages — before being stripped back to three.

The root issue was the Flask/Werkzeug version pairing. Flask 2.1.x requires Werkzeug 2.x but there were incompatibilities between specific minor versions on the target platform. The final settled combination was `Flask==2.1.0` + `gunicorn==20.1.0` + `Werkzeug==2.2.3`.

Build artifact handling went through a similar cycle. Committing the built `index.min.css` and `index.min.js` was tried (so deployment environments without Node.js could serve them directly), then reversed — a glob pattern `**/index.min.**` was added to `.gitignore` as the final position. Source only, build in CI.

---

The week from October 8 to 15 took a blank repo to a working, linted, hot-reloading local dev setup with a proper build pipeline — Webpack bundling TypeScript and SCSS, Flask serving the result, ESLint enforcing consistency. The 2021 version had none of that scaffolding. Everything the 2025 migration built on top of was established here.
