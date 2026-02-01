import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [react()],
    server: {
      allowedHosts: true,
      port: 3000,
      host: true,
      proxy: {
        '/api': {
          target: env.API_PROXY_TARGET || 'http://api:8000',
          changeOrigin: true,
        }
      }
    }
  }
})
