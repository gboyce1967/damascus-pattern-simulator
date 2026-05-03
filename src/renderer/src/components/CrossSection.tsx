import { useState } from 'react'
import { usePreferences } from '../contexts/PreferencesContext'
import { formatLength } from '../lib/units'

export default function CrossSection(props: {
  pngBase64: string | null
  onChange: (ySlice: number, resolution: number) => Promise<void>
}) {
  const { unitSystem } = usePreferences()
  const [y, setY] = useState(0)
  const [res, setRes] = useState(700)

  return (
    <div className="grid grid-cols-[1fr_260px] gap-4 items-start">
      <div className="rounded-xl overflow-hidden border border-white/10 bg-black/30">
        {props.pngBase64 ? (
          <img
            alt="Cross section"
            className="w-full h-[260px] object-contain"
            src={`data:image/png;base64,${props.pngBase64}`}
          />
        ) : (
          <div className="h-[260px] flex items-center justify-center text-zinc-500">Loading…</div>
        )}
      </div>

      <div className="space-y-3">
        <div className="p-3 rounded-xl bg-white/5 border border-white/10">
          <div className="text-sm font-semibold mb-1">Slice position (Y)</div>
          <input
            className="w-full"
            type="range"
            min={-60}
            max={60}
            value={y}
            onChange={(e) => setY(Number(e.target.value))}
          />
          <div className="text-xs text-zinc-400">{formatLength(y, unitSystem, 0)}</div>
        </div>

        <div className="p-3 rounded-xl bg-white/5 border border-white/10">
          <div className="text-sm font-semibold mb-1">Resolution</div>
          <input
            className="w-full"
            type="number"
            min={200}
            max={1200}
            step={50}
            value={res}
            onChange={(e) => setRes(Number(e.target.value))}
          />
          <div className="text-xs text-zinc-400">Higher = sharper but slower</div>
        </div>

        <button
          onClick={() => props.onChange(y, res)}
          className="w-full rounded-lg bg-white/10 hover:bg-white/15 border border-white/10 py-2 text-sm"
        >
          Refresh Slice
        </button>
      </div>
    </div>
  )
}
