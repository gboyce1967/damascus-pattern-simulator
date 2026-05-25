import { useState } from 'react'
import { usePreferences } from '../contexts/PreferencesContext'
import { mmToDisplay, displayToMm, unitLabel, formatLength } from '../lib/units'

const DEFAULT_OCTAGON_CHAMFER_PERCENT = 45
const REGULAR_OCTAGON_CHAMFER_PERCENT = 58.6
const MIN_OCTAGON_CHAMFER_PERCENT = 5
const MAX_OCTAGON_CHAMFER_PERCENT = 75
const MM_PER_INCH = 25.4
const DEFAULT_TWIST_COUNT = 1
const DEFAULT_TWIST_SLIDER_MAX = 30
const MAX_TWIST_COUNT = 1000
const STANDARD_TWISTS_PER_INCH_MIN = 3
const STANDARD_TWISTS_PER_INCH_MAX = 4
const TURKISH_TWISTS_PER_INCH_MIN = 5
const TURKISH_TWISTS_PER_INCH_MAX = 10

function clampOctChamfer(value: number) {
  if (!Number.isFinite(value)) return DEFAULT_OCTAGON_CHAMFER_PERCENT
  return Math.min(MAX_OCTAGON_CHAMFER_PERCENT, Math.max(MIN_OCTAGON_CHAMFER_PERCENT, value))
}
function clampTwistCount(value: number) {
  if (!Number.isFinite(value)) return DEFAULT_TWIST_COUNT
  return Math.min(MAX_TWIST_COUNT, Math.max(0, value))
}

function formatTwistValue(value: number, decimals = 2) {
  return value.toFixed(decimals).replace(/\.0+$/, '').replace(/(\.\d*?)0+$/, '$1')
}

function Section({ title, defaultOpen = true, children }: { title: string; defaultOpen?: boolean; children: React.ReactNode }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <section className="rounded-xl bg-white/5 border border-white/10">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between p-3 text-left"
      >
        <span className="font-semibold">{title}</span>
        <span className={`text-zinc-400 text-xs transition-transform ${open ? 'rotate-90' : ''}`}>▶</span>
      </button>
      {open && <div className="px-3 pb-3">{children}</div>}
    </section>
  )
}

export default function Sidebar(props: {
  ready: boolean
  sessionId: string | null
  billetLengthMm: number | null
  onOp: (op: string, payload?: any) => Promise<void>
  onExport: () => Promise<void>
}) {
  const { unitSystem } = usePreferences()
  const u = unitLabel(unitSystem)

  // All slider/input state is stored in mm internally
  const [wedgeDepth, setWedgeDepth] = useState(18)
  const [wedgeAngle, setWedgeAngle] = useState(35)
  const [splitGap, setSplitGap] = useState(6)

  const [twistCount, setTwistCount] = useState(DEFAULT_TWIST_COUNT)

  const [sqBarSize, setSqBarSize] = useState(15)
  const [sqHeats, setSqHeats] = useState(5)

  const [octBarSize, setOctBarSize] = useState(15)
  const [octHeats, setOctHeats] = useState(5)
  const [octChamfer, setOctChamfer] = useState(DEFAULT_OCTAGON_CHAMFER_PERCENT)

  const updateOctChamfer = (value: number) => setOctChamfer(clampOctChamfer(value))
  const updateTwistCount = (value: number) => setTwistCount(clampTwistCount(value))
  const billetLengthInches = props.billetLengthMm && props.billetLengthMm > 0
    ? props.billetLengthMm / MM_PER_INCH
    : null
  const standardTwistRange = billetLengthInches
    ? {
        min: billetLengthInches * STANDARD_TWISTS_PER_INCH_MIN,
        max: billetLengthInches * STANDARD_TWISTS_PER_INCH_MAX,
      }
    : null
  const turkishTwistRange = billetLengthInches
    ? {
        min: billetLengthInches * TURKISH_TWISTS_PER_INCH_MIN,
        max: billetLengthInches * TURKISH_TWISTS_PER_INCH_MAX,
      }
    : null
  const twistDensity = billetLengthInches ? twistCount / billetLengthInches : null
  const twistSliderMax = Math.max(
    DEFAULT_TWIST_SLIDER_MAX,
    Math.ceil(turkishTwistRange?.max ?? 0),
    Math.ceil(twistCount),
  )

  return (
    <div className="glass p-4 overflow-y-auto">
      <div className="mb-4">
        <div className="text-2xl font-semibold tracking-tight">Damascus Builder 3D</div>
        <div className="text-xs text-zinc-400 mt-1">
          Electron + Tailwind UI • Python Open3D engine
        </div>
      </div>

      <div className="space-y-4">
        <Section title="Feather (Wedge Split)" defaultOpen={false}>
          <label className="text-xs text-zinc-400">Depth ({u})</label>
          <input className="w-full" type="range" min={5} max={30} value={wedgeDepth}
            onChange={e => setWedgeDepth(Number(e.target.value))} />
          <div className="text-xs text-zinc-300 mb-2">{formatLength(wedgeDepth, unitSystem)}</div>

          <label className="text-xs text-zinc-400">Angle (°)</label>
          <input className="w-full" type="range" min={10} max={60} value={wedgeAngle}
            onChange={e => setWedgeAngle(Number(e.target.value))} />
          <div className="text-xs text-zinc-300 mb-2">{wedgeAngle}°</div>

          <label className="text-xs text-zinc-400">Split gap ({u})</label>
          <input className="w-full" type="range" min={0} max={12} value={splitGap}
            onChange={e => setSplitGap(Number(e.target.value))} />
          <div className="text-xs text-zinc-300">{formatLength(splitGap, unitSystem)}</div>

          <button
            disabled={!props.ready}
            onClick={() => props.onOp('wedge', { wedge_depth: wedgeDepth, wedge_angle: wedgeAngle, split_gap: splitGap })}
            className="mt-3 w-full rounded-lg bg-white/10 hover:bg-white/15 border border-white/10 py-2 text-sm"
          >
            Apply Wedge
          </button>
        </Section>

        <Section title="Forge to Square Bar">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-xs text-zinc-400">Bar size ({u})</label>
              <input className="w-full" type="number"
                value={parseFloat(mmToDisplay(sqBarSize, unitSystem).toFixed(2))}
                onChange={e => setSqBarSize(displayToMm(Number(e.target.value), unitSystem))} />
            </div>
            <div>
              <label className="text-xs text-zinc-400">Heats</label>
              <input className="w-full" type="number" value={sqHeats} onChange={e => setSqHeats(Number(e.target.value))} />
            </div>
          </div>

          <button
            disabled={!props.ready}
            onClick={() => props.onOp('forge_square', { target_bar_size: sqBarSize, num_heats: sqHeats })}
            className="mt-3 w-full rounded-lg bg-white/10 hover:bg-white/15 border border-white/10 py-2 text-sm"
          >
            Forge to Square
          </button>
        </Section>

        <Section title="Forge to Octagonal Bar">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-xs text-zinc-400">Bar size ({u})</label>
              <input className="w-full" type="number"
                value={parseFloat(mmToDisplay(octBarSize, unitSystem).toFixed(2))}
                onChange={e => setOctBarSize(displayToMm(Number(e.target.value), unitSystem))} />
            </div>
            <div>
              <label className="text-xs text-zinc-400">Heats</label>
              <input className="w-full" type="number" value={octHeats} onChange={e => setOctHeats(Number(e.target.value))} />
            </div>
          </div>

          <label className="text-xs text-zinc-400 mt-2 block">Die angle (Chamfor)</label>
          <input className="w-full" type="range"
            min={MIN_OCTAGON_CHAMFER_PERCENT}
            max={MAX_OCTAGON_CHAMFER_PERCENT}
            step={0.1}
            value={octChamfer}
            onChange={e => updateOctChamfer(Number(e.target.value))} />
          <div className="mt-2 grid grid-cols-2 gap-2 items-end">
            <div>
              <label className="text-xs text-zinc-400">Chamfor %</label>
              <input className="w-full" type="number"
                min={MIN_OCTAGON_CHAMFER_PERCENT}
                max={MAX_OCTAGON_CHAMFER_PERCENT}
                step={0.1}
                value={Number(octChamfer.toFixed(1))}
                onChange={e => updateOctChamfer(Number(e.target.value))} />
            </div>
            <div className="text-xs text-zinc-300 pb-2">
              {REGULAR_OCTAGON_CHAMFER_PERCENT.toFixed(1)}% = regular octagon
            </div>
          </div>

          <button
            disabled={!props.ready}
            onClick={() => props.onOp('forge_octagon', { target_bar_size: octBarSize, num_heats: octHeats, chamfer_percent: octChamfer })}
            className="mt-3 w-full rounded-lg bg-white/10 hover:bg-white/15 border border-white/10 py-2 text-sm"
          >
            Forge to Octagon
          </button>
        </Section>

        <Section title="Twist">
          <label className="text-xs text-zinc-400">Full twists</label>
          <input className="w-full" type="range" min={0} max={twistSliderMax} step={0.25} value={twistCount}
            onChange={e => updateTwistCount(Number(e.target.value))} />
          <div className="mt-2 grid grid-cols-2 gap-2 items-end">
            <div>
              <label className="text-xs text-zinc-400">Twists</label>
              <input className="w-full" type="number"
                min={0}
                max={MAX_TWIST_COUNT}
                step={0.25}
                value={Number(twistCount.toFixed(2))}
                onChange={e => updateTwistCount(Number(e.target.value))} />
            </div>
            <div className="text-xs text-zinc-300 pb-2">
              {formatTwistValue(twistCount)} {twistCount === 1 ? 'twist' : 'twists'} ({formatTwistValue(twistCount * 360, 1)}°)
            </div>
          </div>

          <div className="mt-2 rounded-lg bg-black/20 border border-white/10 p-2 text-xs text-zinc-300 space-y-1">
            <div className="font-medium text-zinc-200">Twist guidelines</div>
            <div>Standard: 3–4 twists/in • Turkish: 5–10 twists/in</div>
            {billetLengthInches && standardTwistRange && turkishTwistRange ? (
              <div>
                Current length {formatLength(props.billetLengthMm, unitSystem)} ({billetLengthInches.toFixed(2)} in):
                standard {formatTwistValue(standardTwistRange.min, 1)}–{formatTwistValue(standardTwistRange.max, 1)} twists,
                Turkish {formatTwistValue(turkishTwistRange.min, 1)}–{formatTwistValue(turkishTwistRange.max, 1)} twists.
                Selected: {formatTwistValue(twistDensity ?? 0, 2)} twists/in.
              </div>
            ) : (
              <div>Create or load a billet to calculate total twist ranges.</div>
            )}
          </div>

          <button
            disabled={!props.ready}
            onClick={() => props.onOp('twist', { angle_degrees: twistCount * 360 })}
            className="mt-3 w-full rounded-lg bg-white/10 hover:bg-white/15 border border-white/10 py-2 text-sm"
          >
            Apply Twist
          </button>
        </Section>

        <Section title="Export">
          <button
            disabled={!props.ready}
            onClick={() => props.onExport()}
            className="w-full rounded-lg bg-white/10 hover:bg-white/15 border border-white/10 py-2 text-sm"
          >
            Export merged OBJ/STL/PLY…
          </button>
        </Section>
      </div>
    </div>
  )
}
