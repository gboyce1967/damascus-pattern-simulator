import { useEffect, useRef } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

type MeshPayload = {
  dims: { width_mm: number; length_mm: number; height_mm: number }
  layers: Array<{ color: [number, number, number]; vertices: number[]; triangles: number[] }>
} | null

export default function Viewport3D({ mesh }: { mesh: MeshPayload }) {
  const hostRef = useRef<HTMLDivElement | null>(null)
  const sceneRef = useRef<THREE.Scene | null>(null)
  const groupRef = useRef<THREE.Group | null>(null)
  const gridRef = useRef<THREE.GridHelper | null>(null)
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null)
  const controlsRef = useRef<OrbitControls | null>(null)

  useEffect(() => {
    if (!hostRef.current) return

    const host = hostRef.current
    const scene = new THREE.Scene()
    scene.fog = new THREE.Fog(0x05050a, 200, 2000)

    const camera = new THREE.PerspectiveCamera(45, host.clientWidth / host.clientHeight, 0.1, 8000)
    camera.position.set(140, 110, 180)

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setSize(host.clientWidth, host.clientHeight)
    renderer.setPixelRatio(window.devicePixelRatio)
    host.appendChild(renderer.domElement)

    const controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true

    cameraRef.current = camera
    controlsRef.current = controls

    // Lights
    scene.add(new THREE.AmbientLight(0xffffff, 0.55))
    const key = new THREE.DirectionalLight(0xffffff, 0.8)
    key.position.set(200, 260, 140)
    scene.add(key)

    // Build plate (grid) — starts at a default size, will resize to fit billet
    const grid = new THREE.GridHelper(280, 28, 0x222233, 0x11111a)
    scene.add(grid)
    gridRef.current = grid

    scene.add(new THREE.AxesHelper(80))

    const group = new THREE.Group()
    scene.add(group)

    sceneRef.current = scene
    groupRef.current = group

    function onResize() {
      if (!hostRef.current) return
      const w = hostRef.current.clientWidth
      const h = hostRef.current.clientHeight
      if (w === 0 || h === 0) return
      camera.aspect = w / h
      camera.updateProjectionMatrix()
      renderer.setSize(w, h)
    }

    const ro = new ResizeObserver(onResize)
    ro.observe(host)
    window.addEventListener('resize', onResize)

    let raf = 0
    const tick = () => {
      controls.update()
      renderer.render(scene, camera)
      raf = requestAnimationFrame(tick)
    }
    tick()

    return () => {
      cancelAnimationFrame(raf)
      ro.disconnect()
      window.removeEventListener('resize', onResize)
      controls.dispose()
      renderer.dispose()
      host.removeChild(renderer.domElement)
    }
  }, [])

  useEffect(() => {
    const group = groupRef.current
    const scene = sceneRef.current
    if (!group || !scene) return

    // Clear old meshes
    while (group.children.length) group.remove(group.children[0])
    group.rotation.set(0, 0, 0)
    group.position.set(0, 0, 0)

    if (!mesh) return

    for (const layer of mesh.layers) {
      // Remap axes at the vertex level so billet lies flat:
      //   engine X (width)  → scene X
      //   engine Y (length) → scene Z
      //   engine Z (height) → scene Y (up)
      // Billet origin stays at (0,0,0) — bottom corner on the build plate.
      const src = layer.vertices
      const dst = new Float32Array(src.length)
      for (let i = 0; i < src.length; i += 3) {
        dst[i]     = src[i]      // X = width
        dst[i + 1] = src[i + 2]  // Y(up) = height
        dst[i + 2] = src[i + 1]  // Z = length
      }

      const geom = new THREE.BufferGeometry()
      geom.setAttribute('position', new THREE.BufferAttribute(dst, 3))
      geom.setIndex(layer.triangles)
      geom.computeVertexNormals()

      const mat = new THREE.MeshStandardMaterial({
        color: new THREE.Color(layer.color[0], layer.color[1], layer.color[2]),
        metalness: 0.25,
        roughness: 0.65
      })

      group.add(new THREE.Mesh(geom, mat))
    }

    // Resize build plate grid if billet exceeds it
    const maxSpan = Math.max(mesh.dims.width_mm, mesh.dims.length_mm)
    const gridSize = Math.max(280, Math.ceil(maxSpan * 1.5 / 10) * 10)
    if (gridRef.current) {
      scene.remove(gridRef.current)
      gridRef.current.dispose()
    }
    const grid = new THREE.GridHelper(gridSize, Math.round(gridSize / 10), 0x222233, 0x11111a)
    scene.add(grid)
    gridRef.current = grid

    // Auto-frame: centre orbit target on the billet and pull camera back
    // so the whole bar is visible, no matter how long it got.
    const camera = cameraRef.current
    const controls = controlsRef.current
    if (camera && controls) {
      const { width_mm: w, length_mm: l, height_mm: h } = mesh.dims
      // Scene coords: X=width, Y(up)=height, Z=length
      const cx = w / 2
      const cy = h / 2
      const cz = l / 2
      controls.target.set(cx, cy, cz)

      // Pull back far enough to fit the longest dimension
      const maxDim = Math.max(w, l, h)
      const dist = maxDim * 1.4
      camera.position.set(cx + dist * 0.55, cy + dist * 0.45, cz + dist * 0.7)
      camera.far = Math.max(8000, maxDim * 6)
      camera.updateProjectionMatrix()

      // Update fog to match
      if (scene.fog instanceof THREE.Fog) {
        scene.fog.near = dist * 0.3
        scene.fog.far = dist * 5
      }

      controls.update()
    }
  }, [mesh])

  return <div ref={hostRef} className="w-full flex-1 min-h-[200px] rounded-xl overflow-hidden bg-gradient-to-b from-black/40 to-black/10" />
}
