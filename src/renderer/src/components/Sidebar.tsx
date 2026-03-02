import { useState } from 'react'

export default function Sidebar(props: {
  ready: boolean
  sessionId: string | null
  onOp: (op: string, payload?: any) => Promise<void>
  onExport: () => Promise<void>
}) {
  const [wedgeDepth, setWedgeDepth] = useState(18)
  const [wedgeAngle, setWedgeAngle] = useState(35)
  const [splitGap, setSplitGap] = useState(6)

  const [twistAngle, setTwistAngle] = useState(180)

  const [barSize, setBarSize] = useState(15)
  const [heats, setHeats] = useState(5)

  return (
    <div className="glass p-4 h-fit sticky top-5">
      <div className="mb-4">
        <div className="text-2xl font-semibold tracking-tight">Damascus Builder 3D</div>
        <div className="text-xs text-zinc-400 mt-1">
          Electron + Tailwind UI • Python Open3D engine
        </div>
      </div>

      <div className="space-y-4">
        <section className="p-3 rounded-xl bg-white/5 border border-white/10">
          <div className="font-semibold mb-2">Feather (Wedge Split)</div>

          <label className="text-xs text-zinc-400">Depth (mm)</label>
          <input className="w-full" type="range" min={5} max={30} value={wedgeDepth}
            onChange={e => setWedgeDepth(Number(e.target.value))} />
          <div className="text-xs text-zinc-300 mb-2">{wedgeDepth} mm</div>

          <label className="text-xs text-zinc-400">Angle (°)</label>
          <input className="w-full" type="range" min={10} max={60} value={wedgeAngle}
            onChange={e => setWedgeAngle(Number(e.target.value))} />
          <div className="text-xs text-zinc-300 mb-2">{wedgeAngle}°</div>

          <label className="text-xs text-zinc-400">Split gap (mm)</label>
          <input className="w-full" type="range" min={0} max={12} value={splitGap}
            onChange={e => setSplitGap(Number(e.target.value))} />
          <div className="text-xs text-zinc-300">{splitGap} mm</div>

          <button
            disabled={!props.ready}
            onClick={() => props.onOp('wedge', { wedge_depth: wedgeDepth, wedge_angle: wedgeAngle, split_gap: splitGap })}
            className="mt-3 w-full rounded-lg bg-white/10 hover:bg-white/15 border border-white/10 py-2 text-sm"
          >
            Apply Wedge
          </button>
        </section>

        <section className="p-3 rounded-xl bg-white/5 border border-white/10">
          <div className="font-semibold mb-2">Forge to Bar (volume conserving)</div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-xs text-zinc-400">Bar size (mm)</label>
              <input className="w-full" type="number" value={barSize} onChange={e => setBarSize(Number(e.target.value))} />
            </div>
            <div>
              <label className="text-xs text-zinc-400">Heats</label>
              <input className="w-full" type="number" value={heats} onChange={e => setHeats(Number(e.target.value))} />
            </div>
          </div>

          <button
            disabled={!props.ready}
            onClick={() => props.onOp('forge_square', { target_bar_size: barSize, num_heats: heats })}
            className="mt-3 w-full rounded-lg bg-white/10 hover:bg-white/15 border border-white/10 py-2 text-sm"
          >
            Forge to Square
          </button>
        </section>

        <section className="p-3 rounded-xl bg-white/5 border border-white/10">
          <div className="font-semibold mb-2">Twist</div>

          <label className="text-xs text-zinc-400">Total twist (°)</label>
          <input className="w-full" type="range" min={0} max={720} value={twistAngle}
            onChange={e => setTwistAngle(Number(e.target.value))} />
          <div className="text-xs text-zinc-300">{twistAngle}°</div>

          <button
            disabled={!props.ready}
            onClick={() => props.onOp('twist', { angle_degrees: twistAngle })}
            className="mt-3 w-full rounded-lg bg-white/10 hover:bg-white/15 border border-white/10 py-2 text-sm"
          >
            Apply Twist
          </button>
        </section>

        <section className="p-3 rounded-xl bg-white/5 border border-white/10">
          <div className="font-semibold mb-2">Export</div>
          <button
            disabled={!props.ready}
            onClick={() => props.onExport()}
            className="w-full rounded-lg bg-white/10 hover:bg-white/15 border border-white/10 py-2 text-sm"
          >
            Export merged OBJ/STL/PLY…
          </button>
        </section>
      </div>
    </div>
  )
}
