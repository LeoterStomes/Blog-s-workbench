import { defineConfig } from 'astro/config';
import vue from '@astrojs/vue';
import tailwind from '@astrojs/tailwind';
import node from '@astrojs/node';

// 构建与开发服务器缓存分开，避免生产构建让运行中的 Vite 开发缓存失效。
const isProductionBuild = process.env.npm_lifecycle_event === 'build';
const backendPort = process.env.WORKBENCH_BACKEND_PORT || '1235';
const frontendPort = Number(process.env.WORKBENCH_FRONTEND_PORT || '4321');

export default defineConfig({
  integrations: [
    vue(),
    tailwind({ applyBaseStyles: false }),
  ],
  prefetch: true,
  devToolbar: { enabled: false },
  adapter: node({ mode: 'standalone' }),
  server: {
    port: frontendPort,
  },
  vite: {
    cacheDir: isProductionBuild ? 'node_modules/.vite-build' : 'node_modules/.vite',
    server: {
      proxy: {
        '/api': {
          target: `http://localhost:${backendPort}`,
          changeOrigin: true,
          proxyTimeout: 600000,    // 10 分钟，长工具不会断
          timeout: 600000,
        },
        '/uploads': {
          target: `http://localhost:${backendPort}`,
          changeOrigin: true,
        },
      },
    },
    resolve: {
      alias: {
        '@': '/src',
        '@components': '/src/components',
        '@layouts': '/src/layouts',
        '@lib': '/src/lib',
        '@styles': '/src/styles',
      },
    },
  },
});
