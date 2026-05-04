import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import AutoImport from "unplugin-auto-import/vite";
import Components from "unplugin-vue-components/vite";
import { ElementPlusResolver } from "unplugin-vue-components/resolvers";

// 生产版本配置（用于 demo 演示）
export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
    }),
    Components({
      resolvers: [ElementPlusResolver({ importStyle: false })],
    }),
  ],
  server: {
    proxy: {
      "/api": "http://localhost:5001",
    },
  },
  build: {
    modulePreload: false,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("node_modules/element-plus")) return "element-plus";
          if (id.includes("node_modules/echarts")) return "echarts";
          if (
            id.includes("node_modules/vue/") ||
            id.includes("node_modules/vue-router/") ||
            id.includes("node_modules/@vue/")
          )
            return "vue-vendor";
        },
      },
    },
  },
});
