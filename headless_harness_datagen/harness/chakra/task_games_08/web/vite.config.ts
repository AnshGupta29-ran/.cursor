import { defineConfig } from 'vite';

export default defineConfig({
  root: '.',
  server: {
    port: 5188,
    strictPort: false,
    host: "127.0.0.1",
  },
});
