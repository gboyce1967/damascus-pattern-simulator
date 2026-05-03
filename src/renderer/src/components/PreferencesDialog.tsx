import { usePreferences } from '../contexts/PreferencesContext'
import type { UnitSystem } from '../lib/units'

const UNIT_OPTIONS: { value: UnitSystem; label: string; desc: string }[] = [
  { value: 'metric', label: 'Metric', desc: 'Millimetres / Metres' },
  { value: 'imperial', label: 'Imperial', desc: 'Inches / Feet' }
]

export default function PreferencesDialog({ onClose }: { onClose: () => void }) {
  const { unitSystem, setUnitSystem } = usePreferences()

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-[420px] rounded-2xl border border-white/10 bg-[#111118] shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
          <h2 className="text-lg font-semibold tracking-tight">Preferences</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-zinc-400 hover:bg-white/10 hover:text-white"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="px-5 py-5 space-y-4">
          <div>
            <div className="text-sm font-semibold mb-2">Measurement Units</div>
            <div className="space-y-2">
              {UNIT_OPTIONS.map((opt) => (
                <label
                  key={opt.value}
                  className={`flex items-center gap-3 rounded-xl border p-3 cursor-pointer transition
                    ${unitSystem === opt.value
                      ? 'border-blue-500/60 bg-blue-500/10'
                      : 'border-white/10 bg-white/5 hover:bg-white/10'
                    }`}
                >
                  <input
                    type="radio"
                    name="unitSystem"
                    value={opt.value}
                    checked={unitSystem === opt.value}
                    onChange={() => setUnitSystem(opt.value)}
                    className="accent-blue-500"
                  />
                  <div>
                    <div className="text-sm font-medium">{opt.label}</div>
                    <div className="text-xs text-zinc-400">{opt.desc}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end border-t border-white/10 px-5 py-3">
          <button
            onClick={onClose}
            className="rounded-lg bg-white/10 hover:bg-white/15 border border-white/10 px-5 py-2 text-sm"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  )
}
