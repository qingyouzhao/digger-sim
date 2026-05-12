import { defineConfig } from 'vite'

export default defineConfig({
  // './' makes all asset paths relative — dist/ can be placed in any subdirectory
  base: './',

  server: {
    // needed locally because SharedArrayBuffer requires cross-origin isolation;
    // on GitHub Pages the coi-serviceworker.js polyfill handles this instead
    headers: {
      'Cross-Origin-Opener-Policy': 'same-origin',
      'Cross-Origin-Embedder-Policy': 'require-corp',
    },
  },

  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    target: 'esnext',  // required for top-level await
  },
})
