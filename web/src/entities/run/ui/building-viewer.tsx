import { useEffect, useRef } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { MeshPayload } from '@/entities/run/model/types'

type BuildingViewerProps = {
  mesh?: MeshPayload
}

export function BuildingViewer({ mesh }: BuildingViewerProps): JSX.Element {
  const rootRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!rootRef.current) {
      return
    }

    const width = rootRef.current.clientWidth
    const height = rootRef.current.clientHeight

    const scene = new THREE.Scene()
    scene.background = new THREE.Color('#f1f5f9')

    const camera = new THREE.PerspectiveCamera(44, width / height, 0.1, 1000)
    camera.position.set(36, 34, 52)

    const renderer = new THREE.WebGLRenderer({ antialias: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.setSize(width, height)
    rootRef.current.appendChild(renderer.domElement)
    const controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.dampingFactor = 0.08
    controls.target.set(0, 12, 0)
    controls.minDistance = 18
    controls.maxDistance = 180
    controls.maxPolarAngle = Math.PI / 2.05

    const keyLight = new THREE.DirectionalLight(0xffffff, 1.2)
    keyLight.position.set(25, 48, 22)
    scene.add(keyLight)
    scene.add(new THREE.AmbientLight(0xffffff, 0.6))

    const ground = new THREE.Mesh(
      new THREE.PlaneGeometry(180, 180),
      new THREE.MeshStandardMaterial({ color: '#dbe2ea' })
    )
    ground.rotation.x = -Math.PI / 2
    scene.add(ground)

    if (mesh) {
      const material = new THREE.MeshStandardMaterial({ color: '#0ea5e9' })
      if (mesh.type === 'box') {
        const mass = new THREE.Mesh(
          new THREE.BoxGeometry(mesh.width, mesh.height, mesh.depth),
          material
        )
        mass.position.y = mesh.height / 2
        scene.add(mass)
      } else if (mesh.type === 'multi_block') {
        if (mesh.site_outline && mesh.site_outline.length > 2) {
          const shape = new THREE.Shape()
          mesh.site_outline.forEach(([x, z], idx) => {
            if (idx === 0) {
              shape.moveTo(x, z)
            } else {
              shape.lineTo(x, z)
            }
          })
          const siteGeom = new THREE.ShapeGeometry(shape)
          siteGeom.rotateX(-Math.PI / 2)
          const siteMesh = new THREE.Mesh(
            siteGeom,
            new THREE.MeshStandardMaterial({ color: '#cfd8df', transparent: true, opacity: 0.9 })
          )
          scene.add(siteMesh)

          const linePoints = mesh.site_outline.map(([x, z]) => new THREE.Vector3(x, 0.05, z))
          const lineGeom = new THREE.BufferGeometry().setFromPoints(linePoints)
          const line = new THREE.LineLoop(
            lineGeom,
            new THREE.LineBasicMaterial({ color: '#0f172a' })
          )
          scene.add(line)
        }

        for (const block of mesh.blocks) {
          const mass = new THREE.Mesh(
            new THREE.BoxGeometry(block.width, block.height, block.depth),
            material
          )
          mass.position.x = block.x
          mass.position.z = block.z
          mass.position.y = block.height / 2
          scene.add(mass)
        }
      } else if (mesh.type === 'stacked') {
        for (const segment of mesh.segments) {
          const mass = new THREE.Mesh(
            new THREE.BoxGeometry(segment.width, segment.height, segment.depth),
            material
          )
          mass.position.y = segment.base_y + (segment.height / 2)
          scene.add(mass)
        }
      } else {
        const outer = new THREE.Shape()
        outer.moveTo(-mesh.outer_width / 2, -mesh.outer_depth / 2)
        outer.lineTo(mesh.outer_width / 2, -mesh.outer_depth / 2)
        outer.lineTo(mesh.outer_width / 2, mesh.outer_depth / 2)
        outer.lineTo(-mesh.outer_width / 2, mesh.outer_depth / 2)
        outer.lineTo(-mesh.outer_width / 2, -mesh.outer_depth / 2)

        const inner = new THREE.Path()
        inner.moveTo(-mesh.inner_width / 2, -mesh.inner_depth / 2)
        inner.lineTo(-mesh.inner_width / 2, mesh.inner_depth / 2)
        inner.lineTo(mesh.inner_width / 2, mesh.inner_depth / 2)
        inner.lineTo(mesh.inner_width / 2, -mesh.inner_depth / 2)
        inner.lineTo(-mesh.inner_width / 2, -mesh.inner_depth / 2)
        outer.holes.push(inner)

        const geometry = new THREE.ExtrudeGeometry(outer, { depth: mesh.height, bevelEnabled: false })
        geometry.rotateX(-Math.PI / 2)
        geometry.translate(0, mesh.height, 0)
        const mass = new THREE.Mesh(geometry, material)
        scene.add(mass)
      }
    }

    camera.lookAt(0, 10, 0)
    let frameId = 0

    const animate = (): void => {
      controls.update()
      renderer.render(scene, camera)
      frameId = requestAnimationFrame(animate)
    }

    animate()

    const onResize = (): void => {
      if (!rootRef.current) {
        return
      }
      const nextWidth = rootRef.current.clientWidth
      const nextHeight = rootRef.current.clientHeight
      renderer.setSize(nextWidth, nextHeight)
      camera.aspect = nextWidth / nextHeight
      camera.updateProjectionMatrix()
    }

    window.addEventListener('resize', onResize)

    return () => {
      cancelAnimationFrame(frameId)
      window.removeEventListener('resize', onResize)
      controls.dispose()
      renderer.dispose()
      if (rootRef.current?.contains(renderer.domElement)) {
        rootRef.current.removeChild(renderer.domElement)
      }
    }
  }, [mesh])

  return <div ref={rootRef} className="h-[460px] w-full rounded-2xl border border-slate-200 bg-slate-100" />
}
