import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { sentryVitePlugin } from '@sentry/vite-plugin';

// https://vitejs.dev/config/
export default defineConfig({
  build: {
    sourcemap: true,
  },
  plugins: [
    react(),
    sentryVitePlugin({
      org: 'grevity',
      project: 'lyrics-destinpq',
      authToken: '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',
      sourcemaps: { filesToDeleteAfterUpload: ['**/*.map'] },
    }),
  ]
})
