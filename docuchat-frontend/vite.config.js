// vite.config.js — Docker version
// Uses environment variable for API URL
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: '0.0.0.0',   // Required for Docker
    proxy: {
      '/upload': 'http://backend:8000',
      '/chat':   'http://backend:8000',
      '/auth':   'http://backend:8000',
    }
  }
})
