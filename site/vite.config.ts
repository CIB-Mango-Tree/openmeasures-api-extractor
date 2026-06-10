import { defineConfig } from 'vite'
import { tanstackStart } from '@tanstack/react-start/plugin/vite'
import viteReact from '@vitejs/plugin-react'
import viteTsConfigPaths from 'vite-tsconfig-paths'
import tailwindcss from '@tailwindcss/vite'
import { nitroV2Plugin } from '@tanstack/nitro-v2-vite-plugin'

const config = defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: false,
        ws: true,
      },
    },
  },
  plugins: [
    nitroV2Plugin({
      experimental: { websocket: true },
      routeRules: {
        '/api/**': { proxy: { to: 'http://127.0.0.1:8000/api/**' } },
      },
      handlers: [
        {
          route: '/api/ws/updates',
          handler: './src/routes/api/ws/updates.ts',
          lazy: true,
        },
      ],
    }),
    viteTsConfigPaths({
      projects: ['./tsconfig.json'],
    }),
    tailwindcss(),
    tanstackStart({
      router: {
        routeFileIgnorePattern: '^api/',
      },
    }),
    viteReact(),
  ],
});

export default config
