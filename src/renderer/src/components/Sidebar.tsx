import { useState } from 'react'
import { usePreferences } from '../contexts/PreferencesContext'
import { mmToDisplay, displayToMm, unitLabel, formatLength } from '../lib/units'

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
  onOp: (op: string, payload?: any) => Promise<void>
  onExport: () => Promise<void>
}) {
  const { unitSystem } = usePreferences()
  const u = unitLabel(unitSystem)

  // All slider/input state is stored in mm internally
  const [wedgeDepth, setWedgeDepth] = useState(18)
  const [wedgeAngle, setWedgeAngle] = useState(35)
  const [splitGap, setSplitGap] = useState(6)

  const [twistCount, setTwistCount] = useState(1)

  const [sqBarSize, setSqBarSize] = useState(15)
  const [sqHeats, setSqHeats] = useState(5)

  const [octBarSize, setOctBarSize] = useState(15)
  const [octHeats, setOctHeats] = useState(5)
  const [octChamfer, setOctChamfer] = useState(15)

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

          <label className="text-xs text-zinc-400 mt-2 block">Chamfer %</label>
          <input className="w-full" type="range" min={5} max={30} value={octChamfer}
            onChange={e => setOctChamfer(Number(e.target.value))} />
          <div className="text-xs text-zinc-300">{octChamfer}%</div>

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
          <input className="w-full" type="range" min={0} max={30} step={1} value={twistCount}
            onChange={e => setTwistCount(Number(e.target.value))} />
          <div className="text-xs text-zinc-300">{twistCount} {twistCount === 1 ? 'twist' : 'twists'} ({twistCount * 360}°)</div>

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
