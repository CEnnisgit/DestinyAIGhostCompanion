import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // Relative asset paths so the build also loads under file:// inside Electron.
  base: "./",
  server: { port: 5173 },
});
