# Memory Regression — Electron Adapter (Field Guide)

> Snippets below are **pattern fragments**, not complete test files.
> Adapt to the target app's process layout, window and view management, IPC channels, and packaging setup.

## When to Use

Electron desktop apps, including the servers, daemons, CLIs, and bridges the app launches. Pair with [`node.md`](node.md) for main-process and Node child heap work and [`browser.md`](browser.md) for renderer heap and DOM work; this adapter covers what is specific to Electron. For design and review checks, apply [`../resource-cost-checks.md`](../resource-cost-checks.md) first; the lessons below are application decisions, not universal numeric defaults or measured Electron overhead.

## Primary Signals

| Metric | API | What It Catches |
|---|---|---|
| Per-process memory and type | `app.getAppMetrics()` → `memory.workingSetSize`, `privateBytes` (Windows) | Renderer, GPU, and utility growth by process |
| Process memory | `process.getProcessMemoryInfo()` → `private`, `shared`, `residentSet` | Native and private memory of the calling process |
| View → PID mapping | `webContents.getOSProcessId()` | Which window or view owns a renderer |
| Process count by type | `app.getAppMetrics().length`, grouped by `type` | Hidden or orphaned renderers, leaked helpers |
| Node children | OS tools (`ps`, Activity Monitor, Task Manager) by PID | Children started with `child_process`, which are not Chromium-managed |

## Prerequisites

- Measure a **packaged** build. Fuses, the child environment, and launch flags in a packaged app can differ from a dev run.
- Map every process by PID to its owner: main, each renderer and guest view, GPU and utility helpers, and every launched server, daemon, CLI, or bridge.
- Record both the executable **and its execution mode**. One Electron binary can run as the GUI app or, with `ELECTRON_RUN_AS_NODE=1`, as a [plain Node process](https://www.electronjs.org/docs/latest/api/environment-variables#electron_run_as_node). The executable name alone does not identify a renderer.
- Read the [process model](https://www.electronjs.org/docs/latest/tutorial/process-model): each window and embedded view has its own renderer.

## Platform Gotchas

1. **Run-as-node is part of the child's launch contract.** A child launched without the run-as-node setting opened a GUI window instead of speaking its protocol, so the parent timed out and the tools the child provided were missing. Set it where the child is launched, and keep it through any environment filtering or allowlisting. The run-as-node fuse can disable the variable in packaged builds, so verify it there. `utilityProcess` is a documented alternative for Node children.

2. **Check which transport is actually used.** Some clients can connect over HTTP rather than spawning a stdio child. Confirm the real path before optimizing a child that may not run.

3. **Hidden views still hold renderers.** A hidden window or guest view keeps its renderer process and application state. Releasing one is allowed only after explicit guards confirm nothing is lost (unsaved edits, in-progress uploads, active input). A timeout, failure, or unknown answer keeps the view. Restore route and scroll position when it is recreated. A view with no guards is not automatically safe to destroy.

4. **Do not create a renderer to take a thumbnail.** Capture from an already-live, eligible view. After the capture resolves, recheck the view's identity, URL, and navigation state; if it is no longer eligible, keep the previous image.

5. **Send version tokens over recurring IPC, not bytes.** IPC arguments are serialized on every send. Recurring messages carry a version token, and the receiver fetches image or payload bytes only when the token changes. Count serialization and image bytes in the cost estimate.

6. **Share one sampler.** The main process holds one cached sample and one in-flight promise; renderers ask for it over IPC instead of each running their own polling. Invalidate PID-to-owner attribution whenever ownership changes, because PIDs are reused and processes get replaced.

7. **Hidden documents own no polling timer.** Disposing a view removes its listeners and IPC subscriptions, and results that arrive afterwards must not restart its work.

8. **Process replacement and teardown.** Share daemon infrastructure while keeping per-scope state separate. When a process is replaced, only the dead instance's registrations are withdrawn; the old exit handler must check identity so it cannot remove its replacement's. Cancel pending restart work on explicit stop, delete, or quit. A completed HTTP request does not prove a background process is idle (resource-cost-checks check 6).

9. **Units and platform limits.** [`process.getProcessMemoryInfo()`](https://www.electronjs.org/docs/latest/api/process#processgetprocessmemoryinfo) reports in kilobytes, and its fields depend on the platform; the docs explain why macOS provides no `residentSet`. Label every reading with metric, units, PID scope, and platform. Do not compare a footprint figure with an older RSS total, and never count a missing reading as zero.

10. **Summed RSS double-counts.** Shared pages appear in every process that maps them. Prefer private or footprint figures per process over a total of RSS values.

11. **Flags prove nothing alone.** A V8 or Chromium flag such as `--optimize-for-size` in source shows neither a saving nor acceptable latency. Measure the packaged runtime on representative work and on recovery after idle.

## Key API Surface

```javascript
// Pattern fragment: per-process attribution from the main process
const { app, webContents } = require('electron');

const byType = {};
for (const m of app.getAppMetrics()) {          // Chromium-managed processes only
  byType[m.type] = (byType[m.type] ?? 0) + m.memory.workingSetSize; // KB
}

// Map each live view to its renderer PID
const owners = webContents.getAllWebContents().map(wc => ({
  id: wc.id, url: wc.getURL(), pid: wc.getOSProcessId(),
}));

// Private/shared memory of this process (KB; residentSet absent on macOS)
const info = await process.getProcessMemoryInfo();
```

## Measurement Recipe (Pseudocode)

```
build and launch the PACKAGED app
record PID → owner/type/execution-mode map

WARMUP: open and close the target views 2-3x
IDLE: wait for background work to settle
BASELINE: per-process private/footprint + process count by type

STRESS: repeat the open/hide/close or polling flow N times
IDLE: return to idle and wait the same settle time
AFTER: same readings, with the PID map refreshed

ASSERT: process count by type returns to baseline
ASSERT: per-owner private/footprint growth < budget (never summed RSS)
ON FAILURE: renderer heap → browser.md; main or child heap → node.md
```

## Anti-Patterns (Things Agents Must Avoid)

- Measuring a dev build and reporting it as the packaged result
- Summing RSS across processes and calling it app memory
- Treating a missing platform field as zero
- Destroying a hidden view without guards, or recreating it without route and scroll state
- Spawning a renderer only to capture a thumbnail
- Resending image bytes on every recurring IPC message
- Polling per renderer when main already samples
- Using `ipcRenderer.sendSync` or blocking file I/O on the main process ([performance guide](https://www.electronjs.org/docs/latest/tutorial/performance))

## Common Electron Leak Sources

- Hidden windows and guest views kept alive indefinitely
- `ipcMain.handle` / `ipcMain.on` handlers and preload listeners never removed with their view
- Child processes that outlive a quit, or are respawned after an explicit stop
- Stale PID attribution after a process is replaced
- Per-renderer timers still running while the document is hidden

## Failure Diagnosis

| Signal | Next Step |
|---|---|
| Renderer count growing | List `webContents` and owners; find views that are hidden but not released |
| One renderer's memory growing | Heap snapshot of that renderer ([`browser.md`](browser.md)) |
| Main-process memory growing | Check IPC handlers, main-process caches, sampler state ([`node.md`](node.md)) |
| Unknown PIDs growing | Refresh the PID map; check launched children and their execution mode |
| Child missing or timing out | Check run-as-node setting, fuses, and environment filtering on the launch path |

## Agent Adaptation Checklist

Before generating a runnable test, fill in:
- [ ] Packaged build command and launch path
- [ ] PID → owner map, including execution mode of every child
- [ ] Target flow (views to open/hide/close, polling to run)
- [ ] Idle settle time and how idle is proven
- [ ] Metric per platform (private, footprint, committed) and units
- [ ] Budget per owner and per process type
- [ ] Whether this is diagnostic-only or promoted gate
