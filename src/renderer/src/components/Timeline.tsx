export default function Timeline(props: { ops: any[]; logs: string[] }) {
  return (
    <div className="space-y-4 sticky top-5 h-fit">
      <div className="glass p-4">
        <div className="text-xl font-semibold tracking-tight mb-2">Operation Timeline</div>
        <div className="space-y-2 max-h-[340px] overflow-auto pr-1">
          {(props.ops || []).slice().reverse().map((op, i) => (
            <div key={i} className="p-2 rounded-lg bg-white/5 border border-white/10">
              <div className="text-sm font-semibold">{op.operation}</div>
              <div className="text-xs text-zinc-400">{op.timestamp}</div>
            </div>
          ))}
          {(!props.ops || props.ops.length === 0) && (
            <div className="text-zinc-500 text-sm">No ops yet.</div>
          )}
        </div>
      </div>

      <div className="glass p-4">
        <div className="text-xl font-semibold tracking-tight mb-2">Engine Logs</div>
        <pre className="text-[11px] leading-snug text-zinc-300 max-h-[340px] overflow-auto whitespace-pre-wrap">
{props.logs.join('\n')}
        </pre>
      </div>
    </div>
  )
}
