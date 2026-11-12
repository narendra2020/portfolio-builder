import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// See frontend/vite.config.js in the sibling app for why this proxy
// exists and how VITE_API_PROXY_TARGET is used across native vs Docker.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    host: true,
    proxy: {
      "/api": {
        target: process.env.VITE_API_PROXY_TARGET || "http://localhost:8001",
        changeOrigin: true,
      },
    },
  },
});
