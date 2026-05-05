import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// Store DIGITALOCEAN_IP in .env.local (gitignored via *.local) — never commit the real IP.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const doIP = env.DIGITALOCEAN_IP
  // Proxy is only active during `vite dev`, not during `vite build`.
  // Skip the hard-error in production mode so Vercel builds succeed without the var.
  if (!doIP && mode !== 'production') {
    throw new Error('DIGITALOCEAN_IP is not set. Add it to .env.local (never commit this file).')
  }

  return {
    plugins: [react()],
    server: {
      port: 5174,
      strictPort: true,
      proxy: {
        '/api': {
          target: doIP,
          changeOrigin: true,
          secure: false,
          // Rewrite Set-Cookie domain so the browser stores it on localhost.
          // This makes SameSite=Lax cookies work during local dev.
          cookieDomainRewrite: 'localhost',
        },
      },
    },
    build: {
      chunkSizeWarningLimit: 1000,
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (id.includes('node_modules')) {
              return 'vendor';
            }
          },
        },
      },
    },
  }
})
