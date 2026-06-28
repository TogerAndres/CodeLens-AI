import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5500,
    proxy: {
      // Evita problemas de CORS en desarrollo igual que en Control RASS
      "/api": {
        target: "http://localhost:5001",
        changeOrigin: true,
      },
    },
  },
});
