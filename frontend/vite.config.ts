import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  build: { chunkSizeWarningLimit: 900 }, // react + echarts core, single internal app
  server: { proxy: { "/api": "http://localhost:8000" } },
});
