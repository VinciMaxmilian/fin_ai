import { fileURLToPath, URL } from 'node:url'
import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

export default defineConfig(({ mode }) => {
  // As variaveis vivem no .env da raiz do repositorio, compartilhado com o backend.
  const env = loadEnv(mode, '..', 'VITE_')

  return {
    plugins: [react()],
    envDir: '..',
    resolve: {
      alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
    },
    server: {
      port: 5173,
      host: true,
    },
    define: {
      __API_URL__: JSON.stringify(env.VITE_API_URL ?? 'http://localhost:8000/api/v1'),
    },
    build: {
      target: 'es2022',
      sourcemap: mode !== 'production',
      rollupOptions: {
        output: {
          // Separa o que raramente muda: o navegador reaproveita esses arquivos
          // entre deploys em vez de baixar tudo de novo a cada alteração.
          manualChunks: {
            react: ['react', 'react-dom', 'react-router-dom'],
            supabase: ['@supabase/supabase-js'],
          },
        },
      },
    },
  }
})
