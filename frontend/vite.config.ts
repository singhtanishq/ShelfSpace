import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

// Backend origin can be overridden for local dev when :8000 is occupied,
// e.g. `BACKEND_URL=http://127.0.0.1:8001 npm run dev -- --port 5174`.
const backendUrl = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": { target: backendUrl, changeOrigin: true },
      "/media": { target: backendUrl, changeOrigin: true },
    },
  },
});
