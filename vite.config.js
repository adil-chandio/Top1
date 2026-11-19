import { fileURLToPath } from 'node:url';
import { defineConfig } from 'vite';

function redirectStudioDirectory(server) {
  server.middlewares.use((request, response, next) => {
    const match = request.url?.match(/^(\/monarch-studio(?:\/reflector)?)(\?.*)?$/);
    if (!match) return next();
    response.writeHead(308, { Location: `${match[1]}/${match[2] ?? ''}` });
    response.end();
  });
}

export default defineConfig({
  appType: 'mpa',
  plugins: [{
    name: 'monarch-directory-url',
    configureServer: redirectStudioDirectory,
    configurePreviewServer: redirectStudioDirectory,
  }],
  server: { host: '0.0.0.0', allowedHosts: ['.e2b.app'] },
  preview: { host: '0.0.0.0', allowedHosts: ['.e2b.app'] },
  build: {
    rollupOptions: {
      input: {
        home: fileURLToPath(new URL('./index.html', import.meta.url)),
        kit: fileURLToPath(new URL('./kit.html', import.meta.url)),
        monarch: fileURLToPath(new URL('./monarch-studio/index.html', import.meta.url)),
        reflector: fileURLToPath(new URL('./monarch-studio/reflector/index.html', import.meta.url)),
      },
    },
  },
});
