// Local-only override: same as vite.config.ts but proxies to the backend on
// :8001, because :8000 is occupied by an unrelated copy of this project.
// Not committed — delete once :8000 is free. Run with:
//   npx vite --config vite.config.local.ts
import base from "./vite.config";
import { defineConfig, mergeConfig } from "vite";

export default mergeConfig(
  base,
  defineConfig({
    server: {
      proxy: {
        "/api": { target: "http://127.0.0.1:8001", changeOrigin: true },
        "/health": { target: "http://127.0.0.1:8001", changeOrigin: true },
      },
    },
  }),
);
