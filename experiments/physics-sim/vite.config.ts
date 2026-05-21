import { defineConfig } from 'vite'
import path from 'path'

export default defineConfig({
  base: './',
  resolve: {
    alias: { '@shared': path.resolve(__dirname, '../../shared') },
  },
  optimizeDeps: {
    // Rapier handles its own WASM loading; exclude from Vite pre-bundling
    exclude: ['@dimforge/rapier3d-compat'],
  },
})
