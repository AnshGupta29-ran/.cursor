import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Dev: Socket.IO traffic (including websocket upgrades) forwards to the
      // Node server, so the client code uses a relative path in all environments.
      '/socket.io': { target: 'http://localhost:3001', ws: true }
    }
  }
});
