---
title: "2048 v3: React, Electron, and Dual Build Targets"
description: "The 2025 migration replaced Flask and Webpack with React, Vite, and Electron — producing both a deployable web app and a cross-platform desktop app from the same codebase. Getting the two targets to share a build without conflicting took most of the first week."
pubDate: "Jun 10 2025"
primaryTag: "Portfolio"
tags: ["React", "Electron", "Vite", "TypeScript", "Django"]
---

The [2023 version](/devlogs/game-2048-ts-engine) was complete as a game. The problem was deployment — it lived inside the Django monolith, which meant updating the game required redeploying the entire backend. The 2025 migration gave it its own deployment target: a React app built with Vite, packaged with Electron for desktop, deployed to Vercel for web, and reverse-proxied into the portfolio at `/projects/game-2048/`. The GSAP animations and SCSS architecture that came with the migration are covered in [the companion devlog](/devlogs/game-2048-gsap-scss).

## Two Build Targets, One Codebase

The same source tree produces two outputs: an Electron desktop app via `electron-vite`, and a static web bundle via a standalone `vite.config.ts`. They share all the React components and game logic but diverge at the build layer.

`electron.vite.config.ts` handles the Electron build — it has separate entry points for the main process, preload script, and renderer. The renderer base is `/` because Electron loads from the local filesystem.

`vite.config.ts` handles the web build — `root` points at `src/renderer/`, `base` is `/projects/game-2048/` so all asset URLs are prefixed with the portfolio subpath, and output goes to `dist/projects/game-2048/`.

The TypeScript config is split to match. A composition-root `tsconfig.json` with no compiler options of its own just references two configs:

```json
{ "files": [], "references": [{ "path": "./tsconfig.node.json" }, { "path": "./tsconfig.web.json" }] }
```

`tsconfig.node.json` covers the Electron main process and preload. `tsconfig.web.json` covers the React renderer with `"jsx": "react-jsx"` (no need to import React in every file) and a `@renderer/*` path alias. Both explicitly set `"module": "esnext"` — the base configs from `@electron-toolkit/tsconfig` weren't setting this, which caused TypeScript to emit CommonJS and break Vite's ESM-native bundler. That was discovered after the first build attempt.

## Electron: Main Process and Preload

The Electron window is 450×860 — portrait, matching a phone-like game interface:

```ts
const mainWindow = new BrowserWindow({
  width: 450, height: 860,
  show: false,
  autoHideMenuBar: true,
  webPreferences: { preload: join(__dirname, '../preload/index.js'), sandbox: false }
})

mainWindow.on('ready-to-show', () => mainWindow.show())
```

`show: false` with `ready-to-show` prevents the white flash that appears when a window renders before the page is loaded. `autoHideMenuBar` hides the native OS menu bar. External links are intercepted and routed to the OS browser rather than opening a new Electron window:

```ts
mainWindow.webContents.setWindowOpenHandler((details) => {
  shell.openExternal(details.url)
  return { action: 'deny' }
})
```

In development the renderer loads from Vite's dev server URL (`ELECTRON_RENDERER_URL`). In production it loads the built `index.html` from the filesystem.

The preload script exposes a flag to the renderer:

```ts
if (process.contextIsolated) {
  contextBridge.exposeInMainWorld('isElectronApp', true)
  contextBridge.exposeInMainWorld('electron', electronAPI)
}
```

`window.isElectronApp` is the switch used throughout the React app to change behaviour between the desktop and web deployments — mainly for asset path resolution, which needed different handling between Electron's `file://` protocol and the web server.

## React Entry: Conditional Basename

The router basename differs between Electron and web:

```tsx
<BrowserRouter basename={window.isElectronApp ? '/' : '/projects/game-2048'}>
```

Electron serves from `/`; the web deployment lives at `/projects/game-2048` on the portfolio server. The same components handle both — the router just needs to know its root.

## App.tsx: API-Driven Content and SEO

All page content comes from the Django API — the game's title, meta description, nav text, score board config, modal copy, button labels, footer text. None of it is hardcoded in the React components.

```tsx
useEffect(() => {
  fetch(`${API_BASE_URL}/projects/game-2048/api/`)
    .then(r => r.json())
    .then(data => {
      setContent(data.content)
      setGlobalContent(data.global_content)
      setLoading(false)
    })
}, [])
```

`react-helmet-async` manages the `<head>` from within the component tree — title, meta description, Open Graph tags, Twitter Card, and canonical URL all populate from the API response. The canonical URL is built from `globalContent.site_url`, so it's correct regardless of which environment the app is running in.

While loading, the page shows an animated skeleton rather than a blank screen. The skeleton block for the game board uses `min(100vw, 100vh)` to match the responsive sizing the real board uses — so the skeleton dimensions are plausible rather than generic.

## GameLayout: Imperative Game on a React Ref

The game engine is still a TypeScript class — not converted to React state. GameLayout bridges the two:

```tsx
const layoutRef = useRef<HTMLDivElement>(null)

useEffect(() => {
  if (layoutRef.current) { new Game2048(layoutRef.current) }
}, [])
```

React renders the full JSX structure — board grid, score display, game-over overlay, arrow buttons — then steps back. The `Game2048` class receives the container ref and takes ownership of all DOM event handling and tile manipulation from that point. React doesn't re-render when tiles move; the class mutates the DOM directly. This keeps the game logic unchanged from the 2023 version rather than rewriting it as React state.

The arrow buttons in the JSX come from the API: `content.game_nav.arrow_btns` — an array with direction, SVG chevron, and label per entry. The game class attaches click handlers to them by class name after mount.

## The Base URL Problem

Getting asset paths to work across both targets took five commits over two days. The core issue: Electron resolves paths relative to the loaded file's location on the filesystem; the web server resolves them relative to the configured base URL. A path that works in one breaks in the other.

The SVG icon sprite (`icons.svg`) was the most visible failure — SVG `<use>` references need absolute or base-relative paths on web but relative paths in Electron. The first solution was a `baseUrl` variable per component:

```tsx
const baseUrl = window.isElectronApp ? '' : '/'
<use xlinkHref={`${baseUrl}images/icons.svg#chevron-up`} />
```

Once `vite.config.ts` base was confirmed as `/projects/game-2048` and server routing was set up correctly, this conditional was no longer needed — bare relative paths work in both environments — and the `baseUrl` logic was removed. The final state is the simplest one; the path to get there was not.

The API base URL went through a similar process: local dev server → production `.tech` domain → trailing slash removed (double slashes in API calls) → `.com` domain four months later after the portfolio moved domains.

---

The migration produced a project that can ship and update independently. A push to the Vercel deployment updates the web version; an `electron-builder` run produces installers for Windows, Mac, and Linux. Neither requires touching the Django backend.
