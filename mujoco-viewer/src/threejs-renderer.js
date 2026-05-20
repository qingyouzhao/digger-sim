import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'

export function createRenderer() {
  const canvas = document.getElementById('canvas')
  const renderer = new THREE.WebGLRenderer({ antialias: true, canvas })
  renderer.setPixelRatio(devicePixelRatio)
  renderer.setSize(innerWidth, innerHeight)
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap

  const scene = new THREE.Scene()
  scene.background = new THREE.Color(0x87ceeb)
  scene.fog = new THREE.FogExp2(0x87ceeb, 0.015)

  // Z-up to match MuJoCo's coordinate convention
  const camera = new THREE.PerspectiveCamera(50, innerWidth / innerHeight, 0.01, 200)
  camera.up.set(0, 0, 1)
  camera.position.set(5, -4, 3.5)

  const controls = new OrbitControls(camera, renderer.domElement)
  controls.target.set(0.5, 0, 1.0)
  controls.enableDamping = true
  controls.dampingFactor = 0.08

  scene.add(new THREE.AmbientLight(0xffffff, 0.55))

  const sun = new THREE.DirectionalLight(0xffffff, 1.1)
  sun.position.set(6, 6, 12)
  sun.castShadow = true
  sun.shadow.mapSize.set(2048, 2048)
  const sc = sun.shadow.camera
  sc.near = 0.5; sc.far = 60
  sc.top = sc.right = 12; sc.bottom = sc.left = -12
  scene.add(sun)

  const fill = new THREE.DirectionalLight(0x8080ff, 0.25)
  fill.position.set(-5, -5, 5)
  scene.add(fill)

  window.addEventListener('resize', () => {
    camera.aspect = innerWidth / innerHeight
    camera.updateProjectionMatrix()
    renderer.setSize(innerWidth, innerHeight)
  })

  return { renderer, scene, camera, controls }
}
