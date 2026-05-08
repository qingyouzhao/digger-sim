import { defineConfig } from 'vite'

export default defineConfig({
  base: './',
  optimizeDeps: {
    // Rapier handles its own WASM loading; exclude from Vite pre-bundling
    exclude: ['@dimforge/rapier3d-compat'],
  },
})
