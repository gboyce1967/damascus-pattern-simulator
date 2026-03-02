import { useEffect, useMemo, useState } from 'react'
import Sidebar from './components/Sidebar'
import Viewport3D from './components/Viewport3D'
import CrossSection from './components/CrossSection'
import Timeline from './components/Timeline'

type MeshPayload = {
  session_id: string
  dims: { width_mm: number; length_mm: number; height_mm: number }
  layers: Array<{ color: [number, number, number]; vertices: number[]; triangles: number[] }>
}

export default function App() {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [mesh, setMesh] = useState<MeshPayload | null>(null)
  const [ops, setOps] = useState<any[]>([])
  const [crossPng, setCrossPng] = useState<string | null>(null)
  const [logs, setLogs] = useState<string[]>([])

  const ready = useMemo(() => !!sessionId, [sessionId])

  async function refreshAll(id: string) {
    const m = await window.damascus.mesh(id)
    setMesh(m)

    const cs = await window.damascus.crossSection(id, { y_slice: 0, resolution: 700 })
    setCrossPng(cs.png_base64)

    const st = await window.damascus.stats(id)
    setOps(st.operation_history || [])
  }

  useEffect(() => {
    ;(async () => {
      await window.damascus.health()

      const created = await window.damascus.createSession({
        width_mm: 50,
        length_mm: 100,
        num_layers: 30,
        white_thickness_mm: 0.8,
        black_thickness_mm: 0.8
      })
      setSessionId(created.session_id)
      await refreshAll(created.session_id)
    })()
  }, [])

  useEffect(() => {
    const t = setInterval(async () => {
      const l = await window.damascus.logsTail(200)
      setLogs(l)
    }, 800)
    return () => clearInterval(t)
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#07070b] via-[#0b0b10] to-black p-5">
      <div className="mx-auto max-w-[1600px] grid grid-cols-[340px_1fr_340px] gap-4">
        <Sidebar
          ready={ready}
          sessionId={sessionId}
          onOp={async (op, payload) => {
            if (!sessionId) return
            await window.damascus.op(sessionId, op, payload)
            await refreshAll(sessionId)
          }}
          onExport={async () => {
            if (!sessionId) return
            await window.damascus.exportModel(sessionId, true)
          }}
        />

        <div className="space-y-4">
          <div className="glass p-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="text-xl font-semibold tracking-tight">Billet Viewport</div>
                <div className="text-xs text-zinc-400">
                  WebGL 3D preview (layer meshes streamed from the Python engine)
                </div>
              </div>
              <div className="text-xs text-zinc-400">
                {mesh ? `${mesh.dims.width_mm.toFixed(1)}×${mesh.dims.length_mm.toFixed(1)}×${mesh.dims.height_mm.toFixed(1)} mm` : '…'}
              </div>
            </div>
            <Viewport3D mesh={mesh} />
          </div>

          <div className="glass p-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="text-xl font-semibold tracking-tight">Cross-Section</div>
                <div className="text-xs text-zinc-400">
                  Slice along billet length (Y) to preview the etched pattern
                </div>
              </div>
            </div>
            <CrossSection
              pngBase64={crossPng}
              onChange={async (ySlice, res) => {
                if (!sessionId) return
                const cs = await window.damascus.crossSection(sessionId, { y_slice: ySlice, resolution: res })
                setCrossPng(cs.png_base64)
              }}
            />
          </div>
        </div>

        <Timeline ops={ops} logs={logs} />
      </div>
    </div>
  )
}
