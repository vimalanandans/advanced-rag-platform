# AI-Native Workspace Product-UX Guide

## Purpose and scope

The Studio is an English (US), local-first engineering workspace. Its main job is focused RAG pipeline work; AI assistance, diagnostics, models, token data, and traces support that work rather than displacing it. This guide governs Studio changes only and does not alter platform/runtime contracts.

## Product principles

1. **Work first.** The active canvas is the primary surface; navigation is stable on the left and contextual tools appear on the right.
2. **AI is contextual.** Every AI action names and displays its scope. AI output is always a reviewable ChangeSet, never an automatic mutation.
3. **Progressive disclosure.** Normal operation is quiet. Traces, provider details, token usage, raw diagnostics, and experiments stay one interaction away.
4. **Trust is visible.** Save/sync state, local storage, privacy, recovery, data sharing, and reference scope have plain-language explanations.
5. **Control and reversibility.** Users can preview, accept, revise, reject, cancel, and undo an AI proposal. Closing a panel never discards a draft.
6. **Accessible efficiency.** Keyboard shortcuts complement visible controls; focus remains coherent; motion is restrained and respects reduced-motion preferences.

## Required shell

- `AppShell` persists the sidebar state, context drawer mode/width/open tab, and current canvas context in browser storage.
- `NavigationSidebar` holds workspace identity, project navigation, search, creation, favorites/recent items, and utility links. A collapsed rail keeps recognizable icon labels via tooltips and `aria-label`s.
- `PrimaryCanvas` owns breadcrumbs, item identity, selection, undo/redo affordances, and the canvas-specific working area. It must not inherit editor-only controls.
- `ContextDrawer` is docked on large displays or an overlay on constrained displays. It offers Assistant, Inspector, Activity, Versions, and Diagnostics. It is resizable, collapsible, and remembers the last tab.
- `CommandPalette` is optional and contextual. `Escape` closes the most recent transient UI first.
- `SyncStatus` reports quiet local save; it calls attention only to offline, syncing, conflict, or backup failure.

## AI interaction requirements

- Show context chips such as “Pipeline baseline”, “Selected node: dense”, or “Approved references only”. Chips can be removed and scope is inspectable before submission.
- Selection actions must be relevant and compact. For pipelines, examples are Explain, Compare, Improve, and Generate regression test.
- Stream or display generated content as an `AIChangeSet` distinct from saved work. Provide Accept, Reject, Revise, Cancel, Diff, and Undo. `Tab`/`Escape` may accept/reject only when visible buttons are also available.
- Assistant run details are collapsed by default and include model/provider, sources, duration, token usage, errors, and trace ID when available.

## Data & Trust requirements

- Local save is optimistic. Browser preferences/drafts are local-only unless a future sync adapter explicitly changes that behavior.
- Do not store long-lived provider credentials in browser storage. The current Studio uses a local-admin API token only for local development and labels it accordingly.
- Explain where data is saved, what AI receives, whether the user is offline/synced, and how recovery works.
- Diagnostics/export must redact credentials and private request content by default.

## Visual and interaction system

- Use original neutral surfaces, a single blue-green accent, readable system typography, thin borders, compact sidebars, and generous center-canvas space.
- Define CSS tokens for colors, spacing, radius, elevation, type, panel widths, and motion. Do not copy external product branding, labels, geometry, assets, or styling.
- Persistent panel motion uses 120–260 ms ease-out transitions. Reduced-motion mode uses instant state changes.
- Desktop uses the three-region shell; narrow screens use a compact rail and overlay drawer/sheet rather than three columns.

## Definition of done for Studio UX work

- New surface behavior follows this guide and has accessible labels, keyboard behavior, responsive behavior, and reduced-motion support.
- AI-affecting UI identifies scope and cannot silently modify saved content.
- State persistence has a safe fallback when browser storage is unavailable.
- In local development, use the Studio `/api` proxy rather than hard-coding a cross-origin API URL. Direct local API
  origins must be explicitly permitted through the API CORS policy.
- The Studio TypeScript production build succeeds. UI-only work must not require backend contract changes.
