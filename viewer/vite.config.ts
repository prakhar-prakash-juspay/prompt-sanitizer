import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/viewer/',
  build: {
    outDir: '../src/aegis/viewer/static',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/api': 'http://localhost:9443',
    },
  },
})
