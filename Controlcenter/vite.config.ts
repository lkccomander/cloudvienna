import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 4173,
  },
  preview: {
    host: true,
    port: 4173,
    allowedHosts: [".up.railway.app", "localhost", "127.0.0.1"],
  },
});
