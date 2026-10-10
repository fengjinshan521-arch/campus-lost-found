// vite.config.js
import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "file:///E:/campus-lost-found/web/node_modules/vite/dist/node/index.js";
import vue from "file:///E:/campus-lost-found/web/node_modules/@vitejs/plugin-vue/dist/index.mjs";
var __vite_injected_original_import_meta_url = "file:///E:/campus-lost-found/web/vite.config.js";
var vite_config_default = defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", __vite_injected_original_import_meta_url))
    }
  },
  server: {
    port: 5173,
    open: false,
    // 开发环境用代理把 /api 与 /uploads 转发到 Flask，实现同源，规避跨域与 Cookie 问题
    proxy: {
      "/api": { target: "http://127.0.0.1:5000", changeOrigin: true },
      "/uploads": { target: "http://127.0.0.1:5000", changeOrigin: true }
    }
  },
  build: {
    outDir: "dist",
    assetsDir: "assets",
    chunkSizeWarningLimit: 1500
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcuanMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJFOlxcXFxjYW1wdXMtbG9zdC1mb3VuZFxcXFx3ZWJcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfZmlsZW5hbWUgPSBcIkU6XFxcXGNhbXB1cy1sb3N0LWZvdW5kXFxcXHdlYlxcXFx2aXRlLmNvbmZpZy5qc1wiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9pbXBvcnRfbWV0YV91cmwgPSBcImZpbGU6Ly8vRTovY2FtcHVzLWxvc3QtZm91bmQvd2ViL3ZpdGUuY29uZmlnLmpzXCI7aW1wb3J0IHsgZmlsZVVSTFRvUGF0aCwgVVJMIH0gZnJvbSAnbm9kZTp1cmwnXG5pbXBvcnQgeyBkZWZpbmVDb25maWcgfSBmcm9tICd2aXRlJ1xuaW1wb3J0IHZ1ZSBmcm9tICdAdml0ZWpzL3BsdWdpbi12dWUnXG5cbmV4cG9ydCBkZWZhdWx0IGRlZmluZUNvbmZpZyh7XG4gIHBsdWdpbnM6IFt2dWUoKV0sXG4gIHJlc29sdmU6IHtcbiAgICBhbGlhczoge1xuICAgICAgJ0AnOiBmaWxlVVJMVG9QYXRoKG5ldyBVUkwoJy4vc3JjJywgaW1wb3J0Lm1ldGEudXJsKSlcbiAgICB9XG4gIH0sXG4gIHNlcnZlcjoge1xuICAgIHBvcnQ6IDUxNzMsXG4gICAgb3BlbjogZmFsc2UsXG4gICAgLy8gXHU1RjAwXHU1M0QxXHU3M0FGXHU1ODgzXHU3NTI4XHU0RUUzXHU3NDA2XHU2MjhBIC9hcGkgXHU0RTBFIC91cGxvYWRzIFx1OEY2Q1x1NTNEMVx1NTIzMCBGbGFza1x1RkYwQ1x1NUI5RVx1NzNCMFx1NTQwQ1x1NkU5MFx1RkYwQ1x1ODlDNFx1OTA3Rlx1OERFOFx1NTdERlx1NEUwRSBDb29raWUgXHU5NUVFXHU5ODk4XG4gICAgcHJveHk6IHtcbiAgICAgICcvYXBpJzogeyB0YXJnZXQ6ICdodHRwOi8vMTI3LjAuMC4xOjUwMDAnLCBjaGFuZ2VPcmlnaW46IHRydWUgfSxcbiAgICAgICcvdXBsb2Fkcyc6IHsgdGFyZ2V0OiAnaHR0cDovLzEyNy4wLjAuMTo1MDAwJywgY2hhbmdlT3JpZ2luOiB0cnVlIH1cbiAgICB9XG4gIH0sXG4gIGJ1aWxkOiB7XG4gICAgb3V0RGlyOiAnZGlzdCcsXG4gICAgYXNzZXRzRGlyOiAnYXNzZXRzJyxcbiAgICBjaHVua1NpemVXYXJuaW5nTGltaXQ6IDE1MDBcbiAgfVxufSlcbiJdLAogICJtYXBwaW5ncyI6ICI7QUFBZ1EsU0FBUyxlQUFlLFdBQVc7QUFDblMsU0FBUyxvQkFBb0I7QUFDN0IsT0FBTyxTQUFTO0FBRjZJLElBQU0sMkNBQTJDO0FBSTlNLElBQU8sc0JBQVEsYUFBYTtBQUFBLEVBQzFCLFNBQVMsQ0FBQyxJQUFJLENBQUM7QUFBQSxFQUNmLFNBQVM7QUFBQSxJQUNQLE9BQU87QUFBQSxNQUNMLEtBQUssY0FBYyxJQUFJLElBQUksU0FBUyx3Q0FBZSxDQUFDO0FBQUEsSUFDdEQ7QUFBQSxFQUNGO0FBQUEsRUFDQSxRQUFRO0FBQUEsSUFDTixNQUFNO0FBQUEsSUFDTixNQUFNO0FBQUE7QUFBQSxJQUVOLE9BQU87QUFBQSxNQUNMLFFBQVEsRUFBRSxRQUFRLHlCQUF5QixjQUFjLEtBQUs7QUFBQSxNQUM5RCxZQUFZLEVBQUUsUUFBUSx5QkFBeUIsY0FBYyxLQUFLO0FBQUEsSUFDcEU7QUFBQSxFQUNGO0FBQUEsRUFDQSxPQUFPO0FBQUEsSUFDTCxRQUFRO0FBQUEsSUFDUixXQUFXO0FBQUEsSUFDWCx1QkFBdUI7QUFBQSxFQUN6QjtBQUNGLENBQUM7IiwKICAibmFtZXMiOiBbXQp9Cg==
