import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  },
  build: {
    // 🚀 Performance optimizations
    target: 'esnext', // Modern browsers only
    minify: 'esbuild', // Fast minification
    sourcemap: false, // Disable sourcemaps for smaller bundles

    rollupOptions: {
      output: {
        // Manual chunks for better caching
        manualChunks: {
          // React core - rarely changes
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          // i18n - separate chunk
          'vendor-i18n': ['i18next', 'react-i18next'],
          // Charts if using recharts
          // 'vendor-charts': ['recharts'],
        }
      }
    },

    // Chunk size warnings
    chunkSizeWarningLimit: 500,
  },

  // Optimize deps
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom']
  }
})