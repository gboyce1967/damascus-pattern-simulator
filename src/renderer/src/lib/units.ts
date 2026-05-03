/**
 * Unit conversion utilities for metric ↔ imperial display.
 *
 * The engine ALWAYS works in millimetres. These helpers convert values
 * for display and accept user input in the active unit system.
 *
 * Metric:   mm  (millimetres)  /  m  (metres, when ≥ 1 000 mm)
 * Imperial: in  (inches)       /  ft (feet, when ≥ 12 in)
 *
 * In practice all billet dimensions in this app are well under 1 m / 3 ft,
 * so the "small" unit (mm or in) is used almost exclusively.
 */

export type UnitSystem = 'metric' | 'imperial'

const MM_PER_INCH = 25.4

// ── Conversion helpers ──────────────────────────────────────────────

/** Convert a value **from mm** to the display unit. */
export function mmToDisplay(mm: number, system: UnitSystem): number {
  if (system === 'imperial') return mm / MM_PER_INCH
  return mm
}

/** Convert a value **from the display unit** back to mm (for the engine). */
export function displayToMm(value: number, system: UnitSystem): number {
  if (system === 'imperial') return value * MM_PER_INCH
  return value
}

// ── Label helpers ───────────────────────────────────────────────────

/** Short unit label for lengths (e.g. "mm" or "in"). */
export function unitLabel(system: UnitSystem): string {
  return system === 'imperial' ? 'in' : 'mm'
}

/** Format a mm value for display, including the unit suffix. */
export function formatLength(mm: number, system: UnitSystem, decimals = 1): string {
  const v = mmToDisplay(mm, system)
  return `${v.toFixed(decimals)} ${unitLabel(system)}`
}

/**
 * Format billet dimensions string (w × l × h) in the active unit system.
 * Accepts values that are already in mm.
 */
export function formatDims(
  w_mm: number,
  l_mm: number,
  h_mm: number,
  system: UnitSystem,
  decimals = 1
): string {
  const u = unitLabel(system)
  const w = mmToDisplay(w_mm, system).toFixed(decimals)
  const l = mmToDisplay(l_mm, system).toFixed(decimals)
  const h = mmToDisplay(h_mm, system).toFixed(decimals)
  return `${w}×${l}×${h} ${u}`
}
