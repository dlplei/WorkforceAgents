import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // 预打包所有依赖：避免首次访问时 Vite 边扫描边按需 optimize，
  // 导致浏览器长时间停留在 "Waiting for http://127.0.0.1:3000 ..." 
  optimizeDeps: {
    include: [
      "react",
      "react-dom",
      "react-dom/client",
      "react/jsx-runtime",
      "react/jsx-dev-runtime",
      "lucide-react",
    ],
  },
  server: {
    // 监听所有网卡（IPv4 + IPv6），这样 localhost / 127.0.0.1 / 局域网 IP 都能访问
    host: true,
    port: 3000,
    strictPort: true,
    watch: {
      ignored: ["**/backend/**", "**/venv/**"],
    },
    hmr: {
      protocol: "ws",
      clientPort: 3000,
    },
    proxy: {
      // 前端用相对路径 /api/* 请求后端：同源、无 CORS、也不会被浏览器代理拦截
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        ws: false,
      },
    },
  },
});
