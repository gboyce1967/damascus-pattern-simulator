# Dev Notes — Preferences & Unit System (2026-05-03)

## Overview
Added a **Preferences** dialog accessible from the **File** menu (or `Ctrl+,` / `Cmd+,`)
that lets the user switch between **Metric (mm)** and **Imperial (in)** measurement
display throughout the UI.

## Architecture

### Principle: display-only conversion
The Python engine always works in **millimetres**. The conversion to/from inches
happens exclusively in the renderer's display layer. This avoids any risk of
accumulated rounding errors in the simulation and keeps the engine API unchanged.

Conversion factor: `1 in = 25.4 mm`.

### New files

| File | Purpose |
|------|---------|
| `src/services/preferencesStore.ts` | Persists preferences to `<userData>/preferences.json` via lowdb (same pattern as `projectStore`). |
| `src/renderer/src/lib/units.ts` | Pure conversion helpers: `mmToDisplay`, `displayToMm`, `unitLabel`, `formatLength`, `formatDims`. |
| `src/renderer/src/contexts/PreferencesContext.tsx` | React context providing `unitSystem` + `setUnitSystem` to the component tree. |
| `src/renderer/src/components/PreferencesDialog.tsx` | Modal dialog with radio-button unit selection. |

### Modified files

| File | Change |
|------|--------|
| `src/main/index.ts` | Built a native Electron application menu with **File → Preferences…** that sends `menu:open-preferences` IPC to the renderer. Also adds standard Edit/View/Window menus. |
| `src/main/ipc.ts` | Added `prefs:get` and `prefs:set` IPC handlers. Accepts `PreferencesStore` in its options. |
| `src/preload/index.ts` | Exposed `prefsGet`, `prefsSet`, and `onMenuOpenPreferences` on the `window.damascus` bridge. |
| `src/renderer/src/types/global.d.ts` | Added type declarations for the new bridge methods. |
| `src/renderer/src/main.tsx` | Wrapped `<App>` in `<PreferencesProvider>`. |
| `src/renderer/src/App.tsx` | Imports `formatDims` + `usePreferences`; viewport dims badge uses unit-aware formatting; listens for menu event to open preferences dialog. |
| `src/renderer/src/components/Sidebar.tsx` | All `mm` labels now use `unitLabel()`; slider readouts use `formatLength()`; numeric inputs display/accept values in active unit and convert to mm internally. |
| `src/renderer/src/components/CrossSection.tsx` | Slice-position label uses `formatLength()`. |

## How it works end-to-end

1. **File → Preferences…** (or `Ctrl/Cmd+,`) →  main process sends IPC event
2. Renderer opens `<PreferencesDialog>` modal
3. User picks Metric or Imperial → `setUnitSystem()` updates React context + persists via `prefs:set`
4. All components re-render with new unit labels/values
5. On next launch, `PreferencesProvider` loads saved preference via `prefs:get`

## Debugging tips
- Preferences file lives at `<app.getPath('userData')>/preferences.json`
- Default is `{ "unitSystem": "metric" }` — delete the file to reset
- Engine payloads are always in mm regardless of display unit
