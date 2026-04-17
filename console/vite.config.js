import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig({
    plugins: [react()],
    // 构建产物输出到 `console/assets/`（含 index.html 与内层 `assets/` 资源目录），供 FastAPI 挂载
    build: {
        outDir: "assets",
        emptyOutDir: true,
    },
    server: {
        host: "0.0.0.0",
        port: 5174,
        // 开发时把 /api 转到本机 HiData 服务，便于与 `python -m hidata app` 联调
        proxy: {
            "/api": {
                target: process.env.VITE_DEV_API ?? "http://127.0.0.1:8088",
                changeOrigin: true,
            },
        },
    },
});
