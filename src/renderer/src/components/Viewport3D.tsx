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

  useEffect(() => {
    if (!hostRef.current) return

    const host = hostRef.current
    const scene = new THREE.Scene()
    scene.fog = new THREE.Fog(0x05050a, 120, 420)

    const camera = new THREE.PerspectiveCamera(45, host.clientWidth / host.clientHeight, 0.1, 2000)
    camera.position.set(140, 110, 180)

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setSize(host.clientWidth, host.clientHeight)
    renderer.setPixelRatio(window.devicePixelRatio)
    host.appendChild(renderer.domElement)

    const controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true

    // Lights
    scene.add(new THREE.AmbientLight(0xffffff, 0.55))
    const key = new THREE.DirectionalLight(0xffffff, 0.8)
    key.position.set(200, 260, 140)
    scene.add(key)

    // Helpers
    const grid = new THREE.GridHelper(280, 28, 0x222233, 0x11111a)
    grid.position.y = -1
    scene.add(grid)
    scene.add(new THREE.AxesHelper(80))

    const group = new THREE.Group()
    scene.add(group)

    sceneRef.current = scene
    groupRef.current = group

    function onResize() {
      if (!hostRef.current) return
      camera.aspect = hostRef.current.clientWidth / hostRef.current.clientHeight
      camera.updateProjectionMatrix()
      renderer.setSize(hostRef.current.clientWidth, hostRef.current.clientHeight)
    }

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
      window.removeEventListener('resize', onResize)
      controls.dispose()
      renderer.dispose()
      host.removeChild(renderer.domElement)
    }
  }, [])

  useEffect(() => {
    const group = groupRef.current
    if (!group) return

    // Clear old
    while (group.children.length) group.remove(group.children[0])

    if (!mesh) return

    for (const layer of mesh.layers) {
      const geom = new THREE.BufferGeometry()
      geom.setAttribute('position', new THREE.Float32BufferAttribute(layer.vertices, 3))
      geom.setIndex(layer.triangles)

      geom.computeVertexNormals()

      const mat = new THREE.MeshStandardMaterial({
        color: new THREE.Color(layer.color[0], layer.color[1], layer.color[2]),
        metalness: 0.25,
        roughness: 0.65
      })

      const m = new THREE.Mesh(geom, mat)
      group.add(m)
    }

    // Center camera target feel by shifting group slightly upward
    group.position.set(0, 0, 0)
  }, [mesh])

  return <div ref={hostRef} className="w-full h-[420px] rounded-xl overflow-hidden bg-gradient-to-b from-black/40 to-black/10" />
}
