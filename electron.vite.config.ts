import { defineConfig } from 'electron-vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'

export default defineConfig({
  main: {
    build: { sourcemap: true }
  },
  preload: {
    build: { sourcemap: true }
  },
  renderer: {
    plugins: [react()],
    resolve: {
      alias: {
        '@renderer': path.resolve(__dirname, 'src/renderer/src')
      }
    },
    server: {
      watch: {
        ignored: [
          '**/venv/**',
          '**/.venv/**',
          '**/logs/**',
          '**/python/**',
          '**/lib/**',
          '**/tests/**',
          '**/__pycache__/**'
        ]
      }
    }
  }
})
