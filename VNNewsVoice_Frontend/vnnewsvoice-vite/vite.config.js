import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// import.meta.env is NOT available in vite.config.js (Node.js context).
// Store DIGITALOCEAN_IP in .env.local (gitignored via *.local) — never commit the real IP.
export default defineConfig(({ mode }) => {
  // Load all env vars for the current mode (including those without VITE_ prefix).
  const env = loadEnv(mode, process.cwd(), '')
  const doIP = env.DIGITALOCEAN_IP
  // Proxy is only active during `vite dev`, not during `vite build`.
  // Skip the hard-error in production mode so Vercel builds succeed without the var.
  if (!doIP && mode !== 'production') {
    throw new Error('DIGITALOCEAN_IP is not set. Add it to .env.local (never commit this file).')
  }

  // Optional: set LOCAL_RAG_URL=http://localhost:8000 in .env.local to proxy /chat/* directly
  // to a locally-running RAG service (with automatic /chat → /api/v1/chat path rewrite).
  // When not set, /chat/* is forwarded to DIGITALOCEAN_IP (DO gateway handles the rewrite).
  const ragTarget = env.LOCAL_RAG_URL || doIP

  return {
    plugins: [react()],
    server: {
      port: 5173,
      strictPort: true,
      proxy: {
        '/api': {
          target: doIP,
          changeOrigin: true,
          secure: false,
          cookieDomainRewrite: 'localhost',
        },
        '/chat': {
          target: ragTarget,
          changeOrigin: true,
          secure: false,
          cookieDomainRewrite: 'localhost',
          // When targeting the local RAG service directly, rewrite /chat/* → /api/v1/chat/*
          // because the local service exposes /api/v1/chat/* (no gateway in the path).
          ...(env.LOCAL_RAG_URL
            ? { rewrite: (path) => path.replace(/^\/chat/, '/api/v1/chat') }
            : {}),
          bypass(req) {
            // Don't proxy the SPA page route — only proxy API sub-paths like /chat/stream, /chat/conversations
            if (req.url === '/chat' || req.url === '/chat?') return req.url;
            return null; // null means "do proxy"
          },
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
